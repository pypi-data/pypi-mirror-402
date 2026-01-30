from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import os

class StepPayload(BaseModel):
    name: str
    type: str # "tool", "llm", "planning", "custom"
    stage: Optional[str] = None # Mapped to backend stage
    cognitive_type: Optional[str] = None # Cognitive phase
    status: str # "success", "failure"
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    content: Optional[Dict[str, Any]] = None # Generic content container for persistence
    duration_ms: Optional[float] = None
    started_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class RunPayload(BaseModel):
    run_id: str
    name: str
    org_id: str = Field(default_factory=lambda: os.getenv("LIGHTCURVE_ORG_ID", "default-org"))
    agent_id: str # Mapped from name if not provided
    project: Optional[str] = Field(default_factory=lambda: os.getenv("LIGHTCURVE_PROJECT_ID"))
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    status: str # "success", "failure"
    duration_ms: Optional[float] = None
    started_at: datetime
    steps: List[StepPayload] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    exception: Optional[str] = None

    @field_validator('run_id')
    def run_id_must_be_present(cls, v):
        if not v or not v.strip():
            raise ValueError('run_id cannot be empty')
        return v

class IncidentFlags(BaseModel):
    rule_id: str
    severity: str
    description: Optional[str] = None

class InputPayload(BaseModel):
    user_input: str
    interpreted_goal: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)

class KnowledgePayload(BaseModel):
    summary: str
    evidence_present: bool = False
    sources: List[str] = Field(default_factory=list)

class PlanPayload(BaseModel):
    steps: List[str]
    rationale: Optional[str] = None
    alternatives: List[str] = Field(default_factory=list)

class ToolPayload(BaseModel):
    tool_name: str
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    success: bool = True
    retries: int = 0
    latency_ms: Optional[float] = None

class ValidationPayload(BaseModel):
    result: bool
    method: str = "auto"
    confidence_score: Optional[float] = None

class OutputPayload(BaseModel):
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None

# Union type for payloads
PayloadType = Union[InputPayload, KnowledgePayload, PlanPayload, ToolPayload, ValidationPayload, OutputPayload, Dict[str, Any]]

class CognitionEvent(BaseModel):
    run_id: str
    agent_id: str
    org_id: str = Field(default_factory=lambda: os.getenv("LIGHTCURVE_ORG_ID", "default-org"))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: str # input, knowledge, plan, tool, validation, output
    data: Any # PayloadType
    incident_flags: Optional[IncidentFlags] = None

