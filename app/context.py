import contextvars
from typing import Optional
from uuid import UUID

tenant_id_ctx: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar(
    "tenant_id", default=None
)
user_id_ctx: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar(
    "user_id", default=None
)
is_msp_admin_ctx: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "is_msp_admin", default=False
)
public_ctx: contextvars.ContextVar[bool] = contextvars.ContextVar("public", default=False)


def set_tenant(tenant_id: Optional[UUID]):
    tenant_id_ctx.set(tenant_id)


def set_user(user_id: Optional[UUID]):
    user_id_ctx.set(user_id)


def set_msp_admin(flag: bool):
    is_msp_admin_ctx.set(flag)


def set_public(flag: bool):
    public_ctx.set(flag)


def current_tenant() -> Optional[UUID]:
    return tenant_id_ctx.get()


def current_user() -> Optional[UUID]:
    return user_id_ctx.get()


def current_is_msp_admin() -> bool:
    return is_msp_admin_ctx.get()


def current_public() -> bool:
    return public_ctx.get()
