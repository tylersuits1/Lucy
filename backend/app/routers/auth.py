"""POST /auth/login — exchange a username/password for a JWT.

No signup endpoint: this is a fixed, household-scale user list (Tyler +
wife, maybe kids later), created via `scripts/create_user.py` rather
than a public-facing form.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth import authenticate, create_access_token

router = APIRouter(prefix="/auth")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    user_id: int
    username: str
    display_name: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    user = authenticate(request.username, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(user)
    return LoginResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        display_name=user.display_name,
    )
