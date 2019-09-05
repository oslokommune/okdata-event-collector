import json

event_with_list = {"body": json.dumps([{"key00": "value00"}])}

event_with_object = {"body": json.dumps({"key00": "value00"})}

expected_event_body = [{"key00": "value00"}]
