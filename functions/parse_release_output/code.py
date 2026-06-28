#input_type_name: ParseReleaseOutputInput
#output_type_name: ParseReleaseOutputResult
#function_name: parse_release_output
import json
import re
from pydantic import BaseModel
from lemma_sdk import FunctionContext


class ParseReleaseOutputInput(BaseModel):
    raw_answer: str


class ParseReleaseOutputResult(BaseModel):
    risk_level: str
    risk_flags: str
    test_plan: str
    release_notes: str


async def parse_release_output(ctx: FunctionContext, data: ParseReleaseOutputInput) -> ParseReleaseOutputResult:
    text = data.raw_answer.strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    json_text = match.group(0) if match else text

    parsed = json.loads(json_text)

    return ParseReleaseOutputResult(
        risk_level=parsed.get("risk_level") or "medium",
        risk_flags=parsed.get("risk_flags") or "None identified",
        test_plan=parsed.get("test_plan") or "",
        release_notes=parsed.get("release_notes") or "",
    )
