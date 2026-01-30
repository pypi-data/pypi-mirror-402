# Starlette API Server

A simple Starlette API server with basic endpoints.

## Setup

Install dependencies:
```bash
uv sync
```

## Running the server

the server needs to be launched with uvicorn:

For dev usage:

```bash
uv run uvicorn app:app --host 127.0.0.1 --port 4290 --reload
```

