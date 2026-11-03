from dataclasses import dataclass

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from snipvault.errors import PermissionDenied, SnippetNotFound
from snipvault.models import Snippet, Tag, User, utcnow
from snipvault.schemas import SnippetCreate, SnippetUpdate


@dataclass(frozen=True)
class SnippetFilters:
    q: str | None = None
    language: str | None = None
    tag: str | None = None


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _apply_filters(stmt: Select, filters: SnippetFilters) -> Select:
    if filters.q:
        pattern = f"%{_escape_like(filters.q)}%"
        stmt = stmt.where(
            or_(
                Snippet.title.ilike(pattern, escape="\\"),
                Snippet.description.ilike(pattern, escape="\\"),
                Snippet.code.ilike(pattern, escape="\\"),
            )
        )
    if filters.language:
        stmt = stmt.where(Snippet.language == filters.language.lower())
    if filters.tag:
        stmt = stmt.where(Snippet.tags.any(Tag.name == filters.tag.lower()))
    return stmt


def _resolve_tags(db: Session, names: list[str]) -> list[Tag]:
    if not names:
        return []
    existing = {tag.name: tag for tag in db.scalars(select(Tag).where(Tag.name.in_(names)))}
    tags = []
    for name in names:
        tag = existing.get(name)
        if tag is None:
            tag = Tag(name=name)
            db.add(tag)
        tags.append(tag)
    return tags


def create_snippet(db: Session, *, owner: User, data: SnippetCreate) -> Snippet:
    snippet = Snippet(
        title=data.title,
        description=data.description,
        language=data.language,
        code=data.code,
        is_public=data.is_public,
        owner_id=owner.id,
        tags=_resolve_tags(db, data.tags),
    )
    db.add(snippet)
    db.commit()
    return snippet


def list_snippets(
    db: Session,
    *,
    owner_id: int | None = None,
    only_public: bool = False,
    filters: SnippetFilters,
    limit: int,
    offset: int,
) -> tuple[list[Snippet], int]:
    stmt = select(Snippet)
    if owner_id is not None:
        stmt = stmt.where(Snippet.owner_id == owner_id)
    if only_public:
        stmt = stmt.where(Snippet.is_public.is_(True))
    stmt = _apply_filters(stmt, filters)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    ordered = stmt.order_by(Snippet.created_at.desc(), Snippet.id.desc())
    items = list(db.scalars(ordered.limit(limit).offset(offset)))
    return items, total


def get_visible_snippet(db: Session, snippet_id: int, viewer: User | None) -> Snippet:
    """Snippets privados de outras pessoas respondem como se não existissem."""
    snippet = db.get(Snippet, snippet_id)
    is_owner = viewer is not None and snippet is not None and snippet.owner_id == viewer.id
    if snippet is None or not (snippet.is_public or is_owner):
        raise SnippetNotFound()
    return snippet


def get_owned_snippet(db: Session, snippet_id: int, user: User) -> Snippet:
    snippet = get_visible_snippet(db, snippet_id, user)
    if snippet.owner_id != user.id:
        raise PermissionDenied()
    return snippet


def update_snippet(db: Session, snippet: Snippet, data: SnippetUpdate) -> Snippet:
    changes = data.model_dump(exclude_unset=True)
    if "tags" in changes:
        snippet.tags = _resolve_tags(db, changes.pop("tags"))
    for field, value in changes.items():
        setattr(snippet, field, value)
    snippet.updated_at = utcnow()
    db.commit()
    return snippet


def delete_snippet(db: Session, snippet: Snippet) -> None:
    db.delete(snippet)
    db.commit()
