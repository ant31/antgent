import json
import re
from typing import Any


def consert_output_json(input_str: str) -> dict[str, Any]:
    regex = r"```json.*?(\{.*\}).*?```"
    matches = re.search(regex, input_str, re.DOTALL | re.MULTILINE)
    if matches:
        res = matches.group(1)
        jsonoutput = json.loads(res)
    else:
        jsonoutput = json.loads(input_str)
    return jsonoutput
