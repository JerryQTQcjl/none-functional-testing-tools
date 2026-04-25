"""Gatling simulation Java code generator from Jinja2 template."""

from jinja2 import Environment, FileSystemLoader
from urllib.parse import urlparse


class SimulationBuilder:
    def __init__(self, template_dir: str):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            keep_trailing_newline=True,
        )

    def build(self, config: dict, output_path: str) -> str:
        url = config["target_url"]
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path or "/"

        body = config.get("body")
        body_escaped = ""
        if body:
            body_escaped = body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

        class_name = f"Sim_{config.get('execution_id', 'default').replace('-', '_')}"

        template_data = {
            "class_name": class_name,
            "base_url": base_url,
            "path": path,
            "method_lower": (config.get("method", "GET") or "GET").lower(),
            "request_name": f"{config.get('method', 'GET')} {path}",
            "headers": config.get("headers", {}),
            "body": body,
            "body_escaped": body_escaped,
            "expected_status": config.get("expected_status", 200),
            "users": config.get("concurrent_users", 100),
            "ramp_up_seconds": config.get("ramp_up_duration", 10),
            "sustained_seconds": config.get("sustained_duration", 60),
        }

        template = self.env.get_template("simulation.java.j2")
        code = template.render(**template_data)

        with open(output_path, "w") as f:
            f.write(code)

        return output_path
