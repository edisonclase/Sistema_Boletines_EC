import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # 🔹 Identificación del centro
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    minerd_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    regional_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    regional_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    district_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    district_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # 🔹 Contacto
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 🔹 Identidad visual
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # 🔹 Autoridades
    principal_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    principal_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    principal_signature_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 🔹 Estado
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # 🔹 Fechas
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # 🔹 Relación con usuarios (no rompe nada aún)
    users = relationship("User", back_populates="institution")