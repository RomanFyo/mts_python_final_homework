from datetime import datetime, timedelta

import jwt
from sqlalchemy import select

from src.configurations.settings import settings
from src.models import Seller
from src.schemas import UserAuthData

__all__ = [
    "AuthService"
]

class AuthService:
    def __init__(self, session):
        self.session = session

    async def encode_jwt(
            self,
            user_data: UserAuthData,
            expire_minutes: int = settings.access_token_expire_minutes
    ) -> str | None:
        # проверка, что продавец с указанными e_mail и password действительно есть в БД
        seller = await self.session.scalar(select(Seller).where(
            (Seller.e_mail == user_data.e_mail) &
            (Seller.password == user_data.password)
        ))
        if seller is None:
            return None

        # генерация токена
        expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
        jwt_payload = {
            "sub": str(seller.id),
            "e_mail": user_data.e_mail,
            "exp": expire
        }
        encoded = jwt.encode(
            jwt_payload,
            settings.jwt_secret_key,
            algorithm="HS256"
        )
        return encoded

    def decode_jwt(self, token: str | bytes) -> dict:
        decoded = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"]
        )
        return decoded

    async def check_authorization(self, seller_id: int | None, token: str) -> bool:
        payload = self.decode_jwt(
            token=token
        )
        seller = await self.session.get(Seller, seller_id)
        if seller and payload.get("e_mail") == seller.e_mail:
            return True
        return False





