import json
import re
from typing import Any, Dict

from .base import AgentInput, BaseAgent
from .skills.registry import registry


class ExpenseAgent(BaseAgent):
    """
    财务报销助手（简单版）
    - 优先走 LLM（如果 llm.json 配置正常）
    - 失败时走规则解析，给出结构化提示
    """

    name = "expense"
    display_name = "财务报销"
    handle = "@财务报销"
    description = "财务报销：报销流程/材料清单/发票问题/进度查询"
    model = ""
    language = "zh-CN"
    system_prompt = (
        "你是财务报销助手，负责解答报销流程、材料清单、发票合规、进度查询等问题。"
        "请输出严格 JSON，字段为：intent, slots, reply。\n"
        "intent 只能是：submit, materials, invoice, policy, progress, other。\n"
        "slots 是一个对象，尽量从用户输入中提取：amount, category, date, company, project, invoice_type。\n"
        "reply 是给用户的中文答复，简洁清晰，可给出下一步操作。\n"
        "只输出 JSON，不要额外文本。"
    )

    def _simple_parse(self, text: str) -> Dict[str, Any]:
        lower = text.lower()
        intent = "other"
        if "报销" in text and ("提交" in text or "申请" in text or "发起" in text):
            intent = "submit"
        elif "材料" in text or "需要什么" in text or "要什么" in text:
            intent = "materials"
        elif "发票" in text or "invoice" in lower:
            intent = "invoice"
        elif "制度" in text or "政策" in text or "标准" in text or "额度" in text:
            intent = "policy"
        elif "进度" in text or "到哪了" in text or "审核" in text or "查询" in text:
            intent = "progress"

        amount_match = re.search(r"(\d+(?:\.\d+)?)\s*(元|rmb|cny)?", lower)
        date_match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", text)

        slots: Dict[str, Any] = {}
        if amount_match:
            slots["amount"] = amount_match.group(1)
        if date_match:
            slots["date"] = date_match.group(1)

        # very naive category hints
        if "差旅" in text or "出差" in text:
            slots["category"] = "travel"
        elif "餐" in text or "饭" in text:
            slots["category"] = "meal"
        elif "打车" in text or "出租" in text or "滴滴" in text:
            slots["category"] = "transport"

        reply = "我可以帮你梳理报销流程与材料。你想报销哪一类费用？金额/日期/发票类型也可以一起告诉我。"
        if intent == "materials":
            reply = "一般需要：报销单、发票/电子票据、支付凭证（如付款截图/回单）、行程或费用说明（如差旅单）。具体以公司制度为准。"
        elif intent == "invoice":
            reply = "请确认发票抬头、税号、金额、开票日期、项目名称等是否符合公司要求；电子发票需提供 PDF/链接及支付凭证。"
        elif intent == "progress":
            reply = "请提供报销单号或提交日期/金额，我可以帮你整理查询要点（当前系统暂不直连财务审批流）。"
        elif intent == "submit":
            reply = "你可以告诉我费用类型、金额、发生日期、是否有发票/支付凭证，我帮你生成一份提交前的检查清单。"
        elif intent == "policy":
            reply = "请说明你关注的政策点（如餐补标准、差旅住宿上限、交通费），我帮你按常见口径列出需要确认的规则。"

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


AGENT = ExpenseAgent()

