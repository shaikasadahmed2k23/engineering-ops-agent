#input_type_name: ParseTriageOutputInput
#output_type_name: ParseTriageOutputResult
#function_name: parse_triage_output
import json
import re
from pydantic import BaseModel
from lemma_sdk import FunctionContext


class ParseTriageOutputInput(BaseModel):
    raw_answer: str


class ParseTriageOutputResult(BaseModel):
    is_duplicate: bool
    duplicate_of_id: str
    severity: str
    priority: int
    repro_steps: str


async def parse_triage_output(ctx: FunctionContext, data: ParseTriageOutputInput) -> ParseTriageOutputResult:
    text = data.raw_answer.strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    json_text = match.group(0) if match else text

    parsed = json.loads(json_text)
    is_duplicate = bool(parsed.get("is_duplicate", False))

    return ParseTriageOutputResult(
        is_duplicate=is_duplicate,
        duplicate_of_id=parsed.get("duplicate_of_id") or "",
        severity=parsed.get("severity") or "medium",
        priority=parsed.get("priority") if parsed.get("priority") is not None else 3,
        repro_steps=parsed.get("repro_steps") or "",
    )
