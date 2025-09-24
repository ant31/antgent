from functools import lru_cache

from temporalio.client import Client

from antgent.config import TemporalCustomConfigSchema, config
from antgent.utils.importpy import import_from_string


class TClientSingleton:
    _client: Client | None = None

    async def get_client(self, conf: TemporalCustomConfigSchema | None = None) -> Client:
        """Get a singleton Temporal client."""
        if self._client:
            return self._client

        if conf is None:
            conf = config().temporalio

        # The data converter can be a string, so we need to import it.
        @lru_cache(maxsize=1)
        def get_data_converter():
            if conf.converter:
                return import_from_string(conf.converter)
            return None

        self._client = await Client.connect(
            conf.host,
            namespace=conf.namespace,
            data_converter=get_data_converter(),
        )
        return self._client


_tclient_singleton = TClientSingleton()


async def tclient(conf: TemporalCustomConfigSchema | None = None) -> Client:
    """
    Get a singleton Temporal client.
    """
    return await _tclient_singleton.get_client(conf)
