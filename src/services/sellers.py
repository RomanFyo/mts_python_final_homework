from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Book, Seller
from src.schemas import BaseSeller, IncomingSeller

__all__ = ["SellerService"]


class SellerService:
    def __init__(self, session: AsyncSession) -> tuple[Seller, list[Book]] | None:
        self.session = session

    async def get_single_seller(self, seller_id: int) -> tuple[Seller, list[Book]] | None:
        seller = await self.session.get(Seller, seller_id)
        if seller is None:
            return None

        query_res = await self.session.execute(select(Book).where(Book.seller_id == seller.id))
        books = query_res.scalars().all()

        return (seller, books)


    async def get_all_sellers(self) -> list[Seller] | None:
        query = select(Seller)
        result = await self.session.execute(query)

        return result.scalars().all()

    async def add_seller(self, seller: IncomingSeller) -> Seller:
        new_seller = Seller(
            **{
                "first_name": seller.first_name,
                "last_name": seller.last_name,
                "e_mail": seller.e_mail,
                "password": seller.password
            }
        )

        self.session.add(new_seller)
        await self.session.flush()

        return new_seller

    async def delete_seller(self, seller_id: int) -> bool:
        seller = await self.session.get(Seller, seller_id)

        if seller:
            # удаление книг, связанных с селлером
            query = delete(Book).where(Book.seller_id == seller.id)
            await self.session.execute(query)

            # удаление самого селлера
            await self.session.delete(seller)

            return True

        return False

    async def update_seller(self, seller_id, new_seller_data: BaseSeller) -> Seller | None:
        if updated_seller := await self.session.get(Seller, seller_id):
            updated_seller.first_name = new_seller_data.first_name
            updated_seller.last_name = new_seller_data.last_name
            updated_seller.e_mail = new_seller_data.e_mail

            await self.session.flush()

            return updated_seller