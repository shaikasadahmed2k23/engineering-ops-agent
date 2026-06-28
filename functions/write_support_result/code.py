#input_type_name: WriteSupportResultInput
#output_type_name: WriteSupportResultResult
#function_name: write_support_result
from typing import Optional
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class WriteSupportResultInput(BaseModel):
    record_id: str
    subject: str
    body: str
    escalate: bool
    escalation_reason: str
    draft_reply: str
    is_bug_report: bool


class WriteSupportResultResult(BaseModel):
    ok: bool
    record_id: str
    created_issue_id: Optional[str] = None


async def write_support_result(ctx: FunctionContext, data: WriteSupportResultInput) -> WriteSupportResultResult:
    pod = Pod.from_env()

    created_issue_id = None

    if data.is_bug_report:
        new_issue = pod.table("issues").create({
            "source": "support",
            "title": data.subject,
            "description": data.body,
            "status": "new",
        })
        created_issue_id = new_issue.get("id")

    status = "escalated" if data.escalate else "drafted"

    update_payload = {
        "status": status,
        "escalated": data.escalate,
        "escalation_reason": data.escalation_reason,
        "draft_reply": data.draft_reply,
    }
    if created_issue_id:
        update_payload["related_issue_id"] = created_issue_id

    pod.table("tickets").update(data.record_id, update_payload)

    return WriteSupportResultResult(
        ok=True,
        record_id=data.record_id,
        created_issue_id=created_issue_id,
    )
