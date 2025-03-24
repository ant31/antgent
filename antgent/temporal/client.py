from temporalio.client import Client
from temporalloop.converters.pydantic import pydantic_data_converter

from antgent.config import TemporalCustomConfigSchema, config

TEMPORAL_CLIENT: Client | None = None


async def tclient(conf: TemporalCustomConfigSchema | None = None) -> Client:
    return await GTClient(conf).client()


class TClient:
    def __init__(self, conf: TemporalCustomConfigSchema | None = None) -> None:
        if conf is None:
            conf = config().temporalio

        self.conf: TemporalCustomConfigSchema = conf
        self._client = None

    def set_client(self, client: Client) -> None:
        self._client = client

    async def client(self) -> Client:
        if self._client is None:
            self._client = await Client.connect(
                self.conf.host,
                namespace=self.conf.namespace,
                lazy=True,
                data_converter=pydantic_data_converter,
            )
        return self._client


class GTClient(TClient):
    def __new__(cls, conf: TemporalCustomConfigSchema | None = None):
        if not hasattr(cls, "instance") or cls.instance is None:
            cls.instance = TClient(conf)
        return cls.instance

    def reinit(self) -> None:
        self.instance = None
