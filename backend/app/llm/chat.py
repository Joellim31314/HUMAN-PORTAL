"""Follow-up chat with one simulated Londoner, grounded in their week."""
import json

from app.llm.client import chat_json, llm_available
from app.llm.prompts import CHAT_SYSTEM, persona_card
from app.schemas import AgentTrace, ChatReply, ChatTurn, ProductInput

MAX_TURNS = 12


async def chat_with_agent(product: ProductInput, trace: AgentTrace,
                          messages: list[ChatTurn]) -> ChatReply:
    if not llm_available():
        return ChatReply(reply="Chat needs a DeepSeek key: set DEEPSEEK_API_KEY in backend/.env.",
                         source="unavailable")
    *history, question = messages[-MAX_TURNS:]
    payload = {
        "persona": persona_card(trace.agent),
        "product": product.model_dump(mode="json"),
        "outcome": trace.outcome.model_dump(mode="json"),
        "trace": [e.model_dump(mode="json") for e in trace.trace],
        "earlier_interview_quote": trace.interview.quote if trace.interview else None,
        "conversation_so_far": [t.model_dump() for t in history],
        "retailer_asks": question.content,
    }
    value = await chat_json(CHAT_SYSTEM, json.dumps(payload), temperature=0.7, max_tokens=400)
    reply = value.get("reply") if isinstance(value, dict) else None
    if not isinstance(reply, str) or not reply.strip():
        return ChatReply(reply="Sorry, I lost my train of thought. Could you ask that again?",
                         source="unavailable")
    return ChatReply(reply=reply.strip(), source="llm")
