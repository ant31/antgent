# This file is intentionally left empty to ensure that `antgent` can be safely
# imported within a Temporal workflow sandbox. Eagerly importing agent
# implementations here would pull in non-deterministic dependencies like `httpx`.
#
# Please import agents directly from their respective modules, e.g.:
# from antgent.agents.base import BaseAgent
