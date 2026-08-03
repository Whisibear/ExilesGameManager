"""Mod management routes, split by concern: wishlist CRUD (wishlist.py),
general mod list/enable/disable/reorder (crud.py), Steam Workshop installation
(workshop.py), and manual verified-file installation (manual.py).

Routes are merged by extending `routes` directly rather than
`include_router()`, since crud.py's list endpoint is registered at path ""
(matching the original single-file router, mounted at /api/mods with no
trailing slash) - `include_router()` rejects merging a sub-router whose path
is "" when neither router has a prefix yet, even though the real prefix
("/api/mods") is added later in app/main.py."""

from fastapi import APIRouter

from app.routes.mods import crud, manual, nexus, wishlist, workshop

router = APIRouter()
for _sub_router in (wishlist.router, crud.router, nexus.router, workshop.router, manual.router):
    router.routes.extend(_sub_router.routes)
