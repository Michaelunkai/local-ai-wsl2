#!/usr/bin/env bash
# Reconcile only this Compose project's declared bridge policy, without restarting chats.
set -Eeuo pipefail
ensure() { local table="$1"; shift; iptables -w -t "$table" -C "$@" 2>/dev/null || iptables -w -t "$table" -A "$@"; }
for network in unrestricted-ai_default unrestricted-ai_sandbox; do
  read -r id driver internal project subnet < <(docker network inspect "$network" --format '{{.Id}} {{.Driver}} {{.Internal}} {{index .Labels "com.docker.compose.project"}} {{(index .IPAM.Config 0).Subnet}}')
  [[ "$id" =~ ^[a-f0-9]{64}$ && "$driver" == bridge && "$project" == unrestricted-ai ]] || { echo 'Unexpected project network identity' >&2; exit 1; }
  bridge="br-${id:0:12}"
  if [[ "$network" == unrestricted-ai_sandbox ]]; then
    [[ "$internal" == true ]] || { echo 'Sandbox network must be internal' >&2; exit 1; }
    ensure filter DOCKER-INTERNAL -i "$bridge" ! -o "$bridge" -j DROP
    ensure filter DOCKER-INTERNAL ! -i "$bridge" -o "$bridge" -j DROP
    ensure filter DOCKER-FORWARD -i "$bridge" -o "$bridge" -j ACCEPT
  else
    [[ "$internal" == false ]] || exit 1
    ensure filter DOCKER-CT -o "$bridge" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    ensure filter DOCKER-BRIDGE -o "$bridge" -j DOCKER
    ensure filter DOCKER ! -i "$bridge" -o "$bridge" -j DROP
    ensure filter DOCKER-FORWARD -i "$bridge" -j ACCEPT
    ensure nat POSTROUTING -s "$subnet" ! -o "$bridge" -j MASQUERADE
  fi
done
echo 'Project network policy restored; sandbox remains internal.'
