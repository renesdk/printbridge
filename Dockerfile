FROM debian:13-slim
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    cups cups-client cups-filters ghostscript python3 python3-zeroconf usbutils \
    printer-driver-gutenprint printer-driver-brlaser printer-driver-foo2zjs \
    && rm -rf /var/lib/apt/lists/*
COPY app /opt/printbridge
RUN chmod +x /opt/printbridge/start.sh
VOLUME ["/etc/cups", "/var/spool/cups"]
EXPOSE 631 8080
ENTRYPOINT ["/opt/printbridge/start.sh"]
