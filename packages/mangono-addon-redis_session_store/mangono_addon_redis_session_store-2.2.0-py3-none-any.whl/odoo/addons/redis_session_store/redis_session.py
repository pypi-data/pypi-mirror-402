from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
import warnings
from hashlib import sha512

import odoo
from odoo import http
from odoo.service import security

from . import json_encoding
from .env_config import RedisEnvConfig

# The amount of bytes of the session that will remain static and can be used
# for calculating the csrf token and be stored inside the database.
STORED_SESSION_BYTES = 42
# After a session is rotated, the session should be kept for a couple of
# seconds to account for network delay between multiple requests which are
# made at the same time and all use the same old cookie.
SESSION_DELETION_TIMER = 120
MAJOR = odoo.release.version_info[0]
try:
    with warnings.catch_warnings(record=True):
        import werkzeug.contrib.sessions as sessions
except ImportError:
    from odoo.tools._vendor import sessions


_logger = logging.getLogger("odoo.session.REDIS")


# this is equal to the duration of the session garbage collector in
# odoo.http.session_gc()


_logger = logging.getLogger(__name__)
_base64_urlsafe_re = re.compile(r"^[A-Za-z0-9_-]{84}$")
_session_identifier_re = re.compile(r"^[A-Za-z0-9_-]{%s}$" % STORED_SESSION_BYTES)  # noqa


class RedisSessionStore(sessions.SessionStore):
    """SessionStore that saves session to redis"""

    def __init__(
        self,
        redis_config: RedisEnvConfig,
        session_class,
    ):
        super().__init__(session_class=session_class)
        self.redis = redis_config.connect()
        self.expiration = redis_config.expiration
        self.anon_expiration = redis_config.anon_expiration
        self.timeout_on_inactivity = redis_config.timeout_on_inactivity
        self.ignored_urls = redis_config.ignored_urls
        self.support_expire = b"expire" in self.redis.command_list()
        self.prefix = "session:"
        if redis_config.prefix:
            self.prefix = f"{self.prefix}:{redis_config.prefix}:"

    def build_key(self, sid):
        return f"{self.prefix}{sid}"

    def is_valid_key(self, key):
        return _base64_urlsafe_re.match(key) is not None

    def get_expiration(self, session):
        # session.expiration allow to set a custom expiration for a session
        # such as a very short one for monitoring requests
        if not self.support_expire:
            return -1
        session_expiration = getattr(session, "expiration", 0)
        expiration = session_expiration or self.anon_expiration
        if session.uid:
            expiration = session_expiration or self.expiration
        return expiration

    def update_expiration(self, session):
        if not self.support_expire or not self.timeout_on_inactivity:
            return
        path = http.request.httprequest.path
        if any(path.startswith(url) for url in self.ignored_urls):
            return
        key = self.build_key(session.sid)
        expiration = self.get_expiration(session)

        return self.redis.expire(key, expiration)

    def save(self, session):
        key = self.build_key(session.sid)
        expiration = self.get_expiration(session)
        if _logger.isEnabledFor(logging.DEBUG):
            if session.uid:
                user_msg = f"user '{session.login}' (id: {session.uid})"
            else:
                user_msg = "anonymous user"
            _logger.debug(
                "saving session with key '%s' and expiration of %s seconds for %s",
                key,
                expiration,
                user_msg,
            )

        data = json.dumps(dict(session), cls=json_encoding.SessionEncoder).encode("utf-8")
        result = self.redis.set(key, data)
        if result and self.support_expire:
            return self.redis.expire(key, expiration)
        return -1

    def delete(self, session):
        key = self.build_key(session.sid)
        _logger.debug("deleting session with key %s", key)
        return self.redis.delete(key)

    def delete_old_sessions(self, session):
        pass

    def get(self, sid):
        if not self.is_valid_key(sid):
            _logger.debug(
                "session with invalid sid '%s' has been asked, returning a new one",
                sid,
            )
            return self.new()

        key = self.build_key(sid)
        saved = self.redis.get(key)
        if not saved:
            _logger.debug(
                "session with non-existent key '%s' has been asked, returning a new one",
                key,
            )
            return self.new()
        try:
            data = json.loads(saved.decode("utf-8"), cls=json_encoding.SessionDecoder)
        except ValueError:
            _logger.debug(
                "session for key '%s' has been asked but its json content could not be read, it has been reset",
                key,
            )
            data = {}
        return self.session_class(data, sid, False)

    def list(self):
        keys = self.redis.keys(f"{self.prefix}*")
        _logger.debug("a listing redis keys has been called")
        return [key[len(self.prefix) :] for key in keys]

    def rotate(self, session, env, soft=False):
        if soft:
            # Multiple network requests can occur at the same time, all using the old session.
            # We don't want to create a new session for each request, it's better to reference the one already made.
            static = session.sid[:STORED_SESSION_BYTES]
            recent_session = self.get(session.sid)
            if "next_sid" in recent_session:
                # A new session has already been saved on disk by a concurrent request,
                # the _save_session is going to simply use session.sid to set a new cookie.
                session.sid = recent_session["next_sid"]
                return
            next_sid = static + self.generate_key()[STORED_SESSION_BYTES:]
            session["next_sid"] = next_sid
            session["deletion_time"] = time.time() + SESSION_DELETION_TIMER
            self.save(session)
            # Now prepare the new session
            session["gc_previous_sessions"] = True
            session.sid = next_sid
            del session["deletion_time"]
            del session["next_sid"]
        else:
            self.delete(session)
            session.sid = self.generate_key()
        if session.uid:
            assert env, "saving this session requires an environment"
            session.session_token = security.compute_session_token(session, env)
        session.should_rotate = False
        session["create_time"] = time.time()
        self.save(session)

    def vacuum(self, *args, **kwargs):
        """
        Vacuum all expired keys.
        """
        # For MateriaKV, there is currently no active expiration. But `DBSIZE` seems to trigger the database gc.
        # https://www.clever.cloud/developers/doc/addons/materia-kv/
        # Useless for pure Redis config since there is an active expiration process. See :
        # https://redis.io/docs/latest/commands/expire/#how-redis-expires-keys
        self.redis.dbsize()
        _logger.debug("retrieving dbsize to trigger keys vacuum")
        return True

    def get_missing_session_identifiers(self, identifiers: list[str]) -> list[str]:
        """
        :param identifiers: session identifiers whose file existence must be checked
                            identifiers are a part session sid (first 42 chars)
        :type identifiers: iterable
        :return: the identifiers which are not present on the filesystem
        :rtype: set
        """
        existing_keys = set()
        for key in identifiers:
            if self.redis.exists(self.build_key(key)):
                existing_keys.add(key)
        # Remove the identifiers for which a key is present on the session store.
        missing_keys = set(identifiers) - existing_keys
        return list(missing_keys)

    def delete_from_identifiers(self, identifiers: list[str]):
        for identifier in identifiers:
            # Avoid to remove a session if it does not match an identifier.
            # This prevents malicious user to delete sessions from a different
            # database by specifying a custom ``res.device.log``.
            if not _session_identifier_re.match(identifier):
                raise ValueError(
                    f"Identifier format incorrect, did you pass in a string instead of a list? {identifier}"
                )
            redis_key = self.build_key(identifier)
            self.redis.delete(redis_key)

    def generate_key(self, salt=None):
        # The generated key is case sensitive (base64) and the length is 84 chars.
        # In the worst-case scenario, i.e. in an insensitive filesystem (NTFS for example)
        # taking into account the proportion of characters in the pool and a length
        # of 42 (stored part in the database), the entropy for the base64 generated key
        # is 217.875 bits which is better than the 160 bits entropy of a hexadecimal key
        # with a length of 40 (method ``generate_key`` of ``SessionStore``).
        # The risk of collision is negligible in practice.
        # Formulas:
        #   - L: length of generated word
        #   - p_char: probability of obtaining the character in the pool
        #   - n: size of the pool
        #   - k: number of generated word
        #   Entropy = - L * sum(p_char * log2(p_char))
        #   Collision ~= (1 - exp((-k * (k - 1)) / (2 * (n**L))))
        key = str(time.time()).encode() + os.urandom(64)
        hash_key = sha512(key).digest()[:-1]  # prevent base64 padding
        return base64.urlsafe_b64encode(hash_key).decode("utf-8")
