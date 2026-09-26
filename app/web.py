"""Small LAN-only printer administration and Android PDF page, no JS/framework."""
import base64
import binascii
import hmac
import html
import os
import secrets
import subprocess
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import core

PASSWORD = os.environ["PRINTBRIDGE_ADMIN_PASSWORD"]
CSRF = secrets.token_urlsafe(32)
MAX_BODY = 20 * 1024 * 1024


def esc(value):
    return html.escape(str(value), quote=True)


def page(title, body):
    return ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{esc(title)}</title><style>body{{font:1rem system-ui;max-width:760px;"
            "margin:2rem auto;padding:0 1rem;line-height:1.5}}label{display:block;margin:1rem 0}"
            "input,select,button{font:inherit;max-width:100%;padding:.5rem}"
            "input[type=text]{width:95%}button{cursor:pointer}li{margin:.7rem 0}"
            "small{display:block}nav a{margin-right:1rem}</style>"
            "<nav><a href='/'>Manage printers</a><a href='/mobile'>Print PDF from your phone</a></nav>"
            f"<h1>{esc(title)}</h1>{body}</html>").encode()


class Handler(BaseHTTPRequestHandler):
    def send_page(self, title, body, status=200):
        content = page(title, body)
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def admin_authorized(self):
        auth = self.headers.get("Authorization", "")
        try:
            scheme, encoded = auth.split(" ", 1)
            userpass = base64.b64decode(encoded, validate=True).decode("utf-8")
            user, password = userpass.split(":", 1)
            valid = (scheme.lower() == "basic" and user == "admin"
                     and hmac.compare_digest(password, PASSWORD))
        except (ValueError, UnicodeDecodeError, binascii.Error):
            valid = False
        if not valid:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="PrintBridge administration"')
            self.send_header("Content-Length", "0")
            self.end_headers()
        return valid

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/health":
            self.send_page("Status", "CUPS is running.")
            return
        if url.path == "/mobile":
            options = "".join(f"<option value='{esc(q)}'>{esc(q)}</option>" for q in core.queues())
            self.send_page("Print a PDF from Android", "<p>Select a PDF on your phone."
                " Your phone and print server must be on the same local network.</p>"
                "<form method='post' action='/mobile' enctype='multipart/form-data'>"
                f"<label>Printer <select name='queue' required>{options}</select></label>"
                "<label>PDF <input type='file' name='pdf' accept='application/pdf' required></label>"
                "<button>Print</button></form><p>This is a PDF upload option."
                " Android's built-in Print menu requires separate compatibility testing.</p>")
            return
        if not self.admin_authorized():
            return
        try:
            if url.path == "/":
                current = core.queues()
                rows = "".join("<li>" + esc(q) +
                    " <form method='post' action='/test' style='display:inline'>"
                    f"<input type='hidden' name='csrf' value='{CSRF}'>"
                    f"<input type='hidden' name='name' value='{esc(q)}'>"
                    "<button>Test page</button></form>"
                    f"<small>Windows: http://SERVER-IP:631/printers/{esc(q)}</small></li>"
                    for q in current)
                self.send_page("My printers", "<p>Adding a printer preserves existing queues.</p>"
                    f"<ul>{rows or '<li>No printers yet.</li>'}</ul>"
                    "<p><a href='/add'>Add printer</a></p>")
            elif url.path == "/add":
                query = parse_qs(url.query).get("search", [""])[0][:80]
                devices = core.usb_devices()
                opts = "".join(f"<option value='{esc(u)}'>{esc(u)}</option>" for u in devices)
                matches = [(key, label) for key, label in core.models().items()
                           if query.lower() in label.lower()]
                matches = matches[:80] if query else []
                modelopts = "".join(f"<option value='{esc(k)}'>{esc(label)}</option>"
                                    for k, label in matches)
                body = ("<p>Step 1: Name the printer. Step 2: Select USB or enter"
                    " a network address. Step 3: Choose a driver.</p>"
                    "<form method='get' action='/add'><label>Search manufacturer or model "
                    f"<input type='text' name='search' value='{esc(query)}'></label>"
                    "<button>Search drivers</button></form>"
                    "<form method='post' action='/add'>"
                    f"<input type='hidden' name='csrf' value='{CSRF}'>"
                    "<label>Queue name <input type='text' name='name' required placeholder='OfficePrinter'></label>"
                    f"<label>USB printer <select name='usb'><option value=''>None</option>{opts}</select></label>"
                    "<label>OR network address <input type='text' name='uri' "
                    "placeholder='ipp://192.168.0.60/ipp/print'></label>"
                    "<label>Driver <select name='model' required>"
                    "<option value=''>Choose a model</option>"
                    "<option value='everywhere'>Driverless IPP (IPP network printers only)</option>"
                    f"{modelopts}</select></label>"
                    "<p>Can't find the model? Search above. Verify the selected"
                    " driver with a physical print.</p><button>Add printer</button></form>")
                self.send_page("Add printer", body)
            else:
                self.send_page("Not found", "Unknown address.", 404)
        except subprocess.CalledProcessError as exc:
            self.send_page("Printer error", f"<p>CUPS could not list printers: {esc(exc.stderr)}</p>", 500)

    def read_body(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size <= 0 or size > MAX_BODY:
            raise ValueError("The file or form is too large (20 MB maximum).")
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc != self.headers.get("Host"):
            raise ValueError("Unexpected origin address.")
        return self.rfile.read(size)

    def do_POST(self):
        url = urlsplit(self.path)
        if url.path != "/mobile" and not self.admin_authorized():
            return
        try:
            body = self.read_body()
            if url.path == "/mobile":
                content_type = self.headers.get("Content-Type", "")
                if not content_type.startswith("multipart/form-data;"):
                    raise ValueError("Expected a PDF upload.")
                message = BytesParser(policy=policy.default).parsebytes(
                    ("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + body)
                parts = {part.get_param("name", header="content-disposition"): part
                         for part in message.iter_parts()}
                if "queue" not in parts or "pdf" not in parts:
                    raise ValueError("Select both a printer and a PDF.")
                name = parts["queue"].get_payload(decode=True).decode("utf-8")
                pdf = parts["pdf"].get_payload(decode=True)
                if pdf is None:
                    raise ValueError("Select a PDF file.")
                result = core.print_pdf(name, pdf)
                self.send_page("Job submitted", f"<p>{esc(result)}</p><a href='/mobile'>Print another PDF</a>")
                return
            values = parse_qs(body.decode("utf-8"), keep_blank_values=True)
            get = lambda key: values.get(key, [""])[0]
            if not hmac.compare_digest(get("csrf"), CSRF):
                raise ValueError("The form expired. Reload the page.")
            if url.path == "/add":
                name = get("name").strip()
                core.add_queue(name, get("usb") or get("uri").strip(), get("model"))
                self.send_page("Printer added", f"<p>{esc(name)} was added.</p>"
                               "<p>Print a test page from the overview.</p><a href='/'>My printers</a>")
            elif url.path == "/test":
                core.test_page(get("name"))
                self.send_page("Test page submitted", "<p>Confirm that a physical page comes out.</p>"
                               "<a href='/'>My printers</a>")
            else:
                self.send_page("Not found", "Unknown address.", 404)
        except (ValueError, UnicodeDecodeError, subprocess.CalledProcessError) as exc:
            self.send_page("Could not complete action", f"<p>{esc(exc)}</p>"
                           "<p>No existing printers were deleted.</p>", 400)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
