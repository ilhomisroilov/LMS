"""Admin dashboard endpoint."""
from fastapi import APIRouter, Depends

from app.core.authz import AuthContext, require_permission
from app.core.deps import DbSession
from app.core.permissions import Perm
from app.schemas.payment import DashboardStats
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: DbSession, ctx: AuthContext = Depends(require_permission(Perm.ANALYTICS_READ))):
    stats = DashboardService(db).stats(ctx.organization_id)
    if not ctx.has(Perm.PAYMENT_READ):
        return stats.model_copy(update={"revenue_this_month": None, "debt_total": None})
    return stats
