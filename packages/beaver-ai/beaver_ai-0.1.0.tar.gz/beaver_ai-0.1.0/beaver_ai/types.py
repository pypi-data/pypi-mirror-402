from typing import TypedDict, Literal, NotRequired


class Message(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(TypedDict, total=False):
    model: str
    messages: list[Message]
    temperature: float
    max_output_tokens: int
    top_p: float


class Usage(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Choice(TypedDict):
    index: int
    message: Message
    finish_reason: str | None


class ChatCompletionResponse(TypedDict):
    id: str
    model: str
    choices: list[Choice]
    usage: NotRequired[Usage]
