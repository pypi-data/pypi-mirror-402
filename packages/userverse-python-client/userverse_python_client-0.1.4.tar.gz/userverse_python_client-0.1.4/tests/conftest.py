from __future__ import annotations

import sys
from dataclasses import dataclass
from types import ModuleType
from typing import Any


@dataclass
class _DetailModel:
    message: str
    error: str | None = None


@dataclass
class _AppErrorResponseModel:
    detail: _DetailModel


class _GenericResponseModel:
    def __class_getitem__(cls, _item: Any) -> type["_GenericResponseModel"]:
        return cls

    @classmethod
    def model_validate(cls, payload: Any) -> Any:
        return payload


@dataclass
class _UserLoginModel:
    email: str
    password: str


@dataclass
class _UserCreateModel:
    email: str
    password: str
    name: str | None = None


@dataclass
class _UserUpdateModel:
    name: str | None = None


@dataclass
class _UserReadModel:
    id: str | None = None
    email: str | None = None


@dataclass
class _TokenResponseModel:
    token: str | None = None


@dataclass
class _UserQueryParams:
    limit: int | None = None


def _ensure_module(name: str) -> ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = ModuleType(name)
        module.__path__ = []
        sys.modules[name] = module
    return module


# Provide minimal stubs for external dependencies used by the client.
_ensure_module("sverse_generic_models")
app_error_module = _ensure_module("sverse_generic_models.app_error")
generic_response_module = _ensure_module("sverse_generic_models.generic_response")
app_error_module.AppErrorResponseModel = _AppErrorResponseModel
app_error_module.DetailModel = _DetailModel
generic_response_module.GenericResponseModel = _GenericResponseModel

_ensure_module("userverse_models")
user_module = _ensure_module("userverse_models.user")
user_user_module = _ensure_module("userverse_models.user.user")
user_user_module.UserLoginModel = _UserLoginModel
user_user_module.UserUpdateModel = _UserUpdateModel
user_user_module.UserCreateModel = _UserCreateModel
user_user_module.UserReadModel = _UserReadModel
user_user_module.TokenResponseModel = _TokenResponseModel
user_user_module.UserQueryParams = _UserQueryParams
user_module.user = user_user_module
