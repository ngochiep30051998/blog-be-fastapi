from abc import ABC, abstractmethod

class AuditLogRepository(ABC):
    @abstractmethod
    async def create_audit_log(self, audit_log_data):
        pass
    
    @abstractmethod
    async def get_audit_logs_by_admin(self, admin_user_id: str, skip: int = 0, limit: int = 50):
        pass
    
    @abstractmethod
    async def get_audit_logs_by_target_user(self, target_user_id: str, skip: int = 0, limit: int = 50):
        pass

