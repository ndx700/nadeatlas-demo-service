#!/usr/bin/env bash
set -euxo pipefail
rm -rf /tmp/hltv-api
git clone --depth=1 https://github.com/Gabrielcnetto/HLTV-api.git /tmp/hltv-api
cd /tmp/hltv-api
go version
go build -o /tmp/hltv-api-server .
(/tmp/hltv-api-server >/tmp/hltv-api.log 2>&1 & echo $! >/tmp/hltv-api.pid)
sleep 4
echo "=== /api/last-results ==="
curl -i --max-time 90 http://127.0.0.1:8080/api/last-results | head -c 12000 || true
echo
echo "=== server log ==="
tail -100 /tmp/hltv-api.log || true
kill $(cat /tmp/hltv-api.pid) || true
