#input_type_name: WriteTriageResultInput
#output_type_name: WriteTriageResultResult
#function_name: write_triage_result
from typing import Optional
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class WriteTriageResultInput(BaseModel):
    record_id: str
    is_duplicate: bool
    duplicate_of_id: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[int] = None
    repro_steps: Optional[str] = None
    notes: Optional[str] = None


class WriteTriageResultResult(BaseModel):
    ok: bool
    record_id: str


async def write_triage_result(ctx: FunctionContext, data: WriteTriageResultInput) -> WriteTriageResultResult:
    pod = Pod.from_env()

    dup_id = (data.duplicate_of_id or "").strip()

    if data.is_duplicate and dup_id:
        update_payload = {
            "status": "duplicate",
            "duplicate_of_id": dup_id,
        }
    else:
        update_payload = {
            "status": "triaged",
            "severity": data.severity or "medium",
            "priority": data.priority if data.priority is not None else 3,
            "repro_steps": data.repro_steps or "",
        }
        if data.notes:
            update_payload["description"] = data.notes

    pod.table("issues").update(data.record_id, update_payload)

    return WriteTriageResultResult(ok=True, record_id=data.record_id)
