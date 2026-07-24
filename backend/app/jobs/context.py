"""
app/jobs/context.py — JobContext

Carries correlation and execution metadata throughout the pipeline.
Workers propagate this to every stage; stages never construct it directly.
"""
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobContext:
    """Immutable execution context passed through every pipeline stage."""
    job_execution_id: str
    document_id: Optional[str]
    organization_id: str
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_type: str = "DOCUMENT_PROCESSING"
    metadata: dict = field(default_factory=dict)

    def child(self, **overrides) -> "JobContext":
        """Return a derived context (e.g. for a stage-level span)."""
        import dataclasses
        return dataclasses.replace(self, **overrides)
