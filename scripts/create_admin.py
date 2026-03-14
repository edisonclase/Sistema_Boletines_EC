from getpass import getpass
from uuid import uuid4

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.database import SessionLocal
from app.models.role import Role
from app.models.user import User


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def normalize_document_id(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def prompt_text(label: str, *, normalize_digits: bool = False) -> str | None:
    value = input(f"{label}: ").strip()

    if value.lower() in {"salir", "exit", "cancelar"}:
        return None

    if not value:
        print("Este campo es obligatorio.")
        return ""

    if normalize_digits:
        normalized = normalize_document_id(value)
        if not normalized:
            print("Debe ingresar una cédula válida.")
            return ""
        return normalized

    return value


def prompt_password() -> str | None:
    password = getpass("Contraseña: ").strip()
    if password.lower() in {"salir", "exit", "cancelar"}:
        return None

    if len(password) < settings.security_password_min_length:
        print(
            f"La contraseña debe tener al menos "
            f"{settings.security_password_min_length} caracteres."
        )
        return ""

    confirm = getpass("Confirmar contraseña: ").strip()
    if confirm.lower() in {"salir", "exit", "cancelar"}:
        return None

    if password != confirm:
        print("Las contraseñas no coinciden.")
        return ""

    return password


def print_header() -> None:
    print("\n" + "=" * 50)
    print("Registro de usuario al sistema")
    print("=" * 50)
    print("Escriba 'salir' en cualquier campo para cancelar.\n")


def create_admin() -> None:
    db: Session = SessionLocal()

    try:
        print_header()

        role = db.query(Role).filter(Role.name == "admin").first()

        if not role:
            print("No existe el rol admin.")
            return

        while True:
            document_id = prompt_text(
                "Ingrese la cédula de identidad del usuario",
                normalize_digits=True,
            )
            if document_id is None:
                print("Operación cancelada por el usuario.")
                return
            if not document_id:
                continue

            existing_by_document = (
                db.query(User).filter(User.document_id == document_id).first()
            )
            if existing_by_document:
                print("Ya existe un usuario registrado con esa cédula.")
                continue
            break

        while True:
            full_name = prompt_text("Nombre completo")
            if full_name is None:
                print("Operación cancelada por el usuario.")
                return
            if full_name:
                break

        while True:
            email = prompt_text("Correo electrónico")
            if email is None:
                print("Operación cancelada por el usuario.")
                return
            if not email:
                continue

            existing_by_email = db.query(User).filter(User.email == email).first()
            if existing_by_email:
                print("Ya existe un usuario registrado con ese correo electrónico.")
                continue
            break

        while True:
            password = prompt_password()
            if password is None:
                print("Operación cancelada por el usuario.")
                return
            if password:
                break

        hashed = hash_password(password)

        user = User(
            id=uuid4(),
            document_id=document_id,
            full_name=full_name,
            email=email,
            password_hash=hashed,
            role_id=role.id,
            is_active=True,
            failed_login_attempts=0,
        )

        db.add(user)
        db.commit()

        print("\nUsuario administrador creado correctamente.")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()