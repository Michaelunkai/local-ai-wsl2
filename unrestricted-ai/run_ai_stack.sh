#!/usr/bin/env bash
set -Eeuo pipefail
export STACK_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export OLLAMA_MODELS="$STACK_ROOT/ollama_models" DOCKER_CONFIG="$STACK_ROOT/docker_config" HF_HOME="$STACK_ROOT/hf_cache"
export TMPDIR="$STACK_ROOT/tmp" PIP_CACHE_DIR="$STACK_ROOT/pip_cache"
mkdir -p "$TMPDIR" "$DOCKER_CONFIG" "$STACK_ROOT/logs" "$STACK_ROOT/runtime" "$STACK_ROOT/workspace"
for directory in open-webui searxng crawl4ai vector_db indexer; do mkdir -p "$STACK_ROOT/data/$directory"; done
if ! docker info >/dev/null 2>&1; then
    if command -v systemctl >/dev/null; then systemctl start docker; fi
fi
docker info >/dev/null
if [[ ! -f "$STACK_ROOT/docker/.env" ]]; then
    python3 - "$STACK_ROOT" <<'PY'
import secrets,sys,pathlib
root=pathlib.Path(sys.argv[1])
(root/'docker/.env').write_text('WEBUI_SECRET_KEY='+secrets.token_hex(32)+'\nJUPYTER_TOKEN='+secrets.token_hex(32)+'\n')
(root/'data/searxng/settings.yml').write_text('use_default_settings: true\nserver:\n  secret_key: "'+secrets.token_hex(32)+'"\n  limiter: false\n  image_proxy: false\nsearch:\n  formats: [html, json]\n')
PY
fi
python3 - "$STACK_ROOT" <<'PY'
import pathlib,secrets,sys
path=pathlib.Path(sys.argv[1])/'docker/.env'
text=path.read_text()
for key in ('CRAWL4AI_API_TOKEN','CRAWL4AI_SECRET_KEY'):
    if not any(line.startswith(key+'=') for line in text.splitlines()): text+=key+'='+secrets.token_hex(32)+'\n'
path.write_text(text)
PY
compose=(docker compose --env-file "$STACK_ROOT/docker/.env" -f "$STACK_ROOT/docker/docker-compose.yml")
if [[ -f "$STACK_ROOT/docker/images.lock.yml" ]]; then compose+=(-f "$STACK_ROOT/docker/images.lock.yml"); fi
repair_network() {
 if ! bash "$STACK_ROOT/scripts/check-network.sh"; then
   bash "$STACK_ROOT/scripts/repair-network.sh"
 fi
}
build_inputs=(
 "$STACK_ROOT/.dockerignore"
 "$STACK_ROOT/docker/open-webui.Dockerfile"
 "$STACK_ROOT/docker/open-webui-context-compaction.py"
 "$STACK_ROOT/docker/workspace.Dockerfile"
 "$STACK_ROOT/docker/workspace.requirements.lock"
 "$STACK_ROOT/scripts/workspace_api.py"
 "$STACK_ROOT/docker/sandbox.Dockerfile"
 "$STACK_ROOT/docker/sandbox.requirements.lock"
)
build_fingerprint() {
 sha256sum "${build_inputs[@]}" | sha256sum | awk '{print $1}'
}
sync_local_images() {
 local fingerprint_path="$STACK_ROOT/runtime/docker-build.fingerprint"
 local current stored='' rebuild=false image
 current=$(build_fingerprint)
 [[ -f "$fingerprint_path" ]] && stored=$(<"$fingerprint_path")
 [[ "$stored" == "$current" ]] || rebuild=true
 for image in unrestricted-ai-open-webui:local unrestricted-ai-workspace:local unrestricted-ai-sandbox:local; do
   docker image inspect "$image" >/dev/null 2>&1 || rebuild=true
 done
 if $rebuild; then
   "${compose[@]}" build
   printf '%s\n' "$current" > "$fingerprint_path.tmp"
   mv -f "$fingerprint_path.tmp" "$fingerprint_path"
 fi
}
case "${1:-start}" in
 start) sync_local_images; "${compose[@]}" up -d --no-build; repair_network; "${compose[@]}" exec -T workspace-api python /project/scripts/wait-ready.py ;;
 stop) "${compose[@]}" stop ;;
 status) "${compose[@]}" ps ;;
 verify) "${compose[@]}" exec -T workspace-api python /project/scripts/wait-ready.py; "${compose[@]}" exec -T workspace-api python /project/scripts/verify_stack.py ;;
 repair)
   shift
   [[ $# -gt 0 ]] || { echo 'Specify services to repair' >&2; exit 2; }
   for service in "$@"; do
     case "$service" in open-webui|workspace-api|searxng|crawl4ai|qdrant|sandbox) ;; *) echo "Unknown service: $service" >&2; exit 2;; esac
   done
   "${compose[@]}" up -d --no-build "$@"
   "${compose[@]}" restart "$@"
   repair_network
   "${compose[@]}" exec -T workspace-api python /project/scripts/wait-ready.py
   ;;
 update)
   docker compose --env-file "$STACK_ROOT/docker/.env" -f "$STACK_ROOT/docker/docker-compose.yml" pull --ignore-buildable
   docker compose --env-file "$STACK_ROOT/docker/.env" -f "$STACK_ROOT/docker/docker-compose.yml" build --pull
   docker compose --env-file "$STACK_ROOT/docker/.env" -f "$STACK_ROOT/docker/docker-compose.yml" up -d
   build_fingerprint > "$STACK_ROOT/runtime/docker-build.fingerprint"
   python3 "$STACK_ROOT/scripts/lock-images.py"
   repair_network
   "${compose[@]}" exec -T workspace-api python /project/scripts/wait-ready.py
   ;;
 *) echo 'Usage: run_ai_stack.sh [start|stop|status|verify|update|repair SERVICE...]' >&2; exit 2 ;;
esac
