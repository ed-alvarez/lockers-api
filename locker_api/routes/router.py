from fastapi import APIRouter

from .conditions.endpoint import router as conditions_router
from .developer.endpoint import router as developer_router
from .device.endpoint import router as device_router
from .event.endpoint import router as event_router
from .filters.endpoint import router as filters_router
from .financial.endpoint import router as financial_router
from .groups.endpoint import router as groups_router
from .harbor.endpoint import router as harbor_router
from .images.endpoint import router as images_router
from .issue.endpoint import router as issue_router
from .labels.endpoint import router as labels_router
from .location.endpoint import router as location_router
from .locker_wall.endpoint import router as locker_wall_router
from .login.endpoint import router as login_router
from .member.endpoint import router as member_router
from .memberships.endpoint import router as memberships_router
from .notifications.endpoint import router as notifications_router
from .organization.endpoint import router as organization_router
from .price.endpoint import router as price_router
from .product_groups.endpoint import router as product_groups_router
from .products.endpoint import router as products_router
from .promo.endpoint import router as promo_router
from .reports.endpoint import router as reports_router
from .reservations.endpoint import router as reservations_router
from .roles.endpoint import router as roles_router
from .settings.endpoint import router as settings_router
from .size.endpoint import router as size_router
from .types.endpoint import router as types_router
from .user.endpoint import router as user_router
from .verify.endpoint import router as qr_router
from .webhook.endpoint import router as webhook_router
from .white_label.endpoint import router as white_label_router
from .feedback.endpoint import router as feedback_router

central_router = APIRouter()

central_router.include_router(router=location_router)
central_router.include_router(router=device_router)
central_router.include_router(router=locker_wall_router)
central_router.include_router(router=size_router)
central_router.include_router(router=conditions_router)
central_router.include_router(router=products_router)
central_router.include_router(router=product_groups_router)
central_router.include_router(router=notifications_router)
central_router.include_router(router=price_router)
central_router.include_router(router=memberships_router)
central_router.include_router(router=promo_router)
central_router.include_router(router=reservations_router)
central_router.include_router(router=reports_router)
central_router.include_router(router=groups_router)
central_router.include_router(router=organization_router)
central_router.include_router(router=member_router)
central_router.include_router(router=financial_router)
central_router.include_router(router=login_router)
central_router.include_router(router=user_router)
central_router.include_router(router=event_router)
central_router.include_router(router=issue_router)
central_router.include_router(router=images_router)
central_router.include_router(router=white_label_router)
central_router.include_router(router=settings_router)
central_router.include_router(router=webhook_router)
central_router.include_router(router=developer_router)
central_router.include_router(router=types_router)
central_router.include_router(router=filters_router)
central_router.include_router(router=harbor_router)
central_router.include_router(router=qr_router)
central_router.include_router(router=roles_router)
central_router.include_router(router=labels_router)
central_router.include_router(router=feedback_router)
