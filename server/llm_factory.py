# llm_factory.py
# LLM 工厂装载器 (内置主备模型 Try-Catch 自动 Fallback 容灾降级机制)

import asyncio
import os
import httpx
from typing import Dict, Any, Optional

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

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        """
        主备 LLM 自动 Fallback 容灾路由接口
        """
        try:
            return await self._call_model(self.primary_model, prompt, system_instruction)
        except Exception as e:
            # 判断是否存在备用模型，若有则进行降级处理
            if self.fallback_model:
                warning_msg = f"[LLM 降级预警] Agent '{self.agent_name}' 的首选模型 '{self.primary_model}' 请求异常: {str(e)}。系统已自动且无感降级至备选模型 '{self.fallback_model}'。"
                
                # 同步记录到黑板 debate_logs
                if self.blackboard:
                    await self.blackboard.add_debate_log(warning_msg)
                    
                # 重新尝试调用备用模型
                return await self._call_model(self.fallback_model, prompt, system_instruction)
            else:
                # 无备选，抛出异常
                raise e

    async def _call_model(self, model_name: str, prompt: str, system_instruction: str) -> str:
        # 运行时动态热加载 .env 文件，保障宿主进程即使不重启也能即时应用最新的凭证改动
        load_dotenv()
        
        # 混沌工程故障注入（仅在测试环境中通过设置 INJECT_LLM_FAILURE=true 激活）
        inject_failure = os.getenv("INJECT_LLM_FAILURE", "").lower() in ("true", "1")
        if inject_failure and self.agent_name == "epo_examiner" and model_name.lower() in ("deepseek-v4-flash", "v4-flash"):
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

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    raise ValueError(f"LLM API Error: Status {response.status_code}, Body: {response.text}")
        except Exception as e:
            # 向上抛出异常以支持主备 Fallback 容灾降级
            raise ValueError(f"Failed to connect to LLM API ({mapped_model}): {str(e)}")


