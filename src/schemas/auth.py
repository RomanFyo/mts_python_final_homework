from pydantic import BaseModel

__all__ = [
    "UserAuthData",
    "TokenInfo"
]

class UserAuthData(BaseModel):
    e_mail: str
    password: str

class TokenInfo(BaseModel):
    access_token: str
    token_type: str