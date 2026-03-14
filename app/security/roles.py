from enum import Enum


class RoleName(str, Enum):
    ADMIN = "admin"
    REGISTRO = "registro"
    CONSULTA = "consulta"
    DIGITADOR = "digitador"

