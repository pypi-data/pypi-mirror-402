# Import "uv" base image of Python (Stripped down version of python, smaller attack surface)
FROM harbor.finbourne.com/external-images/ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

#-----------BUILDER STAGE-----------#

# UV_COMPILE_BYTECODE  -  Compiles Python files as bytecode (.pyc) during initial install, allowing for faster start as python doesn't need to compile on the first run
# UV_LINK_MODE         -  Controls how Python files are linked in the virtual environment. "copy" means files are copied rather than symlinked (pointed at). Copying prevents issues with layering. 
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Set working directory
WORKDIR /app

# Install dependencies first (better layer caching)
# Note: Avoid BuildKit-only `RUN --mount=...` so this builds with Podman/Buildah too.
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-install-project --no-dev

# Copies  application's files and folders from local machine into the Docker image.
COPY fbnconfig /app/fbnconfig
COPY server /app/server
COPY examples /app/examples
COPY pyproject.toml uv.lock readme.md fbnconfig.md /app/

# Installs dependencies from uv.lock and also installs project. 
# --frozen means it will lock versions and no auto update. 
# --no-dev skips development dependencies such as tests and linting.
RUN uv sync --frozen --no-dev

# Create non-root user 10000 to fit "high" safe range per UID/GID ranges (Linux convention)
# Changes ownership for everything in the directory from root to new fbnconfig user
RUN groupadd -r -g 10000 fbnconfig && \
    useradd --no-log-init -r -m -u 10000 -g fbnconfig fbnconfig && \
    chown -R fbnconfig:fbnconfig /app

#-----------TESTER STAGE-----------#

# Creating a new stage called tester
# Modifies the PATH environment variable to find Python executables
# PYTHONUNBUFFERED - Disables Python's output buffering - because for docker files especially during logging we want real-time output
FROM builder AS tester
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Run the following commands making it -e exit immediately if a command fails and -u catch typos 
# port - Port for the API server to listen on,  base - Base URL for the API server
# Only listen locally inside the container 127.0.0.1, allowing 30s for cleanup when shutting down - (& means background process)
# Store the process ID of the background server to terminate it later
# When the script exists, kill the background server, we don't care about error messages, wait for it to fully stop
# Even if the kill or wait commands fail, dont fail the sript.
# Defining the SMOKE_BASE environment variable to be used by the smoke tests to point at the running server
RUN set -eu; \
    port=8000; \
    base="http://127.0.0.1:${port}/api/fbnconfig"; \
    uv run python -m uvicorn server.app:app --host 127.0.0.1 --port "${port}" --timeout-graceful-shutdown 30 & \
    pid="$!"; \
    trap 'kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true' EXIT; \
    SMOKE_BASE="$base" uv run python -m fbnconfig._smoke.api_smoke



#-----------RUNTIME STAGE-----------#


# Use Harbor-mirrored distroless python image (runtime image with python interpreter only, no shell, no package manager, smaller attack surface)
FROM harbor.finbourne.com/external-images/gcr.io/distroless/python3-debian12:nonroot

# Setting user and group id that container runs in. Distroless default nonroot user has uid/gid 65532.
USER 65532:65532

# Copy only the necessary files from the tester stage to the runtime stage. Docker does the copying and sets ownership to non-root user.
COPY --from=tester --chown=65532:65532 /app/.venv/lib/python3.11/site-packages /app/site-packages
COPY --from=tester --chown=65532:65532 /app/fbnconfig /app/fbnconfig
COPY --from=tester --chown=65532:65532 /app/server /app/server
COPY --from=tester --chown=65532:65532 /app/examples /app/examples

# Set working directory
WORKDIR /app

# Setting env variables
# PYTHONDONTWRITEBYTECODE - Prevents Python from writing .pyc files to disk (already done during build)
# Setting directories 
ENV PYTHONPATH="/app/site-packages" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/tmp \
    TMPDIR=/tmp

# Expose default API port
EXPOSE 8000

# Note: HEALTHCHECK removed - use Kubernetes probes instead:
# - livenessProbe: /api/fbnconfig/health
# - readinessProbe: /api/fbnconfig/ready

# Start as API server instead of CLI
# --timeout-graceful-shutdown: Allow graceful shutdown for in-flight requests
# --timeout-keep-alive: Timeout idle connections (important for C# sidecar caller)
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["server.app:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "30", "--timeout-keep-alive", "10"]
