FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY docker/sandbox.requirements.lock /opt/requirements.lock
RUN pip install -r /opt/requirements.lock && useradd -m -u 1000 sandbox
WORKDIR /workspace
USER 1000:1000
CMD ["python", "-m", "jupyter_server", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--ServerApp.root_dir=/workspace", "--ServerApp.allow_remote_access=True"]
