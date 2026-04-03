from pydantic import BaseModel

from . import ReturnedSellersBook

__all__ = [
    "BaseSeller",
    "IncomingSeller",
    "ReturnedSellerWithBooks",
    "ReturnedSeller",
    "ReturnedSellerWithPassword",
    "ReturnedAllSellers",
]


class BaseSeller(BaseModel):
    first_name: str
    last_name: str
    e_mail: str


class IncomingSeller(BaseSeller):
    password: str


class ReturnedSellerWithBooks(BaseSeller):
    id: int
    books: list[ReturnedSellersBook]


class ReturnedSeller(BaseSeller):
    id: int


class ReturnedSellerWithPassword(ReturnedSeller):
    password: str


class ReturnedAllSellers(BaseModel):
    sellers: list[ReturnedSeller]

