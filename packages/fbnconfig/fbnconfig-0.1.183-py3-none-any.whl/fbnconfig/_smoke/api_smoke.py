from __future__ import annotations
import os
import time
import httpx

READY_ENDPOINT = "/ready"
DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/fbnconfig"
DEFAULT_DEADLINE_SECONDS = 30.0
POLL_INTERVAL_SECONDS = 0.5

def wait_for_server_ready(base_url: str, deadline_seconds: float) -> None:
    """Polls the /ready endpoint until the server is ready or deadline is reached."""
    deadline = time.time() + deadline_seconds
    last_error: str | None = None

    while time.time() < deadline:
        try:
            response = httpx.get(f"{base_url}{READY_ENDPOINT}", timeout=2)
            if response.status_code == 200:
                return  # Server is ready
            last_error = f"ready={response.status_code} {response.text}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(POLL_INTERVAL_SECONDS)

    raise RuntimeError(f"Server did not become ready: {last_error}")

def main() -> None:
    base_url = os.getenv("SMOKE_BASE") or os.getenv("BASE") or DEFAULT_BASE_URL
    deadline_seconds = float(os.getenv("SMOKE_DEADLINE_SECONDS", str(DEFAULT_DEADLINE_SECONDS)))
    if not base_url.startswith("http"):
        raise ValueError(f"Invalid base URL: {base_url}")

    wait_for_server_ready(base_url, deadline_seconds)

    # Check if the API is active
    health = httpx.get(f"{base_url}/health", timeout=5)
    assert health.status_code == 200, f"Health check failed: {health.text}"
    print("\u2713 Health:", health.json())

    # Check if the API is ready for requests
    ready = httpx.get(f"{base_url}/ready", timeout=5)
    assert ready.status_code == 200, f"Ready check failed: {ready.text}"
    print("\u2713 Ready:", ready.json())

    # Send a test request with a known CorrelationId header
    headers = {"CorrelationId": "runsh-corr"} # "runsh-corr" is used as a test value
    invoke = httpx.post(f"{base_url}/invoke", json={"test": "run.sh"}, headers=headers, timeout=5)
    assert invoke.status_code == 200, f"Invoke failed: {invoke.text}"
    print("\u2713 Invoke:", invoke.json())

    # Make sure the server sends back the same CorrelationId header
    assert invoke.headers.get("correlationid") == "runsh-corr", (
        f"CorrelationId header not echoed: {invoke.headers.get('correlationid')}"
    )
    print("\u2713 Echo CorrelationId:", invoke.headers.get("correlationid"))

# Calls the main() function only when the file is run directly
if __name__ == "__main__":
    main()
