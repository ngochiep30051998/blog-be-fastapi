from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class DomainEvent:
    """Base class for all domain events"""
    occurred_at: datetime
    aggregate_id: Any