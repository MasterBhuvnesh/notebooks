#!/usr/bin/env python3
"""Build every document in docs/ -- diagrams, PDF, changelog, README index.

The same script runs on a laptop and in CI, so there is exactly one build.

    python tools/build.py                 # every document, changed ones only
    python tools/build.py rabbitmq        # one document
    python tools/build.py --force         # ignore the hash cache
    python tools/build.py --new kafka     # creates the folder for a new book

Per document:
  1. .mmd -> .png with mermaid-cli, skipping sources whose hash is unchanged
  2. pdflatex twice (second pass resolves the TOC and page refs)
  3. verify: no LaTeX errors, no Overfull \\vbox, page count parsed from the log
  4. record hashes + stats in .build.json
  5. regenerate CHANGELOG.md from git history
Then rewrite the README index table from what is on disk.

A failed check is a failed build. Nothing here is best-effort.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SHARED = ROOT / "shared"
README = ROOT / "README.md"

INDEX_START = "<!-- INDEX:START -->"
INDEX_END = "<!-- INDEX:END -->"

# Where the browsers hide, once shutil.which has come up empty.
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


class BuildError(Exception):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


def git(*args: str) -> str:
    """git output, or '' if this is not a repo / has no commits yet."""
    p = run(["git", *args], ROOT)
    return p.stdout.strip() if p.returncode == 0 else ""


# --------------------------------------------------------------------------
# diagrams
# --------------------------------------------------------------------------

def find_chrome() -> str:
    """mermaid-cli drives puppeteer, which needs a browser it will not find itself.

    Env var wins (that is what CI sets), then PATH, then the usual install paths.
    Never download a second browser.
    """
    if env_path := os.environ.get("PUPPETEER_EXECUTABLE_PATH"):
        return env_path
    for name in ("chrome", "chromium", "chromium-browser", "google-chrome", "msedge"):
        if found := shutil.which(name):
            return found
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    raise BuildError(
        "No Chrome/Chromium found for mermaid rendering. Install one, or set "
        "PUPPETEER_EXECUTABLE_PATH to its executable."
    )


def puppeteer_config() -> Path:
    """Written at build time -- an executablePath committed to git is wrong
    on every machine but the one that wrote it."""
    cfg = ROOT / ".puppeteer.json"
    want = {"executablePath": find_chrome(), "args": ["--no-sandbox"]}
    if not cfg.exists() or json.loads(cfg.read_text()) != want:
        cfg.write_text(json.dumps(want, indent=2), newline="\n")
    return cfg


def render_diagrams(doc: Path, cache: dict, force: bool) -> dict[str, str]:
    """Render changed .mmd files, drop orphan .png files. Returns new hashes."""
    mmd_dir, png_dir = doc / "diagrams" / "mmd", doc / "diagrams" / "png"
    sources = sorted(mmd_dir.glob("*.mmd")) if mmd_dir.is_dir() else []
    hashes = {s.name: sha(s) for s in sources}

    # Delete only PNGs this build made earlier and no longer has a source for.
    # Anything not in the previous cache was put there by hand -- a screenshot,
    # a logo -- and is not ours to remove.
    stems = {s.stem for s in sources}
    ours = {Path(name).stem for name in cache.get("diagrams", {})}
    for stale_png in sorted(ours - stems):
        png = png_dir / f"{stale_png}.png"
        if png.exists():
            print(f"    - {png.name} (mermaid source gone, removed)")
            png.unlink()

    stale = [
        s for s in sources
        if force
        or cache.get("diagrams", {}).get(s.name) != hashes[s.name]
        or not (png_dir / f"{s.stem}.png").exists()
    ]
    if not stale:
        if sources:
            print(f"    diagrams: {len(sources)} up to date")
        return hashes

    png_dir.mkdir(parents=True, exist_ok=True)
    npx = shutil.which("npx")
    if not npx:
        raise BuildError("npx not found -- Node.js is required to render diagrams.")
    cfg = puppeteer_config()

    for src in stale:
        out = png_dir / f"{src.stem}.png"
        print(f"    rendering {src.name}")
        p = run([npx, "-y", "@mermaid-js/mermaid-cli",
                 "-i", str(src), "-o", str(out),
                 "-b", "white", "-s", "3", "-p", str(cfg)], ROOT)
        if p.returncode != 0 or not out.exists():
            raise BuildError(
                f"mermaid failed on {src.relative_to(ROOT)}:\n{p.stdout}\n{p.stderr}"
            )
    return hashes


# --------------------------------------------------------------------------
# LaTeX
# --------------------------------------------------------------------------

def compile_pdf(doc: Path) -> tuple[int, int]:
    """Two pdflatex passes, then verify the log. Returns (pages, bytes)."""
    env = dict(os.environ)
    # Trailing separator keeps the default search path -- without it TeX finds
    # nothing but shared/.
    env["TEXINPUTS"] = str(SHARED) + os.pathsep + env.get("TEXINPUTS", "")

    for pass_no in (1, 2):
        p = run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                doc, env)
        if p.returncode != 0:
            log = (doc / "main.log").read_text(errors="replace") if (doc / "main.log").exists() else p.stdout
            errors = "\n".join(l for l in log.splitlines() if l.startswith("!"))
            raise BuildError(f"pdflatex pass {pass_no} failed:\n{errors or p.stdout[-2000:]}")

    log = (doc / "main.log").read_text(errors="replace")

    if vboxes := log.count("Overfull \\vbox"):
        raise BuildError(
            f"{vboxes} Overfull \\vbox -- content is running off the bottom of a page. "
            "Shrink a diagram (\\mmd[0.30]{...}) or a listing (basicstyle=\\ttfamily\\scriptsize)."
        )

    m = re.findall(r"Output written on main\.pdf \((\d+) pages?, (\d+) bytes\)", log)
    if not m:
        raise BuildError("pdflatex produced no PDF (no 'Output written' in main.log).")
    pages, size = m[-1]
    return int(pages), int(size)


# --------------------------------------------------------------------------
# metadata: changelog + README index
# --------------------------------------------------------------------------

def title_of(doc: Path) -> str:
    m = re.search(r"\\notebooktitle\{(.+?)\}", (doc / "main.tex").read_text(errors="replace"))
    return m.group(1) if m else doc.name


def write_changelog(doc: Path, stats: dict) -> None:
    """Generated from git, wholesale, every build. Never hand-edit it.

    The build bot's own commits are filtered out, otherwise the changelog
    would fill up with the changelog being regenerated.
    """
    # --follow on main.tex, not the directory: renaming a book's folder must not
    # throw away its history. --follow only accepts a single path, hence main.tex.
    log = git("log", "--follow", "--date=short", "--format=%h%x1f%ad%x1f%an%x1f%s",
              "--", f"docs/{doc.name}/main.tex")
    rows = []
    for line in log.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        h, date, author, subject = parts
        if subject.startswith("chore(build)"):
            continue
        rows.append(f"| {date} | `{h}` | {subject} | {author} |")

    body = "\n".join(rows) if rows else "| - | - | _No commits recorded yet._ | - |"
    (doc / "CHANGELOG.md").write_text(
        f"# {title_of(doc)} - changelog\n\n"
        f"<!-- Generated by tools/build.py. Edits here are overwritten. -->\n\n"
        f"**Current build:** {stats['pages']} pages · {stats['bytes'] / 1024:.0f} KB · "
        f"{stats['diagram_count']} diagrams · built {stats['built_at']}"
        f"{' from `' + stats['commit'] + '`' if stats['commit'] else ''}\n\n"
        f"| Date | Commit | Change | Author |\n|---|---|---|---|\n{body}\n",
        # LF always: these files are regenerated on Windows and in a Linux
        # container, and CRLF drift would show up as a diff on every CI run.
        encoding="utf-8", newline="\n",
    )


def doc_dates(slug: str, stats: dict) -> tuple[str, str]:
    """(created, updated) from git, not the filesystem: a clone has no useful
    mtimes. An uncommitted document falls back to its build date."""
    history = git("log", "--follow", "--date=short", "--format=%ad", "--",
                  f"docs/{slug}/main.tex").splitlines()
    if not history:
        return stats["built_at"][:10], stats["built_at"][:10]
    return history[-1], history[0]


def write_manifest(all_stats: dict[str, dict]) -> None:
    """docs/index.json: the whole shelf as data. Feeds the README badges via
    shields.io, and is the thing to read from anywhere else that wants the list."""
    books = []
    for slug in sorted(all_stats):
        s = all_stats[slug]
        created, updated = doc_dates(slug, s)
        books.append({
            "slug": slug,
            "title": s["title"],
            "pages": s["pages"],
            "bytes": s["bytes"],
            "diagrams": s["diagram_count"],
            "created": created,
            "updated": updated,
            "pdf": f"docs/{slug}/main.pdf",
        })
    # Top-level "books"/"pages" are scalars so a shields.io dynamic badge can
    # point straight at $.books and $.pages.
    (DOCS / "index.json").write_text(
        json.dumps({
            "books": len(books),
            "pages": sum(b["pages"] for b in books),
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "documents": books,
        }, indent=2),
        encoding="utf-8", newline="\n",
    )


def update_readme(all_stats: dict[str, dict]) -> None:
    """Rewrite the table between the INDEX markers. Hand-maintained index
    tables rot; this one cannot."""
    if not README.exists():
        return
    text = README.read_text(encoding="utf-8")
    if INDEX_START not in text or INDEX_END not in text:
        print("  ! README has no INDEX markers, skipping index")
        return

    # :---: centres the cells; the <div align="center"> around the markers in
    # README.md centres the table itself and is preserved across regeneration.
    rows = [
        "| Book | Created | Updated | PDF |",
        "| :---: | :---: | :---: | :---: |",
    ]
    for slug in sorted(all_stats):
        s = all_stats[slug]
        created, updated = doc_dates(slug, s)
        rows.append(
            f"| {s['title']} | {created} | {updated} | "
            f"[pdf](docs/{slug}/main.pdf) |"
        )

    head, _, rest = text.partition(INDEX_START)
    _, _, tail = rest.partition(INDEX_END)
    README.write_text(
        f"{head}{INDEX_START}\n\n" + "\n".join(rows) + f"\n\n{INDEX_END}{tail}",
        encoding="utf-8", newline="\n",
    )


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------

def build_doc(doc: Path, force: bool) -> dict:
    print(f"  {doc.name}")
    cache_file = doc / ".build.json"
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}

    diagram_hashes = render_diagrams(doc, cache, force)
    tex_hash = sha(doc / "main.tex")
    sty_hash = sha(SHARED / "notebooks.sty")

    unchanged = (
        not force
        and cache.get("tex") == tex_hash
        and cache.get("sty") == sty_hash
        and cache.get("diagrams") == diagram_hashes
        and (doc / "main.pdf").exists()
    )
    if unchanged:
        print(f"    up to date ({cache['pages']} pages)")
        stats = cache
    else:
        pages, size = compile_pdf(doc)
        stats = {
            "title": title_of(doc),
            "tex": tex_hash,
            "sty": sty_hash,
            "diagrams": diagram_hashes,
            "diagram_count": len(diagram_hashes),
            "pages": pages,
            "bytes": size,
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "commit": git("rev-parse", "--short", "HEAD"),
        }
        cache_file.write_text(json.dumps(stats, indent=2, sort_keys=True), newline="\n")
        print(f"    built {pages} pages, {size / 1024:.0f} KB")

    stats["title"] = title_of(doc)
    write_changelog(doc, stats)
    return stats


NEW_TEX = r"""\documentclass[11pt,a4paper]{article}
\usepackage{notebooks}

\notebooktitle{<<TITLE>>}
\notebooksubtitle{}
\notebooktagline{}
\notebookauthor{}

\begin{document}
\notebookcover

\section{First topic}

\field{Short description:}{One or two sentences, what it is.}

% Diagrams: write diagrams/mmd/01-name.mmd, then reference the PNG the build
% renders from it -- never run mermaid-cli by hand.
% \mmd{01-name.png}

\end{document}
"""


def scaffold(slug: str) -> None:
    """One book, one folder under docs/. The slug is the book's name in
    kebab-case, no date prefix: docs/rabbitmq, docs/kafka, docs/redis."""
    doc = DOCS / slug
    if doc.exists():
        raise BuildError(f"docs/{slug} already exists.")
    (doc / "diagrams" / "mmd").mkdir(parents=True)
    (doc / "diagrams" / "png").mkdir(parents=True)
    title = slug.replace("-", " ").title()
    # .replace, not %-formatting: the template is full of LaTeX % comments.
    (doc / "main.tex").write_text(NEW_TEX.replace("<<TITLE>>", title),
                                  encoding="utf-8", newline="\n")
    print(f"Created docs/{slug}/main.tex - write it, then: python tools/build.py {slug}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slugs", nargs="*", help="document directories under docs/ (default: all)")
    ap.add_argument("--force", action="store_true", help="rebuild even if nothing changed")
    ap.add_argument("--new", metavar="SLUG", help="scaffold a new document and exit")
    args = ap.parse_args()

    try:
        if args.new:
            scaffold(args.new)
            return 0

        DOCS.mkdir(exist_ok=True)
        docs = [DOCS / s for s in args.slugs] if args.slugs else \
            sorted(d for d in DOCS.iterdir() if (d / "main.tex").exists())
        for d in docs:
            if not (d / "main.tex").exists():
                raise BuildError(f"{d} has no main.tex")

        if not docs:
            print("No documents in docs/. Start one with: python tools/build.py --new kafka")
            return 0

        print(f"Building {len(docs)} document(s)")
        stats = {d.name: build_doc(d, args.force) for d in docs}

        # The index and the manifest describe the whole shelf, so building one
        # book must not drop the others: fill the gaps from their build cache.
        shelf = dict(stats)
        for d in sorted(DOCS.iterdir()):
            cached = d / ".build.json"
            if d.name not in shelf and cached.exists():
                shelf[d.name] = json.loads(cached.read_text())
        write_manifest(shelf)
        update_readme(shelf)
        print(f"OK - {sum(s['pages'] for s in stats.values())} pages total")
        return 0
    except BuildError as e:
        print(f"\nBUILD FAILED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
