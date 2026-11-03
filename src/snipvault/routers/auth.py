from fastapi import APIRouter, status

from snipvault import security
from snipvault.deps import AppSettings, CurrentUser, DbSession
from snipvault.schemas import LoginRequest, TokenOut, UserCreate, UserOut
from snipvault.services import users

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession):
    return users.register(db, email=payload.email, password=payload.password)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: DbSession, settings: AppSettings):
    user = users.authenticate(db, email=payload.email, password=payload.password)
    return TokenOut(access_token=security.create_access_token(user.id, settings))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user
