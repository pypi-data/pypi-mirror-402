import json
import logging
from datetime import datetime
from typing import Optional

from .base import BaseAuditLogger
import os

logger = logging.getLogger(__name__)


class FileAuditLogger(BaseAuditLogger):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def log(
        self,
        who: Optional[str],
        action: str,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        resource_type: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        location: Optional[str] = "local",
        request_context: Optional[dict] = None,
        context: Optional[dict] = None,
        client: Optional[dict] = None,
        tenant_id: Optional[str] = None,
        deployment_id: Optional[str] = None
    ):
        entry = {
            "who": who,
            "action": action,
            "resource_id": resource_id,
            "resource_name": resource_name,
            "resource_type": resource_type,
            "timestamp": (datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S"),
            "location": location,
            "request_context": request_context or {},
            "context": context or {},
            "client": client or {},
            "tenant_id": tenant_id,
            "deployment_id": deployment_id or os.getenv("DEPLOYMENT_ID"),
        }
        try:
            with open(self.file_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to audit log file {self.file_path}: {e}")
            raise IOError(f"Failed to write audit log to {self.file_path}") from e 