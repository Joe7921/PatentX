# llm_factory.py
# LLM 工厂装载器 (内置主备模型 Try-Catch 自动 Fallback 容灾降级机制)

import asyncio
import os
import httpx
import time
from typing import Dict, Any, Optional, List

# 动态加载 .env 配置文件，避免硬编码敏感 KEY
def load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    print(f"[DEBUG load_dotenv] env_path: {env_path}, exists: {os.path.exists(env_path)}")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
                    print(f"[DEBUG load_dotenv] set env {k.strip()} = {v.strip()[:10]}...")

load_dotenv()

class LLMFactory:
    _failure_counts: Dict[str, int] = {}
    _circuit_breaker_until: Dict[str, float] = {}

    @staticmethod
    def get_client(agent_name: str, llm_config: Dict[str, Any], blackboard: Optional[Any] = None) -> "MockLLMClient":
        """
        根据 Agent YAML 中的 llm 配置组装并初始化对应的大模型 Client 实例。
        """
        return MockLLMClient(agent_name, llm_config, blackboard)

class MockLLMClient:
    def __init__(self, agent_name: str, config: Dict[str, Any], blackboard: Optional[Any] = None):
        self.agent_name = agent_name
        self.config = config
        self.blackboard = blackboard
        
        # 默认解析主模型与备用模型
        self.primary_model = config.get("model", "gemini-1.5-pro")
        self.fallback_model = config.get("fallback_model")  # 若无则为 None
        self.temperature = config.get("temperature", 0.2)

    async def generate(self, prompt: str, system_instruction: str = "", tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        主备 LLM 自动 Fallback 容灾路由接口，返回包含了 content 和 tool_calls 的字典。
        """
        try:
            return await self._call_model(self.primary_model, prompt, system_instruction, tools)
        except Exception as e:
            # 判断是否存在备用模型，若有则进行降级处理
            if self.fallback_model:
                warning_msg = f"[LLM 降级预警] Agent '{self.agent_name}' 的首选模型 '{self.primary_model}' 请求异常: {str(e)}。系统已自动且无感降级至备选模型 '{self.fallback_model}'。"
                
                # 同步记录到黑板 debate_logs
                if self.blackboard:
                    await self.blackboard.add_debate_log(warning_msg)
                    
                # 重新尝试调用备用模型
                try:
                    return await self._call_model(self.fallback_model, prompt, system_instruction, tools)
                except Exception as fe:
                    pass
            
            # 高质量本地模板降级兜底逻辑
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            import os
            mock_module = os.getenv("MOCK_INJECTION_MODULE")
            if mock_module:
                print("[MOCK_TRANSPORT] Using mock LLM fallback")
                import importlib
                mock = importlib.import_module(mock_module)
                return await mock.mock_llm_generate(messages, tools, self.blackboard)
            else:
                raise RuntimeError(f"All LLM models failed and no mock module injected. Last error: {e}")

    async def _call_model(self, model_name: str, prompt: str, system_instruction: str, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        # 运行时动态热加载 .env 文件，保障宿主进程即使不重启也能即时应用最新的凭证改动
        load_dotenv()
        
        # 混沌工程故障注入（仅在测试环境中通过设置 INJECT_LLM_FAILURE=true 激活）
        inject_failure = os.getenv("INJECT_LLM_FAILURE", "").lower() in ("true", "1")
        if inject_failure and self.agent_name in ("epo_examiner", "first_examiner", "second_examiner") and model_name.lower() in ("deepseek-v4-flash", "v4-flash"):
            raise ValueError("Simulated 429 Rate Limit Exceeded")

        print(f"[DEBUG _call_model] agent: {self.agent_name}, model: {model_name}, env keys: {[k for k in os.environ.keys() if 'DEEPSEEK' in k]}")
        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
        print(f"[DEBUG _call_model] api_key value: '{api_key}', len: {len(api_key) if api_key else 0}, type: {type(api_key)}")
        


        # 完全在生产环境中运行：若未设置 API KEY，直接抛出异常，不再静默退回到 Mock 状态
        if not api_key:
            raise ValueError(
                f"Production Configuration Error: DEEPSEEK_API_KEY is not configured in the environment. "
                f"Unable to execute LLM request for agent '{self.agent_name}'. Current Env DEEPSEEK Keys: {[k for k in os.environ.keys() if 'DEEPSEEK' in k]}"
            )

        # 映射与兼容模型名大小写
        mapped_model = model_name
        if model_name == "deepseek-V4-Pro":
            mapped_model = "deepseek-v4-pro"
        elif model_name == "V4-Flash":
            mapped_model = "deepseek-v4-flash"
        else:
            mapped_model = model_name.lower()

        now = time.time()
        cb_until = LLMFactory._circuit_breaker_until.get(mapped_model, 0)
        if now < cb_until:
            msg = f"[CIRCUIT_BREAKER] 模型 {mapped_model} 处于熔断期，{int(cb_until - now)}秒后恢复，直接走本地Fallback！"
            print(msg)
            if self.blackboard:
                await self.blackboard.add_debate_log(msg)
            raise ValueError(f"Circuit breaker active for {mapped_model}")
        if cb_until and now >= cb_until:
            msg = f"[CIRCUIT_BREAKER] 模型 {mapped_model} 熔断恢复"
            print(msg)
            if self.blackboard:
                await self.blackboard.add_debate_log(msg)
            LLMFactory._circuit_breaker_until[mapped_model] = 0
            LLMFactory._failure_counts[mapped_model] = 0

        # 组建 API 端点
        base_url = api_base.rstrip("/")
        if base_url.endswith("/v1"):
            url = f"{base_url}/chat/completions"
        else:
            url = f"{base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 组装消息列表
        messages = []
        sys_instr = system_instruction
        if not sys_instr and self.config.get("prompts", {}).get("system"):
            sys_instr = self.config["prompts"]["system"]
            
        if sys_instr:
            messages.append({"role": "system", "content": sys_instr})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": mapped_model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 1024
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    LLMFactory._failure_counts[mapped_model] = 0
                    data = response.json()
                    message = data["choices"][0]["message"]
                    # 确保返回格式统一为 dict，包含 content 和 tool_calls 和 reasoning_content
                    return {
                        "content": message.get("content"),
                        "tool_calls": message.get("tool_calls"),
                        "reasoning_content": message.get("reasoning_content")
                    }
                else:
                    raise ValueError(f"LLM API Error: Status {response.status_code}, Body: {response.text}")
        except Exception as e:
            failures = LLMFactory._failure_counts.get(mapped_model, 0) + 1
            LLMFactory._failure_counts[mapped_model] = failures
            if failures >= 3:
                LLMFactory._circuit_breaker_until[mapped_model] = time.time() + 30
                msg = f"[CIRCUIT_BREAKER] 模型 {mapped_model} 连续失败超过3次，触发熔断，30秒内直接走本地Fallback！"
                print(msg)
                if self.blackboard:
                    await self.blackboard.add_debate_log(msg)

            # 向上抛出异常以支持主备 Fallback 容灾降级
            raise ValueError(f"Failed to connect to LLM API ({mapped_model}): {str(e)}")

    async def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        基于完整消息列表的对话接口（支持 ReAct 循环中的多轮工具调用状态跟踪）
        """
        try:
            return await self._call_model_chat(self.primary_model, messages, tools)
        except Exception as e:
            if self.fallback_model:
                warning_msg = f"[LLM 降级预警] Agent '{self.agent_name}' 的首选模型 '{self.primary_model}' 请求异常: {str(e)}。系统已自动且无感降级至备选模型 '{self.fallback_model}'。"
                if self.blackboard:
                    await self.blackboard.add_debate_log(warning_msg)
                try:
                    return await self._call_model_chat(self.fallback_model, messages, tools)
                except Exception as fe:
                    pass
            
            import os
            mock_module = os.getenv("MOCK_INJECTION_MODULE")
            if mock_module:
                print("[MOCK_TRANSPORT] Using mock LLM fallback")
                import importlib
                mock = importlib.import_module(mock_module)
                return await mock.mock_llm_generate(messages, tools, self.blackboard)
            else:
                raise RuntimeError(f"All LLM models failed in chat and no mock module injected. Last error: {e}")

    async def _call_model_chat(self, model_name: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        load_dotenv()
        inject_failure = os.getenv("INJECT_LLM_FAILURE", "").lower() in ("true", "1")
        print(f"[DEBUG chat] agent: {self.agent_name}, model: {model_name}, inject_failure: {inject_failure}, raw_env_val: '{os.getenv('INJECT_LLM_FAILURE')}'")
        if inject_failure and self.agent_name in ("epo_examiner", "first_examiner", "second_examiner") and model_name.lower() in ("deepseek-v4-flash", "v4-flash"):
            print(f"[DEBUG chat] Failure injected successfully for agent: {self.agent_name}")
            raise ValueError("Simulated 429 Rate Limit Exceeded")

        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
        


        if not api_key:
            raise ValueError("Production Configuration Error: DEEPSEEK_API_KEY is not configured.")

        # 映射与兼容模型名大小写
        mapped_model = model_name
        if model_name == "deepseek-V4-Pro":
            mapped_model = "deepseek-v4-pro"
        elif model_name == "V4-Flash":
            mapped_model = "deepseek-v4-flash"
        else:
            mapped_model = model_name.lower()

        now = time.time()
        cb_until = LLMFactory._circuit_breaker_until.get(mapped_model, 0)
        if now < cb_until:
            msg = f"[CIRCUIT_BREAKER] 模型 {mapped_model} 处于熔断期，{int(cb_until - now)}秒后恢复，直接走本地Fallback！"
            print(msg)
            if self.blackboard:
                await self.blackboard.add_debate_log(msg)
            raise ValueError(f"Circuit breaker active for {mapped_model}")
        if cb_until and now >= cb_until:
            msg = f"[CIRCUIT_BREAKER] 模型 {mapped_model} 熔断恢复"
            print(msg)
            if self.blackboard:
                await self.blackboard.add_debate_log(msg)
            LLMFactory._circuit_breaker_until[mapped_model] = 0
            LLMFactory._failure_counts[mapped_model] = 0

        base_url = api_base.rstrip("/")
        if base_url.endswith("/v1"):
            url = f"{base_url}/chat/completions"
        else:
            url = f"{base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": mapped_model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 1024
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    LLMFactory._failure_counts[mapped_model] = 0
                    data = response.json()
                    message = data["choices"][0]["message"]
                    return {
                        "content": message.get("content"),
                        "tool_calls": message.get("tool_calls"),
                        "reasoning_content": message.get("reasoning_content")
                    }
                else:
                    raise ValueError(f"LLM API Error: Status {response.status_code}, Body: {response.text}")
        except Exception as e:
            failures = LLMFactory._failure_counts.get(mapped_model, 0) + 1
            LLMFactory._failure_counts[mapped_model] = failures
            if failures >= 3:
                LLMFactory._circuit_breaker_until[mapped_model] = time.time() + 30
                msg = f"[CIRCUIT_BREAKER] 模型 {mapped_model} 连续失败超过3次，触发熔断，30秒内直接走本地Fallback！"
                print(msg)
                if self.blackboard:
                    await self.blackboard.add_debate_log(msg)

            raise ValueError(f"Failed to connect to LLM API ({mapped_model}): {str(e)}")






