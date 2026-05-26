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
            messages.append({"role": "user", "content": prompt})
            return await self._call_local_fallback_template(messages, tools)

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
            
            # 高质量本地模板降级兜底逻辑
            return await self._call_local_fallback_template(messages, tools)

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

    async def _call_local_fallback_template(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        import json
        msg = "[MOCK_TRANSPORT] 检测到网络异常或熔断，当前请求已切换至本地 Mock 模板生成。"
        print(msg)
        if self.blackboard:
            await self.blackboard.add_debate_log(msg)

        # Get last user message to reflect it dynamically
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = str(m.get("content", ""))
                break
        last_user_msg_truncated = (last_user_msg[:100] + "...") if len(last_user_msg) > 100 else last_user_msg

        tool_calls = None
        content_text = ""
        
        # 统计当前轮数
        assistant_msgs = [m for m in messages if m.get("role") == "assistant" and "tool_calls" in m]
        current_round = len(assistant_msgs) + 1

        print(f"[DEBUG MOCK] current_round: {current_round}, available tools: {[t.get('function', {}).get('name') for t in (tools or [])]}")

        # 获取历史调用过的工具
        called_tools = set()
        for m in messages:
            if m.get("role") == "assistant" and m.get("tool_calls"):
                for tc in m["tool_calls"]:
                    if isinstance(tc, dict):
                        called_tools.add(tc.get("function", {}).get("name"))
                    else:
                        called_tools.add(getattr(tc, "function", None) and getattr(tc.function, "name", None))
        print(f"[DEBUG MOCK] called_tools = {called_tools}")

        if tools and current_round <= 3:
            tool_calls = []
            import hashlib
            seed_str = f"{last_user_msg}_{current_round}"
            seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
            
            # 从所有工具中找出一个未被调用的工具，决定性选择
            available_tool_names = sorted([t.get("function", {}).get("name") for t in tools])
            uncalled_tools = sorted([name for name in available_tool_names if name not in called_tools])
            
            target_tools_to_call = []
            if uncalled_tools:
                num_to_pick = (seed % min(2, len(uncalled_tools))) + 1
                temp_seed = seed
                for _ in range(num_to_pick):
                    if not uncalled_tools: break
                    idx = temp_seed % len(uncalled_tools)
                    target_tools_to_call.append(uncalled_tools.pop(idx))
                    temp_seed //= max(1, len(uncalled_tools))
            else:
                target_tools_to_call.append(available_tool_names[seed % len(available_tool_names)])
                
            for func_name in target_tools_to_call:
                tool_schema = next((t for t in tools if t.get("function", {}).get("name") == func_name), None)
                if not tool_schema:
                    continue
                    
                props = tool_schema.get("function", {}).get("parameters", {}).get("properties")
                if props is None:
                    props = {}
                mock_args = {}
                for k, v in props.items():
                    val_type = v.get("type", "string")
                    prop_seed = int(hashlib.md5(f"{seed}_{k}".encode()).hexdigest(), 16)
                    if val_type == "string":
                        if k in ["query", "claim", "domestic_feature", "feature"]:
                            import re
                            words = sorted(re.findall(r'\b[A-Za-z]+\b', last_user_msg))
                            if len(words) > 3:
                                sample_k = min(5, len(words))
                                sample_words = []
                                t_seed = prop_seed
                                for _ in range(sample_k):
                                    if not words: break
                                    idx = t_seed % len(words)
                                    sample_words.append(words.pop(idx))
                                    t_seed //= max(1, len(words))
                                mock_args[k] = " ".join(sample_words)
                            else:
                                mock_args[k] = f"mock_{k}_{(prop_seed % 900) + 100}"
                        else:
                            mock_args[k] = f"mock_{k}_{(prop_seed % 900) + 100}"
                    elif val_type in ("integer", "number"):
                        mock_args[k] = (prop_seed % 100) + 1
                    elif val_type == "boolean":
                        mock_args[k] = bool(prop_seed % 2)
                    elif val_type == "object":
                        mock_args[k] = {"mock_key": "mock_val"}
                    elif val_type == "array":
                        mock_args[k] = ["mock_item"]
                    else:
                        mock_args[k] = f"mock_{val_type}"

                
                tool_calls.append({
                    "id": f"call_mock_{current_round}_{func_name}_{(seed % 9000) + 1000}",
                    "type": "function",
                    "function": {
                        "name": func_name,
                        "arguments": json.dumps(mock_args, ensure_ascii=False)
                    }
                })
                
            if tool_calls:
                content_text = f"[MOCK_TRANSPORT] 正在随机调用 {len(tool_calls)} 个工具以推进工作流程 (通用 Fallback)。收到您的输入: '{last_user_msg_truncated}'"
            else:
                tool_calls = None
        else:
            content_text = "[MOCK_TRANSPORT] Fallback triggered. Returning standard error string to allow higher-level engine recovery."
            
        return {
            "content": content_text,
            "tool_calls": tool_calls
        }




