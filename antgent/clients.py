from functools import cache

from google import genai
from openai import AsyncOpenAI, OpenAI

from antgent.config import config
from antgent.models.agent import LLMsConfigSchema


@cache
def openai_client(project_name: str = "openai", llms: LLMsConfigSchema | None = None) -> OpenAI:
    """Create a OpenAI instance with the given api_key
    It cache the answer for the same api_key
    use openai.cache_clear() to clear the cache
    """
    if llms is None:
        llms = config().llms

    project = llms.get_project(project_name)
    if project is None:
        # use default with ENV
        return OpenAI()

    return OpenAI(
        api_key=project.api_key,
        organization=project.organization_id,
        project=project.project_id,
        base_url=project.url,
    )


@cache
def openai_aclient(project_name: str = "openai", llms: LLMsConfigSchema | None = None) -> AsyncOpenAI:
    """Create a OpenAI instance with the given api_key
    It cache the answer for the same api_key
    use openai.cache_clear() to clear the cache
    """
    if llms is None:
        llms = config().llms

    project = llms.get_project(project_name)
    if project is None:
        # use default with ENV
        return AsyncOpenAI()

    return AsyncOpenAI(
        api_key=project.api_key,
        organization=project.organization_id,
        project=project.project_id,
        base_url=project.url,
    )


@cache
def genai_client(project_name: str = "gemini", llms: LLMsConfigSchema | None = None) -> genai.Client:
    """Create a GenAI instance with the given api_key
    It cache the answer for the same api_key
    use genai.cache_clear() to clear the cache
    """
    if llms is None:
        llms = config().llms

    project = llms.get_project(project_name)
    if project is None:
        return genai.Client()
    api_key = project.api_key
    return genai.Client(api_key=api_key)
