from fastapi import Depends, HTTPException, status

from app.security.roles import RoleName


def normalize_role_name(role_value: str | None) -> str:
    if not role_value:
        return ""
    return role_value.strip().lower()


def require_roles(*allowed_roles: RoleName):
    """
    Dependency factory para proteger endpoints por rol.

    Uso:
        @router.get("/admin-only")
        def endpoint(current_user = Depends(require_roles(RoleName.ADMIN))):
            ...
    """
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


def require_any_academic_role():
    """
    Permite entrar a usuarios de tipo académico/operativo.
    """
    return require_roles(
        RoleName.ADMIN,
        RoleName.REGISTRO,
        RoleName.CONSULTA,
        RoleName.DIGITADOR,
    )


def require_admin_or_registro():
    return require_roles(RoleName.ADMIN, RoleName.REGISTRO)


def require_admin_only():
    return require_roles(RoleName.ADMIN)


def require_read_only_roles():
    return require_roles(RoleName.ADMIN, RoleName.REGISTRO, RoleName.CONSULTA)


def extract_user_role(current_user) -> str:
    """
    Intenta extraer el rol del usuario sin depender rígidamente
    de una sola forma del modelo.
    """
    # Caso 1: current_user.role es string
    role_attr = getattr(current_user, "role", None)
    if isinstance(role_attr, str):
        return normalize_role_name(role_attr)

    # Caso 2: current_user.role es objeto con .name
    if role_attr is not None:
        role_name = getattr(role_attr, "name", None)
        if isinstance(role_name, str):
            return normalize_role_name(role_name)

    # Caso 3: current_user.role_name
    role_name_attr = getattr(current_user, "role_name", None)
    if isinstance(role_name_attr, str):
        return normalize_role_name(role_name_attr)

    return ""


# Import tardío para evitar ciclos si tu get_current_active_user
# vive dentro de otro módulo de seguridad/auth.
from app.security.auth import get_current_active_user  # noqa: E402
