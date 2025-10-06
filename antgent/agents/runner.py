import logging
from typing import TYPE_CHECKING, cast

from agents import Runner, RunResult, custom_span
from litellm.utils import get_max_tokens, token_counter

from antgent.models.agent import PrepareRun, TLLMInput

if TYPE_CHECKING:
    from antgent.agents.base import BaseAgent, TContext, TOutput

logger = logging.getLogger(__name__)


class ContextTooLargeError(ValueError): ...


class AgentRunnerMixin[TContext, TOutput]:
    """Mixin for running agents."""

    async def prep_input(
        self: "BaseAgent[TContext, TOutput]", llm_input: TLLMInput, ctx: TContext
    ) -> PrepareRun[TContext]:
        if not isinstance(llm_input, str) and not isinstance(llm_input, list):
            raise ValueError(f"Input must be a string or list of TResponseInputItem, got {type(llm_input)}")
        return PrepareRun(llm_input=llm_input, context=ctx, short_cut=False)

    async def prep_response(
        self: "BaseAgent[TContext, TOutput]", response: RunResult | None, ctx: TContext
    ) -> RunResult | None:
        _ = ctx
        if response is None:
            return None
        return response

    async def run_result(
        self: "BaseAgent[TContext, TOutput]",
        agent,
        llm_input: TLLMInput,
        context: TContext,
        check_tokens: bool = False,
        **kwargs,
    ) -> RunResult | None:
        with custom_span("Prepare input"):
            prep_run = await self.prep_input(llm_input, context)
            if prep_run.short_cut:
                logger.info("ShortCut requested: stoping the run")
                return None

            # Filter empty messages if llm_input is a list
            if isinstance(prep_run.llm_input, list):
                prep_run.llm_input = self._filter_empty_messages(prep_run.llm_input)

            if check_tokens and self.max_tokens > 0 and self.count_tokens(prep_run.llm_input) > self.max_tokens:
                raise ContextTooLargeError(f"Input too large: {self.count_tokens(prep_run.llm_input)} tokens")

        # Merge frozen config run_kwargs with runtime kwargs (runtime takes precedence)
        merged_kwargs = {**self.agent_config.run_kwargs, **kwargs}
        res = await Runner.run(agent, input=prep_run.llm_input, context=prep_run.context, **merged_kwargs)
        return await self.prep_response(res, context)

    async def run(
        self: "BaseAgent[TContext, TOutput]",
        agent,
        llm_input: TLLMInput,
        context: TContext,
        check_tokens: bool = False,
        **kwargs,
    ) -> TOutput | None:
        res = await self.run_result(agent, llm_input, context, check_tokens, **kwargs)
        if res is None:
            return None
        return cast(TOutput, res.final_output)

    def count_tokens(self: "BaseAgent[TContext, TOutput]", content) -> int:
        return token_counter(self.model, messages=content)

    @property
    def max_tokens(self: "BaseAgent[TContext, TOutput]") -> int:
        if self._max_tokens is None:
            maxtokens = get_max_tokens(self.model)
            if maxtokens is None:
                maxtokens = 0
            if self.conf.max_input_tokens and maxtokens > 0:
                maxtokens = min(self.conf.max_input_tokens, maxtokens)
            self._max_tokens = maxtokens
        return self._max_tokens
