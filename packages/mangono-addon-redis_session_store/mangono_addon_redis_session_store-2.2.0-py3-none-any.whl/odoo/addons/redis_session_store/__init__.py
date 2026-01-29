import logging
from environ_odoo_config import odoo_utils

_logger = logging.getLogger("odoo.session.REDIS")

try:
    import redis

    _logger.info("Lib redis installed")
except ImportError:
    redis = None


def _post_load_module():
    if not redis:
        raise ImportError("Please install package redis")
    import odoo.release

    if "redis_session_store" not in odoo_utils.get_server_wide_modules(odoo.release.serie):
        return
    from environ_odoo_config.environ import Environ
    from .env_config import RedisEnvConfig

    redis_config = RedisEnvConfig(Environ.new())
    server_info = redis_config.connect().info()
    # In case this is a Materia KV Redis compatible databaseOdooSessionClass
    if not server_info.get("redis_version") and server_info.get("Materia KV "):
        server_info = {"redis_version": f"Materia KV - {server_info['Materia KV ']}"}
    if not server_info:
        raise ValueError("Can't display server info")
    _logger.info("Redis Session enable [%s]", server_info.get("redis_version", "No version provided"))
    from . import odoo_monkey_patch

    odoo_monkey_patch.patch_odoo(redis_config)
