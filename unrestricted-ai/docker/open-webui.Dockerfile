FROM ghcr.io/open-webui/open-webui@sha256:8b432fe0a65b91116afc7961365c6cca5379cc923171386a96691f3471f3cae9

# Keep the installed WebUI release and replace only the context-compaction
# module. This handles a tool-heavy first turn that fills a 32K context before
# the upstream three-message minimum can compact it.
COPY docker/open-webui-context-compaction.py /app/backend/open_webui/utils/context_compaction.py
