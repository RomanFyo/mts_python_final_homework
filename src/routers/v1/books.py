from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.schemas import (IncomingBook, PatchBook, ReturnedAllBooks,
                         ReturnedBook, UpdateBook)
from src.services import AuthService, BookService, SellerService

books_router = APIRouter(prefix="/books", tags=["books"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]

http_bearer = HTTPBearer()

@books_router.get("/", response_model=ReturnedAllBooks)
async def get_all_books(session: DBSession):
    books = await BookService(session).get_all_books()
    return {"books": books}


@books_router.post("/", response_model=ReturnedBook, status_code=status.HTTP_201_CREATED)
async def create_book(
        book: IncomingBook,
        session: DBSession,
        credentials: HTTPAuthorizationCredentials = Depends(http_bearer)
):
    # получение информации о селлере (нельзя добавлять книгу с seller_id, которого нет в sellers_table)
    seller_info = await SellerService(session).get_single_seller(book.seller_id)
    if book.seller_id is not None and seller_info is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # проверка доступа по токену
    token = credentials.credentials
    if not await AuthService(session).check_authorization(book.seller_id, token):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    new_book = await BookService(session).add_book(book)

    return new_book


@books_router.get("/{book_id}", response_model=ReturnedBook)
async def get_single_book(book_id: int, session: DBSession):
    book = await BookService(session).get_single_book(book_id)

    if book is not None:
        return book

    return Response(status_code=status.HTTP_404_NOT_FOUND)


@books_router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, session: DBSession):

    deleted_book = await BookService(session).delete_book(book_id)

    if not deleted_book:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@books_router.put("/{book_id}", response_model=ReturnedBook)
async def update_book(
        book_id: int,
        new_book_data: UpdateBook,
        session: DBSession,
        credentials: HTTPAuthorizationCredentials = Depends(http_bearer)
):
    # проверка доступа по токену
    book = await BookService(session).get_single_book(book_id)
    token = credentials.credentials
    if not await AuthService(session).check_authorization(book.seller_id, token):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    # обновление данных о книге
    updated_book = await BookService(session).update_book(book_id, new_book_data)
    if not updated_book:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return updated_book


@books_router.patch("/{book_id}", response_model=ReturnedBook)
async def patch_book(book_id: int, patched_book: PatchBook, session: DBSession):
    book = await BookService(session).partial_update_book(book_id, patched_book)

    if not book:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return book
