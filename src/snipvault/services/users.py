from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from snipvault.errors import EmailAlreadyRegistered, InvalidCredentials
from snipvault.models import User
from snipvault.security import hash_password, verify_password

# Usado quando o e-mail não existe, para que o tempo de resposta não revele
# quais contas estão cadastradas.
_DUMMY_HASH = hash_password("senha-descartavel")


def register(db: Session, *, email: str, password: str) -> User:
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise EmailAlreadyRegistered()

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise EmailAlreadyRegistered() from None
    return user


def authenticate(db: Session, *, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    stored_hash = user.password_hash if user else _DUMMY_HASH
    password_ok = verify_password(password, stored_hash)
    if user is None or not password_ok:
        raise InvalidCredentials()
    return user
