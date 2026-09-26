# PrintBridge

A small CUPS-based print server prototype for TrueNAS SCALE 25.10 Custom Apps.
Add a USB or network printer in the web UI; add more printers later without
resetting existing queues. Print PDFs from an Android phone through the mobile
web page. Windows clients can connect using a CUPS IPP queue.

**Status: pre-release prototype.** The upstream brlaser variant has not been
built or physically verified here. In one TrueNAS HL-2035 test, the USB device
disconnected during print; using upstream brlaser may not resolve that fault.
A successful build or a listed driver does not establish compatibility.

## Start here

Follow the [complete beginner installation guide](docs/INSTALLATION.md). It
covers source upload, an automated GitHub image build, GHCR visibility, the
TrueNAS Custom App YAML, printer setup, and physical Windows/Android tests.
GitHub builds the image. The end user does not compile it on the NAS.

Already running `v0.1.0`? Follow the [upstream brlaser upgrade guide](docs/UPGRADE-UPSTREAM-BRLASER.md).

## Included features

- CUPS, Gutenprint, foo2zjs, and upstream brlaser v6, built from the pinned
  [pdewacht/brlaser](https://github.com/pdewacht/brlaser) commit
  `23117fe9e0266396e4791cdae84d979928aed135`, in one container. The
  build tools are left behind in a separate build stage.
- A small English web UI at port 8080 to add queues and send test pages.
- Existing queues persist under `/etc/cups`; pending jobs under `/var/spool/cups`.
- PDF upload from a phone at `/mobile`, limited to 20 MB.
- Shared IPP queues on port 631, plus experimental DNS-SD/mDNS advertising when
  `PRINTBRIDGE_ADVERTISE_IP` is set and the container uses host networking.
- A GitHub Actions workflow to build a tagged GHCR image. This repository does
  not include a published image or a listing in the TrueNAS app catalog.

The mobile PDF page is **not** proof that Android's built-in Print menu works.
Test the latter separately and report phone model, Android version, printer
model, network layout, and what happened. Do not claim Mopria certification.

## Developer-only local test

On a Linux host with Docker Engine and Compose, put
`PRINTBRIDGE_ADMIN_PASSWORD=YOUR_LONG_UNIQUE_PASSWORD` in a private `.env` file
in the repository root. Run
`docker compose -f compose.development.yaml up -d --build`. Open
`http://HOST-IP:8080/` as user `admin`, add a printer, and confirm a physical
test page. For Android PDF upload use `http://HOST-IP:8080/mobile`; for Windows
use `http://HOST-IP:631/printers/QUEUE_NAME`. These commands are for project
development, not the beginner installation path.

## Before a stable release

Complete the [physical acceptance plan](docs/TESTPLAN.md), especially USB
reconnection, Windows 11 and native Android printing, update/rollback, and
idle/peak CPU and RAM measurements. A `512m` memory cap is only a starting
point. A very low cap can terminate a large PDF job.

## Security boundary

The prototype uses HTTP Basic authentication for administration on a trusted
LAN. The password is in the installed app YAML. The mobile PDF page and IPP
printing are available to LAN clients. Do **not** forward TCP 631 or 8080 to
the Internet. Authentication/TLS and stronger access control must be addressed
before a general public release. Vendor-only drivers and firmware-dependent
models are outside the initial scope.
