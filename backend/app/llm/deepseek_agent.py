import json
from collections.abc import Callable
from typing import Any

import httpx

from app.llm.deepseek import LLMClientError, LLMConfigurationError
from app.schemas.agent import AgentChatResponse, AgentToolExecution


ToolExecutor = Callable[[str, dict[str, Any]], dict[str, Any]]


class DeepSeekToolCallingClient:
    SYSTEM_PROMPT = """
你是电力交易辅助决策 Agent。

你的职责是理解用户意图，并在需要读取或分析具体市场数据时调用工具。
不要编造数据库中不存在的数据，不要自己猜测 market_data_id。
当用户要求分析某条市场数据时，应优先调用 analyze_market 工具。
工具返回的是系统确定性计算结果，你应基于工具结果用中文做简洁解释，并明确风险和数据局限。
如果用户没有提供可识别的市场数据 ID，应要求用户提供 ID，而不是调用工具。
""".strip()

    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "analyze_market",
                "description": (
                    "根据 market_data_id 读取市场数据并计算价格偏差、净负荷、"
                    "新能源占比和确定性市场信号。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "market_data_id": {
                            "type": "integer",
                            "description": "市场数据记录 ID",
                            "minimum": 1,
                        }
                    },
                    "required": ["market_data_id"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    def __init__(
        self,
        api_key: str | None,
        base_url: str,
        model: str,
        timeout_seconds: float = 30.0,
        max_tool_rounds: int = 3,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_tool_rounds = max_tool_rounds

    def run(
        self,
        message: str,
        tool_executor: ToolExecutor,
    ) -> AgentChatResponse:
        if not self.api_key:
            raise LLMConfigurationError(
                "DeepSeek API key is not configured"
            )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]
        executions: list[AgentToolExecution] = []

        for _ in range(self.max_tool_rounds + 1):
            assistant_message = self._request(messages)
            tool_calls = assistant_message.get("tool_calls") or []

            if not tool_calls:
                content = assistant_message.get("content")
                if not isinstance(content, str) or not content.strip():
                    raise LLMClientError(
                        "DeepSeek returned empty agent content"
                    )

                return AgentChatResponse(
                    answer=content.strip(),
                    model=self.model,
                    tool_executions=executions,
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.get("content"),
                    "tool_calls": tool_calls,
                }
            )

            for tool_call in tool_calls:
                tool_call_id, tool_name, arguments = self._parse_tool_call(
                    tool_call
                )
                result = tool_executor(tool_name, arguments)

                executions.append(
                    AgentToolExecution(
                        tool_name=tool_name,
                        arguments=arguments,
                        result=result,
                    )
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(
                            result,
                            ensure_ascii=False,
                        ),
                    }
                )

        raise LLMClientError("Agent exceeded maximum tool rounds")

    def _request(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": self.TOOLS,
            "tool_choice": "auto",
            "thinking": {"type": "disabled"},
            "max_tokens": 1200,
        }

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMClientError(
                f"DeepSeek agent request failed: {exc}"
            ) from exc

        try:
            data = response.json()
            message = data["choices"][0]["message"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMClientError(
                "DeepSeek returned an unexpected agent response"
            ) from exc

        if not isinstance(message, dict):
            raise LLMClientError(
                "DeepSeek returned an invalid agent message"
            )

        return message

    @staticmethod
    def _parse_tool_call(
        tool_call: dict[str, Any],
    ) -> tuple[str, str, dict[str, Any]]:
        try:
            tool_call_id = tool_call["id"]
            function = tool_call["function"]
            tool_name = function["name"]
            raw_arguments = function["arguments"]
            arguments = json.loads(raw_arguments)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise LLMClientError(
                "DeepSeek returned an invalid tool call"
            ) from exc

        if not isinstance(arguments, dict):
            raise LLMClientError(
                "DeepSeek tool arguments must be a JSON object"
            )

        return str(tool_call_id), str(tool_name), arguments
