from typing import Any

from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string
from pydantic import TypeAdapter
from pydantic import ValidationError as PydanticValidationError


class PydanticDjangoValidator:
    def __init__(self, dotted_path_to_type: str):
        self._dotted_path_to_type = dotted_path_to_type
        self._adapter = TypeAdapter(import_string(dotted_path_to_type))

    def __call__(self, value: Any):
        try:
            self._adapter.validate_python(value)
        except PydanticValidationError as e:
            raise ValidationError([error["msg"] for error in e.errors()]) from e

    def deconstruct(self):
        return (
            f"{self.__class__.__module__}.{self.__class__.__qualname__}",
            (),
            dict(dotted_path_to_type=self._dotted_path_to_type),
        )

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._dotted_path_to_type == other._dotted_path_to_type
