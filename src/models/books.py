from typing import List

from sqlalchemy import String, ForeignKey, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

__all__ = ["Book"]

# ORM
class Book(BaseModel):
    __tablename__ = "books_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    author: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(nullable=True)
    pages: Mapped[int]
    # todo: проверить, что данные изменения нормально работают

    seller_id: Mapped[int] = mapped_column(
        ForeignKey("sellers_table.id"),
        nullable=True
    )

    seller: Mapped["Seller"] = relationship(back_populates="books")


