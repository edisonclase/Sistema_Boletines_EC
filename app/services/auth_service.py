from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.auth import AuthUserResponse
from app.security.jwt import create_access_token
from app.security.password import verify_password


def normalize_email(value: str) -> str:
    return value.strip().lower()


def build_auth_user_response(user: User) -> AuthUserResponse:
    role_name = user.role.name if user.role else ""

    return AuthUserResponse(
        id=str(user.id),
        document_id=user.document_id,
        full_name=user.full_name,
        email=user.email,
        role=role_name,
    )


def _write_auth_audit_log(
    db: Session,
    *,
    event_type: str,
    user: User | None = None,
    details: str | None = None,
) -> None:
    audit = AuditLog(
        user_id=user.id if user else None,
        user_name=user.full_name if user else None,
        role_name=user.role.name if user and user.role else None,
        event_type=event_type,
        details=details,
    )
    db.add(audit)


def authenticate_user(db: Session, email: str, password: str) -> dict:
    normalized_email = normalize_email(email)
    now = datetime.now(timezone.utc)

    user = (
        db.query(User)
        .filter(func.lower(User.email) == normalized_email)
        .first()
    )

    if not user:
        _write_auth_audit_log(
            db,
            event_type="login_failed",
            details=f"Intento fallido para correo no registrado: {normalized_email}",
        )
        db.commit()
        return {
            "ok": False,
            "status_code": 401,
            "message": "Credenciales inválidas.",
        }

    if not user.is_active:
        _write_auth_audit_log(
            db,
            event_type="login_inactive",
            user=user,
            details="Intento de acceso con cuenta inactiva.",
        )
        db.commit()
        return {
            "ok": False,
            "status_code": 403,
            "message": "La cuenta está inactiva. Contacte al administrador.",
        }

    if user.locked_until and user.locked_until > now:
        _write_auth_audit_log(
            db,
            event_type="login_blocked",
            user=user,
            details="Intento de acceso con cuenta temporalmente bloqueada.",
        )
        db.commit()
        return {
            "ok": False,
            "status_code": 423,
            "message": "La cuenta está temporalmente bloqueada. Intente más tarde.",
        }

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= settings.security_max_login_attempts:
            user.locked_until = now + timedelta(
                minutes=settings.security_account_lockout_minutes
            )
            _write_auth_audit_log(
                db,
                event_type="account_locked",
                user=user,
                details=(
                    "Cuenta bloqueada por superar el máximo de intentos fallidos "
                    f"({settings.security_max_login_attempts})."
                ),
            )
            db.commit()
            return {
                "ok": False,
                "status_code": 423,
                "message": "La cuenta fue bloqueada temporalmente por intentos fallidos.",
            }

        _write_auth_audit_log(
            db,
            event_type="login_failed",
            user=user,
            details=(
                "Contraseña inválida. "
                f"Intentos fallidos actuales: {user.failed_login_attempts}."
            ),
        )
        db.commit()
        return {
            "ok": False,
            "status_code": 401,
            "message": "Credenciales inválidas.",
        }

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now

    role_name = user.role.name if user.role else ""

    access_token = create_access_token(
        {
            "sub": normalized_email,
            "uid": str(user.id),
            "role": role_name,
            "full_name": user.full_name,
        }
    )

    _write_auth_audit_log(
        db,
        event_type="login_success",
        user=user,
        details="Inicio de sesión exitoso.",
    )

    db.commit()
    db.refresh(user)

    return {
        "ok": True,
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": build_auth_user_response(user),
        },
    }
