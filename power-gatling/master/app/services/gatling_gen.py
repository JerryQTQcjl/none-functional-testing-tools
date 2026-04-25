"""Gatling Java DSL simulation code generator."""

from urllib.parse import urlparse

from jinja2 import Environment, BaseLoader

SIMULATION_TEMPLATE = """package loadforge;

import io.gatling.javaapi.core.*;
import io.gatling.javaapi.http.*;
import java.time.Duration;
import java.util.Map;

import static io.gatling.javaapi.core.CoreDsl.*;
import static io.gatling.javaapi.http.HttpDsl.*;

public class {{ class_name }} extends Simulation {
{% if headers and headers|length > 0 %}
    private static final Map<String, String> CUSTOM_HEADERS = Map.of(
    {% for key, value in headers.items() %}
        "{{ key }}", "{{ value }}"{% if not loop.last %},{% endif %}

    {% endfor %}
    );
{% endif %}

    private HttpProtocolBuilder httpProtocol = http
        .baseUrl("{{ base_url }}")
        .header("x-load-test", "true")
{% if headers %}
    {% for key, value in headers.items() %}
        .header("{{ key }}", "{{ value }}")
    {% endfor %}
{% endif %}
        .acceptHeader("application/json")
        .acceptEncodingHeader("gzip, deflate")
        .userAgentHeader("LoadForge-Worker/1.0");

    private ScenarioBuilder scn = scenario("{{ class_name }}")
        .exec(
            http("{{ request_name }}")
                .{{ method_lower }}("{{ path }}")
{% if body %}
                .body(StringBody("{{ body_escaped }}"))
                .asJson()
{% endif %}
                .check(status().is({{ expected_status }}))
        );

    {
        setUp(
            scn.injectOpen(
                rampUsers({{ users }}).during(Duration.ofSeconds({{ ramp_up_seconds }})),
                constantUsersPerSec((double) {{ users }} / Math.max(1, {{ sustained_seconds }}))
                    .during(Duration.ofSeconds({{ sustained_seconds }}))
            )
        ).protocols(httpProtocol)
         .assertions(
             global().failedRequests().percent().lt(50.0)
         );
    }
}
"""


def generate_simulation(config: dict) -> str:
    """Generate Gatling Java simulation code from test configuration."""
    url = config["target_url"]
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path or "/"

    class_name = f"Sim_{config.get('scenario_id', 'default').replace('-', '_')}"
    request_name = f"{config.get('method', 'GET')} {path}"

    body = config.get("body")
    body_escaped = ""
    if body:
        body_escaped = body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    template_data = {
        "class_name": class_name,
        "base_url": base_url,
        "path": path,
        "method_lower": (config.get("method", "GET") or "GET").lower(),
        "request_name": request_name,
        "headers": config.get("headers", {}),
        "body": body,
        "body_escaped": body_escaped,
        "expected_status": config.get("expected_status", 200),
        "users": config.get("concurrent_users", 100),
        "ramp_up_seconds": config.get("ramp_up_duration", 10),
        "sustained_seconds": config.get("sustained_duration", 60),
    }

    env = Environment(loader=BaseLoader(), keep_trailing_newline=True)
    template = env.from_string(SIMULATION_TEMPLATE)
    return template.render(**template_data)
