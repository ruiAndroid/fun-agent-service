import json
import logging
import sys

from agents.registry import list_agents, run_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("agent-runtime")


def main() -> int:
    args = sys.argv[1:]
    if "--list" in args:
        print(json.dumps(list_agents(), ensure_ascii=False))
        return 0

    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"error": "empty payload"}, ensure_ascii=False))
        return 1

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"invalid json: {exc}"}, ensure_ascii=False))
        return 1

    agent = payload.get("agent")
    user_input = payload.get("input", "")
    context = payload.get("context", {})
    trace_id = context.get("trace_id") if isinstance(context, dict) else None
    try:
        logger.info("run agent=%s trace_id=%s", agent, trace_id)
        output = run_agent(agent, user_input, context)
    except Exception as exc:
        logger.exception("agent runtime error trace_id=%s", trace_id)
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps({"output": output}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
