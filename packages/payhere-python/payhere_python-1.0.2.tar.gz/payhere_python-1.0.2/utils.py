# payhere-python/utils.py
from typing import Type, TypeVar
import logging
from pydantic import BaseModel, ValidationError
from .exceptions import PayHereError


__logger__ = logging.getLogger("payhere")


T = TypeVar("T", bound=BaseModel)


def _try_pydantic_parse(model: Type[T], data: dict) -> T:
    try:
        return model(**data)
    except ValidationError as e:
        __logger__.error(f"Pydantic parsing error: {str(e)}")
        raise PayHereError(f"Pydantic parsing error: {str(e)}")