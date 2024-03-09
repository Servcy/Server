from enum import Enum


class ERole(Enum):
    OWNER = 3
    ADMIN = 2
    MEMBER = 1
    GUEST = 0


class EAccess(Enum):
    PUBLIC = 0
    PRIVATE = 1
