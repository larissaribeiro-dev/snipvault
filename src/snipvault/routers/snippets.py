from fastapi import APIRouter, Response, status

from snipvault.deps import CurrentUser, DbSession, ListingParams, OptionalUser
from snipvault.schemas import Page, SnippetCreate, SnippetOut, SnippetUpdate
from snipvault.services import snippets

router = APIRouter(prefix="/snippets", tags=["snippets"])
public_router = APIRouter(prefix="/public/snippets", tags=["public"])


def _page(items, total: int, listing) -> Page[SnippetOut]:
    return Page[SnippetOut](
        items=[SnippetOut.model_validate(item) for item in items],
        total=total,
        limit=listing.limit,
        offset=listing.offset,
    )


@router.post("", response_model=SnippetOut, status_code=status.HTTP_201_CREATED)
def create_snippet(payload: SnippetCreate, db: DbSession, user: CurrentUser):
    return snippets.create_snippet(db, owner=user, data=payload)


@router.get("", response_model=Page[SnippetOut])
def list_my_snippets(db: DbSession, user: CurrentUser, listing: ListingParams):
    items, total = snippets.list_snippets(
        db, owner_id=user.id, filters=listing.filters, limit=listing.limit, offset=listing.offset
    )
    return _page(items, total, listing)


@router.get("/{snippet_id}", response_model=SnippetOut)
def get_snippet(snippet_id: int, db: DbSession, viewer: OptionalUser):
    return snippets.get_visible_snippet(db, snippet_id, viewer)


@router.patch("/{snippet_id}", response_model=SnippetOut)
def update_snippet(snippet_id: int, payload: SnippetUpdate, db: DbSession, user: CurrentUser):
    snippet = snippets.get_owned_snippet(db, snippet_id, user)
    return snippets.update_snippet(db, snippet, payload)


@router.delete("/{snippet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snippet(snippet_id: int, db: DbSession, user: CurrentUser):
    snippet = snippets.get_owned_snippet(db, snippet_id, user)
    snippets.delete_snippet(db, snippet)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@public_router.get("", response_model=Page[SnippetOut])
def list_public_snippets(db: DbSession, listing: ListingParams):
    items, total = snippets.list_snippets(
        db, only_public=True, filters=listing.filters, limit=listing.limit, offset=listing.offset
    )
    return _page(items, total, listing)
