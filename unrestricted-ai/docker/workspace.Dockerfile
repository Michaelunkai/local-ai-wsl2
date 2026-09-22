FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY docker/workspace.requirements.lock /app/requirements.lock
RUN pip install -r /app/requirements.lock
COPY scripts/workspace_api.py /app/workspace_api.py
CMD ["uvicorn", "workspace_api:app", "--host", "0.0.0.0", "--port", "8000"]
