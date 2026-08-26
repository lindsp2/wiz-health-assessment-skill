#!/usr/bin/env python3
"""
Local, credential-free PPTX -> PDF conversion.
================================================
Provides a zero-Google path to produce the executive PDF from the locally
generated .pptx, using a LibreOffice headless install if one is present.

This closes the gap where `--format pdf` previously required Google Slides:
when Google credentials are absent, generate_deck.py builds the local .pptx and
then calls convert_pptx_to_pdf() here to render the PDF offline.
"""

import os
import re
import shutil
import subprocess
import sys
import zipfile
from io import BytesIO
from pathlib import Path


def find_libreoffice():
    """Locate a LibreOffice/soffice binary across platforms. Returns path or None."""
    # 1) Honor an explicit override.
    override = os.environ.get("LIBREOFFICE_PATH")
    if override and Path(override).exists():
        return override

    # 2) Anything already on PATH.
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found

    # 3) Common fixed install locations per OS.
    candidates = []
    if sys.platform == "darwin":
        candidates.append("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    elif sys.platform.startswith("win"):
        candidates += [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
    else:  # linux / other unix
        candidates += [
            "/usr/bin/soffice",
            "/usr/bin/libreoffice",
            "/snap/bin/libreoffice",
            "/opt/libreoffice/program/soffice",
        ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


INSTALL_HINTS = {
    "linux": "sudo apt-get install -y libreoffice-impress   # Debian/Ubuntu\n"
             "    sudo dnf install -y libreoffice-impress       # Fedora/RHEL\n"
             "    sudo snap install libreoffice                  # any distro (snap)",
    "darwin": "brew install --cask libreoffice                # Homebrew\n"
              "    (or download from https://www.libreoffice.org/download/)",
    "win32": "winget install TheDocumentFoundation.LibreOffice   # winget\n"
             "    choco install libreoffice-fresh                    # Chocolatey\n"
             "    (or download from https://www.libreoffice.org/download/)",
}


def install_hint():
    key = "darwin" if sys.platform == "darwin" else ("win32" if sys.platform.startswith("win") else "linux")
    return INSTALL_HINTS[key]


# PowerPoint's default bullet hanging-indent (0.25" in EMU). The Wiz template
# defines bullets as a large "●" (U+25CF) with marL=0/indent=0, which PowerPoint
# renders small with spacing but LibreOffice renders oversized and glued to the
# text. We normalize ONLY those paragraphs for the LibreOffice render so the PDF
# matches the PowerPoint export. Applied to a temp copy — the source .pptx keeps
# its exact original formatting (so a later PowerPoint export is unaffected).
_BULLET_INDENT_EMU = 228600


def _dominant_hyperlink_color(src):
    """Most common explicit run color on hyperlink (<a:hlinkClick>) runs across all
    slides. Returns a 6-hex string or None. LibreOffice ignores a hyperlink run's
    own color and paints it with the THEME's hyperlink color, so to honor the
    deck's link color we copy this into the theme (see _normalize_for_libreoffice)."""
    from collections import Counter
    counts = Counter()
    for name in src.namelist():
        if re.match(r"ppt/slides/slide\d+\.xml$", name):
            x = src.read(name).decode("utf-8", "ignore")
            for r in re.findall(r"<a:r>.*?</a:r>", x, re.S):
                if "hlinkClick" in r:
                    m = re.search(r'<a:solidFill><a:srgbClr val="([0-9A-Fa-f]{6})"', r)
                    if m:
                        counts[m.group(1).upper()] += 1
    return counts.most_common(1)[0][0] if counts else None


def _normalize_for_libreoffice(pptx_path):
    """Write a temp copy of the .pptx tuned for the LibreOffice renderer:
      1. Bullet paragraphs: swap the oversized '●' glyph for '•' and add a hanging
         indent (LibreOffice renders the template's marL=0/indent=0 bullets glued).
      2. Hyperlink color: LibreOffice restyles hyperlink runs and repaints them dark
         (black), overriding the run's explicit color — but only for links that sit
         mid-paragraph next to other runs, which is why some links come out black and
         others don't. We ensure each link run carries the deck's link color, then
         remove the hyperlink relationship so LibreOffice stops restyling it. The
         text keeps its color + underline; it just isn't clickable in this PDF.
    The source .pptx is untouched (PowerPoint keeps clickable, correctly-colored
    links); returns the temp path, or the original path if nothing needed changing."""
    try:
        src = zipfile.ZipFile(pptx_path)
    except Exception:
        return pptx_path

    link_color = _dominant_hyperlink_color(src)

    def fix_para(p):
        # Only real bulleted paragraphs that use the oversized glyph with no indent.
        if "<a:buChar" not in p:
            return p

        def repl_ppr(m):
            tag = m.group(0)
            # Only retarget the glued case (marL=0 & indent=0); leave intentional
            # indentation (nested levels, custom margins) untouched.
            if 'marL="0"' in tag and 'indent="0"' in tag:
                tag = tag.replace('marL="0"', f'marL="{_BULLET_INDENT_EMU}"')
                tag = tag.replace('indent="0"', f'indent="-{_BULLET_INDENT_EMU}"')
            return tag

        p = re.sub(r"<a:pPr\b[^>]*>", repl_ppr, p, count=1)
        p = p.replace('<a:buChar char="●"/>', '<a:buChar char="•"/>')
        return p

    def fix_hyperlinks(x):
        def per_run(m):
            r = m.group(0)
            if "hlinkClick" not in r:
                return r
            # Guarantee the link color survives: if this run has no explicit fill,
            # inject the deck's link color right after the rPr open tag.
            if link_color and "<a:solidFill>" not in r:
                r = re.sub(
                    r"(<a:rPr\b[^>]*>)",
                    rf'\1<a:solidFill><a:srgbClr val="{link_color}"/></a:solidFill>',
                    r, count=1,
                )
            # Drop the hyperlink relationship so LibreOffice stops repainting it dark.
            r = re.sub(r"<a:hlinkClick[^>]*?/>", "", r)
            r = re.sub(r"<a:hlinkClick.*?</a:hlinkClick>", "", r, flags=re.S)
            return r

        return re.sub(r"<a:r>.*?</a:r>", per_run, x, flags=re.S)

    changed = False
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in src.infolist():
            data = src.read(item.filename)
            if re.match(r"ppt/slides/slide\d+\.xml$", item.filename):
                x = data.decode("utf-8")
                nx = re.sub(r"<a:p>.*?</a:p>", lambda m: fix_para(m.group(0)), x, flags=re.S)
                nx = fix_hyperlinks(nx)
                if nx != x:
                    changed = True
                    data = nx.encode("utf-8")
            zout.writestr(item, data)
    src.close()

    if not changed:
        return pptx_path
    tmp = str(Path(pptx_path).with_suffix(".lo-render.pptx"))
    with open(tmp, "wb") as f:
        f.write(buf.getvalue())
    return tmp


def convert_pptx_to_pdf(pptx_path, output_pdf, timeout=300):
    """
    Convert a .pptx to .pdf locally via LibreOffice headless. No Google, no network.

    Returns (True, message) on success, (False, actionable_message) on failure.
    Never raises — the caller decides how to surface the result.
    """
    pptx_path = str(pptx_path)
    output_pdf = str(output_pdf)

    if not os.path.exists(pptx_path):
        return False, f"Source PPTX not found: {pptx_path}"

    soffice = find_libreoffice()
    if not soffice:
        return False, (
            "LibreOffice was not found, so the PDF could not be rendered locally.\n"
            "    Install it once (free, no account, fully offline), then re-run:\n\n"
            f"    {install_hint()}\n\n"
            "    Or set LIBREOFFICE_PATH in your .env to an existing soffice binary."
        )

    out_dir = str(Path(output_pdf).resolve().parent)
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # Render a normalized copy (bullets + hyperlink color) so LibreOffice matches
    # the PowerPoint export.
    render_src = _normalize_for_libreoffice(pptx_path)

    # LibreOffice writes <sourcename>.pdf into --outdir; we rename to output_pdf after.
    cmd = [
        soffice, "--headless", "--norestore", "--nolockcheck",
        "--convert-to", "pdf:impress_pdf_Export",
        "--outdir", out_dir, render_src,
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            # A dedicated profile dir avoids clashes with a running desktop LibreOffice.
            env={**os.environ, "HOME": os.environ.get("HOME", out_dir)},
        )
    except subprocess.TimeoutExpired:
        return False, f"LibreOffice conversion timed out after {timeout}s."
    except Exception as e:  # pragma: no cover - defensive
        return False, f"LibreOffice invocation failed: {e}"
    finally:
        # Remove the temp normalized copy (only if we actually created one).
        if render_src != pptx_path:
            try:
                os.remove(render_src)
            except OSError:
                pass

    produced = Path(out_dir) / (Path(render_src).stem + ".pdf")
    if not produced.exists():
        return False, (
            "LibreOffice ran but produced no PDF.\n"
            f"    stdout: {proc.stdout.strip()[:500]}\n"
            f"    stderr: {proc.stderr.strip()[:500]}"
        )

    if str(produced) != str(Path(output_pdf)):
        shutil.move(str(produced), output_pdf)

    size = os.path.getsize(output_pdf)
    return True, f"{output_pdf} ({size:,} bytes) via LibreOffice ({soffice})"


if __name__ == "__main__":
    # Standalone helper: python3 local_pdf.py <deck.pptx> [out.pdf]
    if len(sys.argv) < 2:
        print("usage: python3 local_pdf.py <deck.pptx> [out.pdf]")
        sys.exit(2)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else str(Path(src).with_suffix(".pdf"))
    ok, msg = convert_pptx_to_pdf(src, dst)
    print(("[✓] " if ok else "[!] ") + msg)
    sys.exit(0 if ok else 1)
