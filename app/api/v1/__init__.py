from fastapi import APIRouter

from api.v1 import occon25, root

router = APIRouter()
router.include_router(root.router, tags=["root"])
router.include_router(occon25.router, prefix="/occon25", tags=["OCCON 2025"])
