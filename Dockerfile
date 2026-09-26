# Build upstream brlaser in a temporary stage. Pin the v6 commit.
FROM debian:13-slim AS brlaser-builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git cmake make g++ libcups2-dev libcupsimage2-dev \
    && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/pdewacht/brlaser.git /src/brlaser \
    && cd /src/brlaser \
    && git checkout --detach 23117fe9e0266396e4791cdae84d979928aed135 \
    && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build -j2 \
    && ctest --test-dir build --output-on-failure \
    && DESTDIR=/brlaser-install cmake --install build

FROM debian:13-slim
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    cups cups-client cups-filters ghostscript python3 python3-zeroconf usbutils \
    libcupsimage2t64 printer-driver-gutenprint printer-driver-foo2zjs \
    && rm -rf /var/lib/apt/lists/*
COPY --from=brlaser-builder /brlaser-install/usr/ /usr/
COPY app /opt/printbridge
RUN chmod +x /opt/printbridge/start.sh \
    && test -x /usr/lib/cups/filter/rastertobrlaser \
    && test -f /usr/share/cups/drv/brlaser.drv
VOLUME ["/etc/cups", "/var/spool/cups"]
EXPOSE 631 8080
ENTRYPOINT ["/opt/printbridge/start.sh"]
