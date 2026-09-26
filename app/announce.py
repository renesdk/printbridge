"""Optional DNS-SD announcement of existing CUPS queues on the local LAN."""
import os
import re
import socket
import time
from zeroconf import ServiceInfo, Zeroconf

import core


def description(queue):
    ip = os.environ["PRINTBRIDGE_ADVERTISE_IP"]
    socket.inet_aton(ip)
    safe = re.sub(r"[^a-zA-Z0-9-]", "-", socket.gethostname()).strip("-") or "printbridge"
    safe_queue = re.sub(r"[^a-zA-Z0-9-]", "-", queue).strip("-")
    return ServiceInfo(
        "_ipp._tcp.local.", f"{safe_queue}-PrintBridge._ipp._tcp.local.",
        addresses=[socket.inet_aton(ip)], port=631,
        properties={"txtvers": "1", "qtotal": "1", "rp": f"printers/{queue}",
                    "ty": queue, "pdl": "application/pdf", "priority": "0"},
        server=f"printbridge-{safe}.local.")


def main():
    zeroconf = Zeroconf()
    registered = {}
    try:
        while True:
            try:
                current = set(core.queues())
                for queue in set(registered) - current:
                    zeroconf.unregister_service(registered.pop(queue))
                for queue in current - set(registered):
                    info = description(queue)
                    zeroconf.register_service(info, allow_name_change=True)
                    registered[queue] = info
            except Exception as exc:
                print(f"DNS-SD announce retry: {exc}", flush=True)
            time.sleep(15)
    finally:
        zeroconf.close()


if __name__ == "__main__":
    main()
