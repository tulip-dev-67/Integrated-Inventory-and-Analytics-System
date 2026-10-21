import hashlib
import os

MANAGER = "Manager"
JUNIOR_MANAGER = "Junior Manager"
VALID_ROLES = (MANAGER, JUNIOR_MANAGER)


class AuthenticationError(Exception):
    """Raised when login fails."""


class PermissionDenied(Exception):
    """Raised when a user's role does not allow an action."""


class User:
    """An authenticated user. Read-only, so a role can't be changed after login."""

    def __init__(self, username, role):
        self.__username = username
        self.__role = role

    @property
    def username(self):
        return self.__username

    @property
    def role(self):
        return self.__role


class UserManager:
    def __init__(self):
        # username -> (salt, password_hash, role); passwords are never stored in plain text
        self.__users = {}

    @staticmethod
    def _hash(password, salt):
        return hashlib.sha256(salt + password.encode("utf-8")).hexdigest()

    def create_user(self, username, password, role):
        if not username or not password:
            raise ValueError("Username and password cannot be empty.")
        if role not in VALID_ROLES:
            raise ValueError(f"Role must be one of {VALID_ROLES}.")
        if username in self.__users:
            raise ValueError(f"User '{username}' already exists.")
        salt = os.urandom(16)
        self.__users[username] = (salt, self._hash(password, salt), role)

    def authenticate(self, username, password):
        record = self.__users.get(username)
        if record is None:
            raise AuthenticationError("Invalid username or password.")
        salt, stored_hash, role = record
        if self._hash(password, salt) != stored_hash:
            raise AuthenticationError("Invalid username or password.")
        return User(username, role)