from antgent.models.agent import TLLMInput


def estimate_tokens(model: str, messages: TLLMInput, tools: list[dict] | None = None) -> int:
    """
    Returns an accurate token estimation for the given model,
    handling multimodal messages, text, and tool schemas.
    """
    from litellm.utils import token_counter  # noqa: PLC0415

    return token_counter(model=model, messages=messages, tools=tools)  # type: ignore
