from datetime import datetime, timezone
from bson import ObjectId
from src.domain.audit.entity import AuditLogEntity
from src.domain.audit.repository import AuditLogRepository
from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoAuditLogRepository(AuditLogRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["audit_logs"]
    
    async def create_audit_log(self, audit_log: AuditLogEntity):
        data = {
            "_id": audit_log.id,
            "action": audit_log.action,
            "admin_user_id": audit_log.admin_user_id,
            "admin_user_email": audit_log.admin_user_email,
            "target_user_id": audit_log.target_user_id,
            "target_user_email": audit_log.target_user_email,
            "details": audit_log.details,
            "created_at": audit_log.created_at
        }
        await self.collection.insert_one(data)
        return data
    
    async def get_audit_logs_by_admin(self, admin_user_id: str, skip: int = 0, limit: int = 50):
        cursor = self.collection.find({"admin_user_id": admin_user_id}).sort("created_at", -1).skip(skip).limit(limit)
        logs = await cursor.to_list(length=limit)
        return logs
    
    async def get_audit_logs_by_target_user(self, target_user_id: str, skip: int = 0, limit: int = 50):
        cursor = self.collection.find({"target_user_id": target_user_id}).sort("created_at", -1).skip(skip).limit(limit)
        logs = await cursor.to_list(length=limit)
        return logs

