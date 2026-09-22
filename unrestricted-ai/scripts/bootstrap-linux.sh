#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
export STACK_ROOT="${STACK_ROOT:-/mnt/f/backup/UnrestrictedAi}"
export OLLAMA_MODELS="$STACK_ROOT/ollama_models" DOCKER_CONFIG="$STACK_ROOT/docker_config"
export HF_HOME="$STACK_ROOT/hf_cache" TMPDIR="$STACK_ROOT/tmp" PIP_CACHE_DIR="$STACK_ROOT/pip_cache"
# GnuPG requires Unix temporary-file semantics. This directory is in the F: VHDX.
export TMPDIR=/tmp
mkdir -p "$TMPDIR" "$DOCKER_CONFIG"
exec > >(tee -a "$STACK_ROOT/logs/bootstrap-linux.log") 2>&1
apt-get update -o Acquire::Retries=3
apt-get install -y --no-install-recommends ca-certificates curl gnupg python3 python3-venv
install -m 0755 -d /etc/apt/keyrings
curl -fsSL --retry 3 https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable' > /etc/apt/sources.list.d/docker.list
curl -fsSL --retry 3 https://nvidia.github.io/libnvidia-container/gpgkey | gpg --batch --yes --dearmor -o /etc/apt/keyrings/nvidia-container-toolkit.gpg
curl -fsSL --retry 3 https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/etc/apt/keyrings/nvidia-container-toolkit.gpg] https://#g' > /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt-get update -o Acquire::Retries=3
apt-get install -y --no-install-recommends docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin nvidia-container-toolkit
mkdir -p /etc/docker
echo '{"log-driver":"local","log-opts":{"max-size":"10m","max-file":"3"}}' > /etc/docker/daemon.json
nvidia-ctk runtime configure --runtime=docker
cat > /etc/wsl.conf <<'EOF'
[boot]
systemd=true
[user]
default=root
EOF
echo 'Bootstrap packages installed. Restart this distribution to enable systemd.'
