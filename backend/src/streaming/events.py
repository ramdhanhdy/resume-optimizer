"""Event types for SSE streaming."""

from typing import Literal, Union, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class BaseEvent(BaseModel):
    """Base event with common fields."""
    type: str
    ts: int = Field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    job_id: str


class JobStatusEvent(BaseEvent):
    """Job status change event."""
    type: Literal["job_status"] = "job_status"
    payload: dict = Field(default_factory=dict)
    
    @classmethod
    def create(cls, job_id: str, status: Literal["started", "running", "completed", "failed", "canceled"]):
        return cls(job_id=job_id, payload={"status": status})


class StepProgressEvent(BaseEvent):
    """Step progress update event."""
    type: Literal["step_progress"] = "step_progress"
    payload: dict = Field(default_factory=dict)
    
    @classmethod
    def create(cls, job_id: str, step: str, pct: float, eta_sec: Optional[float] = None):
        payload = {"step": step, "pct": pct}
        if eta_sec is not None:
            payload["eta_sec"] = eta_sec
        return cls(job_id=job_id, payload=payload)


class InsightEvent(BaseEvent):
    """Insight emitted event."""
    type: Literal["insight_emitted"] = "insight_emitted"
    payload: dict = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        job_id: str,
        insight_id: str,
        category: str,
        importance: Literal["low", "medium", "high"],
        message: str,
        step: Optional[str] = None,
    ):
        payload = {
            "id": insight_id,
            "category": category,
            "importance": importance,
            "message": message,
        }
        if step:
            payload["step"] = step
        return cls(job_id=job_id, payload=payload)


class MetricUpdateEvent(BaseEvent):
    """Metric update event."""
    type: Literal["metric_update"] = "metric_update"
    payload: dict = Field(default_factory=dict)
    
    @classmethod
    def create(cls, job_id: str, key: str, value: float, unit: Optional[str] = None):
        payload = {"key": key, "value": value}
        if unit:
            payload["unit"] = unit
        return cls(job_id=job_id, payload=payload)


class ValidationUpdateEvent(BaseEvent):
    """Validation update event."""
    type: Literal["validation_update"] = "validation_update"
    payload: dict = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        job_id: str,
        rule_id: str,
        status: Literal["pass", "warn", "fail"],
        message: Optional[str] = None,
    ):
        payload = {"rule_id": rule_id, "status": status}
        if message:
            payload["message"] = message
        return cls(job_id=job_id, payload=payload)


class DiffChunkEvent(BaseEvent):
    """Diff chunk event."""
    type: Literal["diff_chunk"] = "diff_chunk"
    payload: dict = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        job_id: str,
        section: str,
        summary: str,
        patch_id: Optional[str] = None,
    ):
        payload = {"section": section, "summary": summary}
        if patch_id:
            payload["patch_id"] = patch_id
        return cls(job_id=job_id, payload=payload)


class ErrorEvent(BaseEvent):
    """Error event."""
    type: Literal["error"] = "error"
    payload: dict = Field(default_factory=dict)
    
    @classmethod
    def create(cls, job_id: str, code: str, message: str):
        return cls(job_id=job_id, payload={"code": code, "message": message})


class HeartbeatEvent(BaseEvent):
    """Heartbeat event."""
    type: Literal["heartbeat"] = "heartbeat"
    payload: dict = Field(default_factory=dict)


class AgentStepStartedEvent(BaseEvent):
    """Agent step started event."""
    type: Literal["agent_step_started"] = "agent_step_started"
    payload: dict = Field(default_factory=dict)
    
    @classmethod
    def create(cls, job_id: str, step: str, agent_name: str):
        payload = {"step": step, "agent_name": agent_name}
        return cls(job_id=job_id, payload=payload)


class AgentStepCompletedEvent(BaseEvent):
    """Agent step completed event."""
    type: Literal["agent_step_completed"] = "agent_step_completed"
    payload: dict = Field(default_factory=dict)
    
    @classmethod
    def create(cls, job_id: str, step: str, agent_name: str, total_chars: int):
        payload = {"step": step, "agent_name": agent_name, "total_chars": total_chars}
        return cls(job_id=job_id, payload=payload)


class AgentChunkEvent(BaseEvent):
    """Agent content chunk event."""
    type: Literal["agent_chunk"] = "agent_chunk"
    payload: dict = Field(default_factory=dict)
    
    @classmethod
    def create(cls, job_id: str, step: str, chunk: str, seq: int, total_len: int):
        payload = {
            "step": step,
            "chunk": chunk,
            "seq": seq,
            "total_len": total_len
        }
        return cls(job_id=job_id, payload=payload)


class DoneEvent(BaseEvent):
    """Done event."""
    type: Literal["done"] = "done"
    payload: dict = Field(default_factory=dict)


ProcessingEvent = Union[
    JobStatusEvent,
    StepProgressEvent,
    InsightEvent,
    MetricUpdateEvent,
    ValidationUpdateEvent,
    DiffChunkEvent,
    ErrorEvent,
    HeartbeatEvent,
    DoneEvent,
    AgentStepStartedEvent,
    AgentStepCompletedEvent,
    AgentChunkEvent,
]
