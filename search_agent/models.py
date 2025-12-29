import html

from openai.types.completion_usage import CompletionUsage
from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str

    def __str__(self) -> str:
        return f"<em>{html.escape(self.source)}</em>\n"


class AgentResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]

    def __str__(self) -> str:
        result = f"<b>Вопрос</b>\n{html.escape(self.question)}\n\n<b>Ответ</b>\n{html.escape(self.answer)}"
        if self.citations:
            citations = "\n".join([str(c) for c in self.citations])
            result += f"\n\n<em>Источники</em>\n{citations}"
        return result


class UsageStats(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    elapsed_seconds: float = 0.0

    def add(self, usage: CompletionUsage | None, elapsed: float = 0.0) -> None:
        if usage:
            self.prompt_tokens += usage.prompt_tokens or 0
            self.completion_tokens += usage.completion_tokens or 0
            self.total_tokens += usage.total_tokens or 0
        self.calls += 1
        self.elapsed_seconds += elapsed

    def cost(self, input_price: float, output_price: float) -> float:
        """Цена указывается за 1M токенов"""
        return (
            self.prompt_tokens * input_price + self.completion_tokens * output_price
        ) / 1_000_000

    @property
    def tokens_per_second(self) -> float:
        if self.elapsed_seconds == 0:
            return 0
        return self.completion_tokens / self.elapsed_seconds

    def __str__(self) -> str:
        return (
            f"Calls: {self.calls}\n"
            f"Prompt tokens: {self.prompt_tokens:,}\n"
            f"Completion tokens: {self.completion_tokens:,}\n"
            f"Total tokens: {self.total_tokens:,}\n"
            f"Time: {self.elapsed_seconds:.2f}s\n"
            f"Speed: {self.tokens_per_second:.1f} tokens/s"
        )


class AgentResult(BaseModel):
    response: AgentResponse
    usage: UsageStats = Field(default_factory=UsageStats)
    tool_calls: list[dict] = Field(default_factory=list)
