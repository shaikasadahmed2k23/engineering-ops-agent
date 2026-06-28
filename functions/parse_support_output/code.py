#input_type_name: ParseSupportOutputInput
#output_type_name: ParseSupportOutputResult
#function_name: parse_support_output
import json
import re
from pydantic import BaseModel
from lemma_sdk import FunctionContext


class ParseSupportOutputInput(BaseModel):
    raw_answer: str


class ParseSupportOutputResult(BaseModel):
    escalate: bool
    escalation_reason: str
    draft_reply: str
    is_bug_report: bool


async def parse_support_output(ctx: FunctionContext, data: ParseSupportOutputInput) -> ParseSupportOutputResult:
    text = data.raw_answer.strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    json_text = match.group(0) if match else text

    parsed = json.loads(json_text)

    return ParseSupportOutputResult(
        escalate=bool(parsed.get("escalate", False)),
        escalation_reason=parsed.get("escalation_reason") or "",
        draft_reply=parsed.get("draft_reply") or "",
        is_bug_report=bool(parsed.get("is_bug_report", False)),
    )
