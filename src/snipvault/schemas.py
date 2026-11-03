import re
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
TAG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9+#._-]{0,29}$")
MAX_TAGS = 10

T = TypeVar("T")


def normalize_tags(values: list[str]) -> list[str]:
    unique: dict[str, None] = {}
    for raw in values:
        tag = raw.strip().lower()
        if not TAG_PATTERN.fullmatch(tag):
            raise ValueError(f"tag inválida: {raw!r}")
        unique.setdefault(tag)
    if len(unique) > MAX_TAGS:
        raise ValueError(f"máximo de {MAX_TAGS} tags por snippet")
    return list(unique)


class UserCreate(BaseModel):
    email: str = Field(max_length=255, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class _SnippetFields(BaseModel):
    @field_validator("title", "language", mode="before", check_fields=False)
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("language", check_fields=False)
    @classmethod
    def lowercase_language(cls, value):
        return value.lower() if value is not None else value

    @field_validator("tags", check_fields=False)
    @classmethod
    def clean_tags(cls, value):
        return normalize_tags(value) if value is not None else value


class SnippetCreate(_SnippetFields):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    language: str = Field(min_length=1, max_length=30)
    code: str = Field(min_length=1, max_length=50_000)
    is_public: bool = False
    tags: list[str] = Field(default_factory=list)


class SnippetUpdate(_SnippetFields):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    language: str | None = Field(default=None, min_length=1, max_length=30)
    code: str | None = Field(default=None, min_length=1, max_length=50_000)
    is_public: bool | None = None
    tags: list[str] | None = None

    @field_validator("title", "language", "code", "is_public", "tags")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("não pode ser nulo")
        return value


class SnippetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    language: str
    code: str
    is_public: bool
    tags: list[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def tag_names(cls, value):
        return sorted(getattr(tag, "name", tag) for tag in value)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
