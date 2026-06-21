from fastapi import APIRouter
from ml.violations.catalog import VIOLATION_CATALOG, VIOLATION_PRIORITY

router = APIRouter(tags=["Violations Catalog"])


@router.get("/violations/catalog")
async def get_violation_catalog():
    return {
        "categories": VIOLATION_CATALOG,
        "priority_order": VIOLATION_PRIORITY,
        "total": len(VIOLATION_CATALOG),
    }
