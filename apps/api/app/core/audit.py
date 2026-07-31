"""Writes to the append-only audit_logs table. Callers add the entry to the same
db-session/transaction as their main action instead of committing separately, so the
audit entry and the action it describes either both land or both roll back together."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


def record(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            log_metadata=metadata or {},
            ip_address=ip_address,
        )
    )
