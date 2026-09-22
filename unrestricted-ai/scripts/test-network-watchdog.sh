#!/usr/bin/env bash
set -Eeuo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

timer=unrestricted-ai-network-reconcile.timer
systemctl is-active --quiet "$timer" || { echo "$timer is not active" >&2; exit 1; }

id=$(docker network inspect unrestricted-ai_default --format '{{.Id}}')
[[ "$id" =~ ^[a-f0-9]{64}$ ]] || { echo 'Cannot identify project network' >&2; exit 1; }
bridge="br-${id:0:12}"
iptables -C DOCKER-FORWARD -i "$bridge" -j ACCEPT
iptables -D DOCKER-FORWARD -i "$bridge" -j ACCEPT

deadline=$((SECONDS+45))
until iptables -C DOCKER-FORWARD -i "$bridge" -j ACCEPT 2>/dev/null; do
    (( SECONDS < deadline )) || { echo 'Network watchdog did not restore forwarding in 45 seconds' >&2; exit 1; }
    sleep 1
done

docker exec -i unrestricted-ai-workspace-api-1 python - <<'PY'
import socket

import requests

addresses = socket.getaddrinfo('example.com', 443, type=socket.SOCK_STREAM)
assert addresses, 'Docker DNS returned no addresses for example.com'

r = requests.get('https://example.com/', timeout=15)
r.raise_for_status()

r = requests.get('http://open-webui:8080/health', timeout=15)
r.raise_for_status()
assert r.json().get('status') is True
PY

sandbox=$(docker network inspect unrestricted-ai_sandbox --format '{{.Id}}')
sandbox_bridge="br-${sandbox:0:12}"
iptables -C DOCKER-INTERNAL -i "$sandbox_bridge" ! -o "$sandbox_bridge" -j DROP
iptables -C DOCKER-INTERNAL ! -i "$sandbox_bridge" -o "$sandbox_bridge" -j DROP
iptables -C DOCKER-FORWARD -i "$sandbox_bridge" -o "$sandbox_bridge" -j ACCEPT

timestamp=$(date --iso-8601=seconds)
cat > "$root/logs/network-watchdog-test.json" <<EOF
{
  "passed": true,
  "timestamp": "$timestamp",
  "bridge": "$bridge",
  "restoredWithinSeconds": 45,
  "containerConnectivity": true,
  "externalDns": true,
  "externalHttps": true,
  "sandboxIsolationPreserved": true
}
EOF
printf 'PASS network watchdog restored %s and preserved sandbox isolation\n' "$bridge"
