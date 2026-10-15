#!/usr/bin/env python3
"""Render cv.html to a text-based A4 PDF with headless Firefox (Marionette).

Usage:  python3 tools/cv_pdf.py [output.pdf]
Default output: Lebenslauf_Tobias_Barth.pdf in the repo root.
Needs only Firefox (also the snap package) - no extra Python packages.
"""
import base64
import json
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "cv.html"
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "Lebenslauf_Tobias_Barth.pdf"


# Google Fonts serves Bricolage Grotesque and Schibsted Grotesk as variable
# fonts. Firefox's PDF backend can't embed non-default instances of those and
# draws them as outlines -> name, headings and company names would not be
# extractable for applicant tracking systems. For the PDF only, swap in static
# instances of the same families (Fontsource) and disable ligatures, whose
# glyphs have no text mapping ("Konfigurator" would come out as "Kon?gurator").
FONTSOURCE = "https://cdn.jsdelivr.net/npm/@fontsource/{pkg}@5.3.0/files/{pkg}-latin-{w}-normal.woff2"
PDF_FONTS = {"PDF Bricolage": ("bricolage-grotesque", (500, 700, 800)),
             "PDF Schibsted": ("schibsted-grotesk", (400, 500, 600))}
PDF_CSS = "".join(
    f'@font-face{{font-family:"{fam}";font-weight:{w};'
    f'src:url({FONTSOURCE.format(pkg=pkg, w=w)}) format("woff2")}}'
    for fam, (pkg, weights) in PDF_FONTS.items() for w in weights
) + (':root{--disp:"PDF Bricolage",sans-serif;--sans:"PDF Schibsted",system-ui,sans-serif}'
     '*{font-variant-ligatures:none!important}')
PDF_FONT_LOADS = [f'{w} 12px "{fam}"' for fam, (_, weights) in PDF_FONTS.items() for w in weights]


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Marionette:
    """Minimal client for Firefox's Marionette protocol (length-prefixed JSON)."""

    def __init__(self, port):
        for _ in range(150):
            try:
                self.sock = socket.create_connection(("127.0.0.1", port), timeout=60)
                break
            except OSError:
                time.sleep(0.2)
        else:
            raise SystemExit("Firefox/Marionette did not start")
        self.buf = b""
        self.msg_id = 0
        self._read()  # server handshake

    def _read(self):
        while b":" not in self.buf:
            self.buf += self.sock.recv(65536)
        length, rest = self.buf.split(b":", 1)
        length = int(length)
        while len(rest) < length:
            rest += self.sock.recv(1 << 20)
        self.buf = rest[length:]
        return json.loads(rest[:length])

    def cmd(self, name, params=None):
        self.msg_id += 1
        data = json.dumps([0, self.msg_id, name, params or {}]).encode()
        self.sock.sendall(str(len(data)).encode() + b":" + data)
        _, _, error, result = self._read()
        if error:
            raise SystemExit(f"{name} failed: {error}")
        return result


def main():
    port = free_port()
    # Snap-packaged Firefox can't read /tmp or hidden dirs, so the throwaway
    # profile lives in a visible folder in $HOME and is removed afterwards.
    profile = pathlib.Path(tempfile.mkdtemp(prefix="cv-pdf-profile-", dir=pathlib.Path.home()))
    (profile / "user.js").write_text(f'user_pref("marionette.port", {port});\n')
    firefox = subprocess.Popen(
        ["firefox", "--headless", "--marionette", "--no-remote", "--profile", str(profile)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        m = Marionette(port)
        m.cmd("WebDriver:NewSession", {"capabilities": {}})
        m.cmd("WebDriver:Navigate", {"url": SRC.as_uri()})
        # Inject the static-font override and wait until every font is loaded.
        loaded = m.cmd("WebDriver:ExecuteAsyncScript", {
            "script": """
                const [css, loads, done] = arguments;
                const style = document.createElement('style');
                style.textContent = css;
                document.head.appendChild(style);
                document.body.offsetHeight;
                Promise.all(loads.map(f => document.fonts.load(f)))
                  .then(() => document.fonts.ready)
                  .then(() => done(loads.every(f => document.fonts.check(f))));
            """,
            "args": [PDF_CSS, PDF_FONT_LOADS],
        })
        if not loaded.get("value"):
            raise SystemExit("static PDF fonts did not load (offline?)")
        time.sleep(0.5)
        result = m.cmd("WebDriver:Print", {
            "orientation": "portrait",
            "scale": 1,
            "background": True,
            "page": {"width": 21.0, "height": 29.7},
            "margin": {"top": 0, "bottom": 0, "left": 0, "right": 0},
            "shrinkToFit": False,
        })
        OUT.write_bytes(base64.b64decode(result["value"]))
        print(f"wrote {OUT}")
    finally:
        firefox.terminate()
        try:
            firefox.wait(timeout=15)
        except subprocess.TimeoutExpired:
            firefox.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
