from fastapi import Depends, HTTPException, status

from app.security.roles import RoleName


def normalize_role_name(role_value: str | None) -> str:
    if not role_value:
        return ""
    return role_value.strip().lower()


def extract_user_role(current_user) -> str:
    role_attr = getattr(current_user, "role", None)

    if isinstance(role_attr, str):
        return normalize_role_name(role_attr)

    if role_attr is not None:
        role_name = getattr(role_attr, "name", None)
        if isinstance(role_name, str):
            return normalize_role_name(role_name)

    role_name_attr = getattr(current_user, "role_name", None)
    if isinstance(role_name_attr, str):
        return normalize_role_name(role_name_attr)

    return ""


def require_roles(*allowed_roles: RoleName):
    allowed = {role.value for role in allowed_roles}

    def dependency(current_user=Depends(get_current_active_user)):
        user_role = extract_user_role(current_user)

        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción.",
            )

        return current_user

    return dependency


def require_admin_only():
    return require_roles(RoleName.ADMIN)


def require_admin_or_registro():
    return require_roles(RoleName.ADMIN, RoleName.REGISTRO)


def require_read_only_roles():
    return require_roles(RoleName.ADMIN, RoleName.REGISTRO, RoleName.CONSULTA)


def require_all_operational_roles():
    return require_roles(
        RoleName.ADMIN,
        RoleName.REGISTRO,
        RoleName.CONSULTA,
        RoleName.DIGITADOR,
    )


# Import al final para evitar ciclos
from app.security.auth_service import get_current_active_user  # noqa: E402
