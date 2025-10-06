from antgent.agents.summarizer.models import SummaryInput
from antgent.models.agent import AgentInput


class TextSummarizerWorkflowContext(SummaryInput): ...


class AgentTextSummarizerWorkflowCtxInput(AgentInput[TextSummarizerWorkflowContext]): ...
