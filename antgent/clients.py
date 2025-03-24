from functools import cache

from agents import set_tracing_export_api_key
from google import genai
from openai import AsyncOpenAI, OpenAI

from antgent.config import config


@cache
def openai_client(project_name: str = "") -> OpenAI:
    """Create a OpenAI instance with the given api_key
    It cache the answer for the same api_key
    use openai.cache_clear() to clear the cache
    """
    if not project_name:
        project = config().openai.projects[0]
    else:
        project = getattr(config().openai.projects, project_name)
    openaiconf = config().openai
    api_key = project.api_key
    organization = openaiconf.organization_id
    base_url = openaiconf.url
    return OpenAI(
        api_key=api_key,
        organization=organization,
        project=project.project_id,
        base_url=base_url,
    )


@cache
def openai_aclient(project_name: str = "") -> AsyncOpenAI:
    """Create a OpenAI instance with the given api_key
    It cache the answer for the same api_key
    use openai.cache_clear() to clear the cache
    """
    if not project_name:
        project = config().openai.projects[0]
    else:
        project = config().openai.get_project(project_name)
        if project is None:
            raise ValueError(f"Project {project_name} not found")
    openai = config().openai.get_project("openai")

    if openai is not None:
        print("set_Tracing")
        set_tracing_export_api_key(openai.api_key)
    openaiconf = config().openai
    api_key = project.api_key
    organization = openaiconf.organization_id
    base_url = project.url

    return AsyncOpenAI(
        api_key=api_key,
        organization=organization,
        project=project.project_id,
        base_url=base_url,
    )


@cache
def genai_client(project_name: str = "gemini") -> genai.Client:
    """Create a GenAI instance with the given api_key
    It cache the answer for the same api_key
    use genai.cache_clear() to clear the cache
    """
    project = config().openai.get_project(project_name)
    if project is None:
        raise ValueError(f"Project {project_name} not found")
    api_key = project.api_key
    return genai.Client(api_key=api_key)
