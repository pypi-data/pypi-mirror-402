from enum import StrEnum


class EnvType(StrEnum):
    local = "local"
    dev = "dev"
    staging = "staging"
    prod = "prod"