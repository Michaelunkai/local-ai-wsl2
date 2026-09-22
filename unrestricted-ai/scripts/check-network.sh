#!/usr/bin/env bash
# Detect the observed WSL/Docker loss of this project's forwarding rules.
set -euo pipefail
id=$(docker network inspect unrestricted-ai_default --format '{{.Id}}' 2>/dev/null) || exit 0
bridge="br-${id:0:12}"
iptables -C DOCKER-FORWARD -i "$bridge" -j ACCEPT 2>/dev/null || {
  echo "Project network forwarding rule missing for $bridge" >&2
  exit 1
}
iptables -C DOCKER-CT -o "$bridge" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || exit 1
sandbox=$(docker network inspect unrestricted-ai_sandbox --format '{{.Id}}')
sandbox_bridge="br-${sandbox:0:12}"
iptables -C DOCKER-INTERNAL -i "$sandbox_bridge" ! -o "$sandbox_bridge" -j DROP 2>/dev/null || exit 1
iptables -C DOCKER-INTERNAL ! -i "$sandbox_bridge" -o "$sandbox_bridge" -j DROP 2>/dev/null || exit 1
iptables -C DOCKER-FORWARD -i "$sandbox_bridge" -o "$sandbox_bridge" -j ACCEPT 2>/dev/null || exit 1
