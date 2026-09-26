"""Small, testable boundary between the web UI and CUPS."""
import re
import subprocess

QUEUE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,62}\Z")
URI = re.compile(r"(?:usb|ipp|ipps|socket|lpd)://[^\s]+\Z", re.I)


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def models():
    result = {}
    for line in run("lpinfo", "-m").splitlines():
        key, sep, label = line.partition(" ")
        if sep:
            result[key] = label.strip()
    return result


def usb_devices():
    return [line.split(None, 1)[1] for line in run("lpinfo", "-v").splitlines()
            if len(line.split(None, 1)) == 2 and line.split(None, 1)[1].startswith("usb://")]


def queues():
    result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True)
    if result.returncode and "No destinations added" not in result.stderr + result.stdout:
        result.check_returncode()
    return [match.group(1) for line in result.stdout.splitlines()
            if (match := re.match(r"printer (\S+) ", line))]


def add_queue(name, uri, model):
    if not QUEUE.fullmatch(name):
        raise ValueError("Invalid name. Use letters, digits, _ or -; start with a letter.")
    if not URI.fullmatch(uri):
        raise ValueError("Invalid printer address.")
    if name in queues():
        raise ValueError("This queue name is already in use. Existing printers were not changed.")
    if uri.startswith("usb://") and uri not in usb_devices():
        raise ValueError("The app cannot see this USB printer. Check USB access in TrueNAS.")
    if model == "everywhere":
        if not uri.startswith(("ipp://", "ipps://")):
            raise ValueError("Driverless IPP requires an ipp:// or ipps:// address.")
    elif model not in models():
        raise ValueError("Select a model from the list. That driver is not installed.")
    run("lpadmin", "-p", name, "-E", "-v", uri, "-m", model,
        "-o", "printer-is-shared=true", "-o", "PageSize=A4")
    run("cupsaccept", name)
    run("cupsenable", name)


def test_page(name):
    if name not in queues():
        raise ValueError("Printer not found.")
    run("lp", "-d", name, "/usr/share/cups/data/testprint")


def print_pdf(name, data):
    if name not in queues():
        raise ValueError("Printer not found.")
    if not data.startswith(b"%PDF-"):
        raise ValueError("Select a PDF file.")
    result = subprocess.run(["lp", "-d", name, "-"], input=data,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout.decode("utf-8", "replace")
