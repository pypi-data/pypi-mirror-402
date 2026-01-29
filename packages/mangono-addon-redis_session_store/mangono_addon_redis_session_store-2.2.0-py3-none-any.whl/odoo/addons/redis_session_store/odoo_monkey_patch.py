from __future__ import annotations

import logging
import random
from typing import Any

import wrapt

import odoo
from odoo import http as odoo_http
from odoo.http import request
from odoo.tools import func as odoo_func

from .env_config import RedisEnvConfig
from .redis_session import RedisSessionStore

_logger = logging.getLogger("odoo.session.REDIS")


def _get_session_class(major_odoo_version: int):
    if major_odoo_version < 16:
        return odoo_http.OpenERPSession
    return odoo_http.Session


def _reset_cached_properties(major_odoo_version: int, obj: Any):
    if major_odoo_version >= 19:
        odoo_func.reset_cached_properties(obj)
    else:
        odoo_func.lazy_property.reset_all(obj)


def session_gc(session_store):
    # session_gc is called at setup_session so we keep the randomness bit to only vacuum once in a while.
    if random.random() < 0.001:
        session_store.vacuum()


def _update_expiration():
    if (
        hasattr(odoo_http.root.session_store, "update_expiration")
        and request
        and request.session
        and request.session.uid
        and not request.env["res.users"].browse(request.session.uid)._is_public()
    ):
        odoo_http.root.session_store.update_expiration(request.session)


def patch_odoo(redis_config: RedisEnvConfig):
    _patch_odoo_http_root(redis_config)
    _patch_odoo_authenticate(redis_config)


def _patch_odoo_http_root(redis_config: RedisEnvConfig):
    _reset_cached_properties(redis_config.for_version.value, odoo.http.root)
    type(odoo_http.root).session_store = RedisSessionStore(
        redis_config, session_class=_get_session_class(redis_config.for_version.value)
    )
    # Keep compatibility with odoo env config.
    # There is no more session_gc global function, so no more patch needed.
    # Now see FilesystemSessionStore#vacuum.
    if not redis_config.disable_gc:
        odoo_http.session_gc = session_gc


def _patch_odoo_authenticate(redis_config: RedisEnvConfig):
    @wrapt.patch_function_wrapper(
        "odoo.addons.base",
        "models.ir_http.IrHttp._authenticate",
    )
    def _patch_IrHttp__authenticate(wrapped, instance, args, kwargs):
        _update_expiration()
        return wrapped(*args, **kwargs)
