import json
import re
from typing import Any, Dict

from .base import AgentInput, BaseAgent
from .skills.registry import registry


class AttendanceAgent(BaseAgent):
    name = "attendance"
    display_name = "考勤助手"
    handle = "@考勤助手"
    description = "考勤助手：打卡/请假/加班/统计"
    model = ""
    language = "zh-CN"
    system_prompt = (
        "你是考勤助手，负责处理打卡、请假、加班、考勤统计等问题。"
        "请输出严格 JSON，字段为：intent, slots, reply。\n"
        "intent 只能是：check_in, check_out, leave, overtime, stats, query, other。\n"
        "slots 是一个对象，尽量从用户输入中提取：date, time, duration, reason, range, person。\n"
        "reply 是给用户的中文答复，简洁清晰。\n"
        "只输出 JSON，不要额外文本。"
    )

    def _simple_parse(self, text: str) -> Dict[str, Any]:
        lower = text.lower()
        intent = "other"
        if "打卡" in text or "签到" in text or "check in" in lower:
            intent = "check_in"
        elif "下班" in text or "签退" in text or "check out" in lower:
            intent = "check_out"
        elif "请假" in text or "休假" in text or "假" in text:
            intent = "leave"
        elif "加班" in text:
            intent = "overtime"
        elif "统计" in text or "汇总" in text or "报表" in text:
            intent = "stats"
        elif "查询" in text or "查看" in text:
            intent = "query"

        time_match = re.search(r"(\d{1,2}:\d{2})", text)
        date_match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", text)
        duration_match = re.search(r"(\d+(\.\d+)?\s*(小时|h|天|d))", text)

        slots: Dict[str, Any] = {}
        if time_match:
            slots["time"] = time_match.group(1)
        if date_match:
            slots["date"] = date_match.group(1)
        if duration_match:
            slots["duration"] = duration_match.group(1)

        return {
            "intent": intent,
            "slots": slots,
            "reply": "我已记录你的请求，请确认是否需要提交到考勤系统。",
        }

    def run(self, payload: AgentInput) -> str:
        client = registry.llm()
        if self.model:
            client.model = self.model
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": payload.text},
        ]
        try:
            response = client.chat(messages)
            try:
                data = json.loads(response)
                return data.get("reply", "")
            except Exception:
                # If model didn't follow JSON instruction, return raw content.
                return response
        except Exception as exc:
            data = self._simple_parse(payload.text)
            return f"LLM 调用失败：{exc}。{data['reply']}"


AGENT = AttendanceAgent()
