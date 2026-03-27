from pydantic import BaseModel

class TokenData(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginPayload(BaseModel):
    email: str
    password: str