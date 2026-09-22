#!/usr/bin/env bash
set -Eeuo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
systemctl start docker
gateway=$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}')
[[ "$gateway" == '172.17.0.1' ]] || { echo "Unexpected Docker bridge gateway: $gateway" >&2; exit 1; }
changed=false
for unit in ollama-relay.socket ollama-relay.service embedding-relay.socket embedding-relay.service host-tools-relay.socket host-tools-relay.service unrestricted-ai-network-reconcile.service unrestricted-ai-network-reconcile.timer; do
    if [[ "$(readlink "/etc/systemd/system/$unit" || true)" != "$root/docker/$unit" ]]; then
        ln -sfn "$root/docker/$unit" "/etc/systemd/system/$unit"
        changed=true
    fi
done
if $changed; then systemctl daemon-reload; fi
systemctl enable --now ollama-relay.socket embedding-relay.socket host-tools-relay.socket unrestricted-ai-network-reconcile.timer
