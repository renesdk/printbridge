#!/bin/sh
set -eu
: "${PRINTBRIDGE_ADMIN_PASSWORD:?Set PRINTBRIDGE_ADMIN_PASSWORD in the app installer}"
/usr/sbin/cupsd -f &
cups_pid=$!
web_pid=
announce_pid=
stop() {
    [ -z "$announce_pid" ] || kill -TERM "$announce_pid" 2>/dev/null || true
    [ -z "$web_pid" ] || kill -TERM "$web_pid" 2>/dev/null || true
    kill -TERM "$cups_pid" 2>/dev/null || true
    wait "$cups_pid" 2>/dev/null || true
}
trap stop INT TERM EXIT
i=0
until lpstat -r 2>/dev/null | grep -q 'scheduler is running'; do
    i=$((i + 1))
    [ "$i" -lt 30 ] || exit 1
    sleep 1
done
cupsctl --remote-any --share-printers
python3 /opt/printbridge/web.py &
web_pid=$!
if [ -n "${PRINTBRIDGE_ADVERTISE_IP:-}" ]; then
    python3 /opt/printbridge/announce.py &
    announce_pid=$!
fi
wait "$web_pid"
