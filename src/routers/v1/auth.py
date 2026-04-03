from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.schemas import TokenInfo, UserAuthData
from src.services import AuthService

auth_router = APIRouter(prefix="/token", tags=["auth"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]

@auth_router.post("/", response_model=TokenInfo)
async def authorize(user_data: UserAuthData, session: DBSession):
    token = await AuthService(session).encode_jwt(user_data)

    if token is None:  # ситуация, когда пользователя с указанными e_mail и password нет в системе
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    return TokenInfo(
        access_token=token,
        token_type="bearer"
    )


