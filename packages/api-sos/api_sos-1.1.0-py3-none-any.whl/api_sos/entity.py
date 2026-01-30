from enum import StrEnum, auto
from typing import Any, Literal

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from api_sos.utils import auto_reader


class Method(StrEnum):
    GET = auto()
    HEAD = auto()
    OPTIONS = auto()
    TRACE = auto()
    PUT = auto()
    DELETE = auto()
    POST = auto()
    PATCH = auto()
    CONNECT = auto()


@dataclass
class HTTPRequestTimeout:
    total: float | None = None
    connect: float | None = None
    sock_read: float | None = None
    sock_connect: float | None = None
    ceil_threshold: float = 5


@dataclass
class HTTPVersion:
    major: int
    minor: int


@dataclass
class AssertResponse:
    headers: dict[str, str] | None = Field(None, description="The headers should be in the response")
    http_status: int | None = Field(None, description="The http status should be in the response")
    http_version: HTTPVersion | None = Field(None, description="The http version should be in the response")
    encoding: str = Field("utf-8", description="The encoding should be in the response")
    content: str | dict | list | None = Field(None, description="The content should be in the response")


@dataclass
class BasicAuth:
    login: str
    password: str = ""
    encoding: str = "latin1"


@dataclass(
    config=ConfigDict(
        populate_by_name=True,
    )
)
class Parameter:
    name: str
    in_: Literal["path", "query", "header", "cookie"] = Field(..., alias="in")
    value: Any = Field(..., description="The value to be used")


@dataclass
class Payload:
    value: dict | bytes = Field(..., description="The payload to be used")


@dataclass(
    config=ConfigDict(
        populate_by_name=True,
    )
)
class APICheck:
    name: str
    pathname: str = Field(..., description="The path to the resource to be checked(part of uri)")
    method: Method = Field(Method.GET, description="The method to be used")
    payload: Payload | None = Field(None, description="The payload to be used")
    parameters: list[Parameter] | None = Field(None, description="The parameters to be used")
    headers: dict | None = Field(None, description="The headers to be used")
    proxy: str | None = Field(None, description="The proxy to be used")
    proxy_auth: BasicAuth | None = Field(None, description="The proxy auth to be used")
    timeout: HTTPRequestTimeout | None = Field(None, description="The timeout to be used")
    assert_: AssertResponse | None = Field(None, alias="assert", description="The asserts to be used")


@dataclass
class Input:
    version: str
    endpoint: str | None = Field(None, description="The endpoint to be used")
    checks: list[APICheck] = Field(..., description="The checks to be used", default_factory=list)  # type: ignore

    @classmethod
    def load(cls, file: str):
        return Input(**auto_reader(file))


@dataclass
class DiffResult:
    field: str
    assert_value: Any
    actual_value: Any
