from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any

class BaseAuditLogger(ABC):
    @abstractmethod
    def log(self, *, who, action, resource_id=None, resource_name=None,
              resource_type=None, timestamp=None, location=None,
              request_context=None, context=None, client=None, tenant_id=None):
        """Audit an action with full context"""
        pass

