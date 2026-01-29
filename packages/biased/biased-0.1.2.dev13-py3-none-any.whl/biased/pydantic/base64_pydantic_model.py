import base64
import binascii
import json
from json import JSONDecodeError
from typing import Annotated, Any, TypeVar

from pydantic import BaseModel, BeforeValidator, PlainSerializer

T = TypeVar("T", bound=BaseModel)


def _decode_b64_json(v: Any) -> Any:
    """Decodes a Base64 string into a Python dictionary."""
    if isinstance(v, str):
        try:
            decoded_bytes = base64.b64decode(v)
            return json.loads(decoded_bytes.decode())
        except (binascii.Error, JSONDecodeError):
            # If decoding fails, we pass it through so Pydantic
            # can raise a standard validation error later.
            return v
    return v


def _encode_b64_json(v: Any) -> str:
    """Serializes a Pydantic model into a Base64 encoded JSON string."""
    if isinstance(v, BaseModel):
        json_str = v.model_dump_json()
        return base64.b64encode(json_str.encode()).decode()
    return str(v)


Base64PydanticModel = Annotated[
    T,
    BeforeValidator(_decode_b64_json),
    PlainSerializer(_encode_b64_json),
]
