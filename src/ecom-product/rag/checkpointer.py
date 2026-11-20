from typing import Any, NotRequired, TypedDict
from . import rag_engine
from .rag_engine import SearchInput
from  langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.graph import StateGraph, START, END
from ..db.db import get_db
from ..config.config import settings

class ChatSearchState(TypedDict):
    user_query: str
    intent: NotRequired[dict[str, Any]]


def merge_content_node(state: ChatSearchState) -> ChatSearchState:
    prev_intent = state.get("intent")
    query = state["user_query"]

    if prev_intent:
        prompt_input = (
            f"Previous active search filters: {prev_intent}\n"
            f"Follow-up user message: {query}\n"
            "Instruction: Keep all previous filters (especially gender, gift_for, occasion) intact "
            "UNLESS the follow-up message explicitly changes or overrides them."
        )

    else: 
        prompt_input = query

    update_intent: SearchInput = rag_engine.extract_intent(prompt_input)

    return {"user_query": query, "intent": update_intent.model_dump()}


_checkpointer = MongoDBSaver(get_db().client, db_name=settings.db_name)

_builder = StateGraph(ChatSearchState)
_builder.add_node("merge_intent", merge_content_node)
_builder.add_edge(START, "merge_intent")
_builder.add_edge("merge_intent", END)

_state_builder = _builder.compile(checkpointer=_checkpointer)


def resolve_stateful_intent(user_query: str, thread_id:str) -> SearchInput:
    result = _state_builder.invoke(
        {"user_query": user_query},
        config={"configurable": {"thread_id": thread_id}},
    )

    return rag_engine.SearchInput.model_validate(result["intent"])
