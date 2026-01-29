from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import time
import uuid
import json

# Contract version for compatibility checks
SCHEMA_VERSION = "1.0"

@dataclass
class ExecutionRequest:
    """
    Generic request to the Execution Layer (Worker).
    Support various operation types via payload.
    
    All fields are JSON-serializable for remote execution.
    """
    type: str  # e.g., "execute_plan", "scan_repo", "apply_patch"
    payload: Dict[str, Any] = field(default_factory=dict)
    turn: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Versioning and idempotency
    schema_version: str = SCHEMA_VERSION
    request_id: Optional[str] = None  # Idempotency key
    created_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())[:8]

@dataclass
class ExecutionResult:
    """
    Generic result from Execution Layer.
    
    Contains facts only - no semantic success/failure logic.
    All fields are JSON-serializable for remote execution.
    """
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)  # Main response payload
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    logs: str = ""
    status: str = "completed"  # COMPLETED | FAILED | TIMED_OUT
    error: Optional[str] = None
    # Versioning and tracing
    schema_version: str = SCHEMA_VERSION
    request_id: Optional[str] = None  # Echo back from request
    created_at: float = field(default_factory=time.time)

class StepStatus(str, Enum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"

@dataclass
class StepRecord:
    """
    Database representation of a Step.
    """
    run_id: str
    step_id: int
    type: str
    payload: dict
    status: StepStatus
    worker_id: Optional[str] = None
    result: Optional[dict] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
