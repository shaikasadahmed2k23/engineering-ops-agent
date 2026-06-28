#input_type_name: WriteReleaseResultInput
#output_type_name: WriteReleaseResultResult
#function_name: write_release_result
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class WriteReleaseResultInput(BaseModel):
    record_id: str
    risk_level: str
    risk_flags: str
    test_plan: str
    release_notes: str


class WriteReleaseResultResult(BaseModel):
    ok: bool
    record_id: str


async def write_release_result(ctx: FunctionContext, data: WriteReleaseResultInput) -> WriteReleaseResultResult:
    pod = Pod.from_env()

    status = "blocked" if data.risk_level == "high" else "reviewed"

    update_payload = {
        "status": status,
        "risk_level": data.risk_level,
        "risk_flags": data.risk_flags,
        "test_plan": data.test_plan,
        "release_notes_draft": data.release_notes,
    }

    pod.table("prs").update(data.record_id, update_payload)

    return WriteReleaseResultResult(ok=True, record_id=data.record_id)
