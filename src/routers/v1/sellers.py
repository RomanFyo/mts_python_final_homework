from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.schemas import (BaseSeller, IncomingSeller, ReturnedAllSellers,
                         ReturnedSellerWithBooks, ReturnedSellerWithPassword)
from src.services import AuthService, SellerService

sellers_router = APIRouter(prefix="/sellers", tags=["sellers"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]

http_bearer = HTTPBearer()

@sellers_router.get("/", response_model=ReturnedAllSellers)
async def get_all_sellers(session: DBSession):
    sellers = await SellerService(session).get_all_sellers()
    return {"sellers": sellers}

@sellers_router.get("/{seller_id}", response_model=ReturnedSellerWithBooks)
async def get_single_seller(
        seller_id: int,
        session: DBSession,
        credentials: HTTPAuthorizationCredentials = Depends(http_bearer)
):
    seller_info = await SellerService(session).get_single_seller(seller_id)

    # проверка, что селлер с указанным id действительно есть
    if seller_info is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # проверка доступа по токену
    token = credentials.credentials
    if not await AuthService(session).check_authorization(seller_id, token):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    return {
        **seller_info[0].__dict__,
        "books": seller_info[1]
    }

@sellers_router.post("/", response_model=ReturnedSellerWithPassword, status_code=status.HTTP_201_CREATED)
async def create_seller(seller: IncomingSeller, session: DBSession):
    new_seller = await SellerService(session).add_seller(seller)

    return new_seller

@sellers_router.put("/{seller_id}", response_model=ReturnedSellerWithPassword)
async def update_seller(seller_id: int, new_seller_data: BaseSeller, session: DBSession):
    updated_seller = await SellerService(session).update_seller(seller_id, new_seller_data)

    if updated_seller is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return updated_seller

@sellers_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(seller_id: int, session: DBSession):
    is_seller_deleted = await SellerService(session).delete_seller(seller_id)

    if not is_seller_deleted:
        return Response(status_code=status.HTTP_404_NOT_FOUND)