###########################################################
#            Testing Script for Royal TS Logging          #
#              copyright (c) DatACT GmbH, 2025            #
###########################################################
import http.server
import socketserver
import json

PORT = 8081  # Change this to the port you want to listen on

def recursively_parse_json(obj):
    """
    Recursively scans and converts:
    1. JSON-encoded strings into proper JSON objects.
    2. Lists of {"Key": "...", "Value": "..."} pairs into dictionaries.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                try:
                    parsed_value = json.loads(value)
                    obj[key] = recursively_parse_json(parsed_value)  # Recurse for nested JSON
                except json.JSONDecodeError:
                    pass  # Keep as is if it's not valid JSON
            else:
                obj[key] = recursively_parse_json(value)

        # Convert key-value pair lists into dictionaries
        if all(isinstance(item, dict) and "Key" in item and "Value" in item for item in obj.values()):
            return {item["Key"]: item["Value"] for item in obj.values()}

    elif isinstance(obj, list):
        # Check if it's a key-value pair list that can be converted into a dictionary
        if all(isinstance(item, dict) and "Key" in item and "Value" in item for item in obj):
            return {item["Key"]: item["Value"] for item in obj}
        return [recursively_parse_json(item) for item in obj]

    return obj

def filter_activity_logs(logs):
    """
    Filters logs to only include entries where:
    "Properties": {"SourceContext": "RoyalTS.App.Logging.Category.Activity"}
    """
    if isinstance(logs, list):
        return [log for log in logs if log.get("Properties", {}).get("SourceContext") == "RoyalTS.App.Logging.Category.Activity"]
    elif isinstance(logs, dict):
        return logs if logs.get("Properties", {}).get("SourceContext") == "RoyalTS.App.Logging.Category.Activity" else None
    return []

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"Received GET request:\nPath: {self.path}\nHeaders:\n{self.headers}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        print(f"PATH: {self.path}")        
        body = self.rfile.read(content_length) if content_length else b''
        if body:
            try:
                parsed_body = json.loads(body.decode(errors='ignore'))
                parsed_body = recursively_parse_json(parsed_body)  # Fix JSON-encoded strings & convert key-value lists to dicts
                filtered_logs = filter_activity_logs(parsed_body)  # Only keep activity logs

                if filtered_logs:
                    formatted_json = json.dumps(filtered_logs, indent=4, ensure_ascii=False)
                    print(f"Filtered Activity Logs:\n{formatted_json}")

            except json.JSONDecodeError:
                print(f"Body (raw):\n{body.decode(errors='ignore')}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return # Suppress default logging

def run_server(port):
    with socketserver.TCPServer(("", port), RequestHandler) as httpd:
        print(f"Listening on port {port}...")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server(PORT)
