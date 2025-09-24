from antgent.agents.summarizer.models import SummaryInput
from antgent.models.agent import AgentWorkflowInput


class TextSummarizerWorkflowContext(SummaryInput): ...


class AgentTextSummarizerWorkflowCtxInput(AgentWorkflowInput[TextSummarizerWorkflowContext]): ...
