from datetime import datetime, timezone
from bson import ObjectId
from src.domain.audit.entity import AuditLogEntity
from src.domain.audit.repository import AuditLogRepository


class AuditService:
    def __init__(self, audit_repo: AuditLogRepository):
        self.audit_repo = audit_repo
    
    async def log_admin_action(
        self,
        action: str,
        admin_user_id: str,
        admin_user_email: str,
        target_user_id: str = None,
        target_user_email: str = None,
        details: dict = None
    ):
        """Log an admin action for audit purposes"""
        audit_log = AuditLogEntity(
            id=ObjectId(),
            action=action,
            admin_user_id=admin_user_id,
            admin_user_email=admin_user_email,
            target_user_id=target_user_id,
            target_user_email=target_user_email,
            details=details or {},
            created_at=datetime.now(timezone.utc)
        )
        return await self.audit_repo.create_audit_log(audit_log)

