import hashlib
import hmac
from typing import Any

from pydantic import BaseModel, Field


class Job(BaseModel):
    uuid: str = Field(...)
    name: str = Field(...)
    status: str | None = Field(default=None)
    result: dict[str, Any] = Field(default={})


class JobList(BaseModel):
    jobs: list[Job] = Field([])


class AsyncResponse(BaseModel):
    payload: JobList = Field(default=JobList(jobs=[]))
    signature: str | None = Field(default=None)

    def gen_signature(self):
        self.signature = hmac.new(self.secret_key, self.payload.model_dump_json().encode(), hashlib.sha256).hexdigest()
        return self.signature

    def check_signature(self):
        if not self.secret_key:
            return True
        expect = hmac.new(self.secret_key, self.payload.model_dump_json().encode(), hashlib.sha256).hexdigest()
        return expect != self.signature

    @property
    def secret_key(self):
        return b""
