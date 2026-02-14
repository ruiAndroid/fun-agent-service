import json
import re
from typing import Any, Dict

from .base import AgentInput, BaseAgent
from .skills.registry import registry


class AdminAgent(BaseAgent):
    """
    行政管家（简单版）
    - 优先走 LLM（如果 llm.json 配置正常）
    - 失败时走规则解析
    """

    name = "admin"
    display_name = "行政管家"
    handle = "@行政管家"
    description = "行政管家：维修报修/物品领取/制度咨询/办公支持"
    model = ""
    language = "zh-CN"
    system_prompt = (
        "你是行政管家，负责处理维修报修、物品领取、行政制度咨询、办公支持等问题。"
        "请输出严格 JSON，字段为：intent, slots, reply。\n"
        "intent 只能是：repair, pickup, consult, other。\n"
        "slots 是一个对象，尽量从用户输入中提取：location, item, issue, time, contact。\n"
        "reply 是给用户的中文答复，简洁清晰，给出下一步动作（需要哪些信息/如何提交）。\n"
        "只输出 JSON，不要额外文本。"
    )

    def _simple_parse(self, text: str) -> Dict[str, Any]:
        lower = text.lower()
        intent = "other"

        if "维修" in text or "报修" in text or "修理" in text or "坏了" in text:
            intent = "repair"
        elif "领取" in text or "领用" in text or "申领" in text:
            intent = "pickup"
        elif "咨询" in text or "怎么" in text or "流程" in text or "制度" in text or "规定" in text:
            intent = "consult"

        slots: Dict[str, Any] = {}

        # simple extraction
        loc_match = re.search(r"(?:在|位于|位置|地点)[:：]?\s*([^\s，。,。]{2,20})", text)
        if loc_match:
            slots["location"] = loc_match.group(1)

        item_match = re.search(r"(?:领取|领用|申领)[:：]?\s*([^\s，。,。]{1,20})", text)
        if item_match:
            slots["item"] = item_match.group(1)

        time_match = re.search(r"(\d{1,2}:\d{2})", text)
        if time_match:
            slots["time"] = time_match.group(1)

        # rough contact (phone)
        phone_match = re.search(r"(\b1\d{10}\b)", text)
        if phone_match:
            slots["contact"] = phone_match.group(1)

        reply = "我可以帮你处理行政支持。请补充具体需求与相关信息，我再给你下一步操作。"
        if intent == "repair":
            reply = (
                "好的，我来帮你报修。请提供：问题现象、具体位置（楼层/工位/会议室）、紧急程度、方便维修的时间、联系人。"
            )
        elif intent == "pickup":
            reply = (
                "可以的。请告诉我：需要领取的物品名称/数量、用途、领取人、领取时间；如有部门/项目编码也一并提供。"
            )
        elif intent == "consult":
            reply = "你想咨询哪一项行政制度/流程？例如：办公用品申请、门禁/工位、访客流程、会议室预定、快递收发等。"

        return {"intent": intent, "slots": slots, "reply": reply}

    def run(self, payload: AgentInput) -> str:
        trace = f"[trace={payload.trace_id}] " if payload.trace_id else ""
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
                return f"{trace}{data.get('reply', '')}"
            except Exception:
                return f"{trace}{response}"
        except Exception as exc:
            data = self._simple_parse(payload.text)
            return f"{trace}LLM 调用失败：{exc}。{data['reply']}"


AGENT = AdminAgent()

