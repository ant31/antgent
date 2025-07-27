import json
import re


def parse_json_mk(input_str: str) -> dict:
    regex = r"```json.*?(\{.*\}).*?```"
    matches = re.search(regex, input_str, re.DOTALL | re.MULTILINE)
    if matches:
        res = matches.group(1)
        jsonoutput = json.loads(res)
    else:
        jsonoutput = json.loads(input_str)
    return jsonoutput
