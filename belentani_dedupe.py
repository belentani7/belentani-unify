#!/usr/bin/env python3
"""Descubre, deduplica (sha256) y consolida los HTML de Belentani del PC."""
import argparse
import csv
import hashlib
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime

HOME = os.path.expanduser("~")

ROOTS = [
    os.path.join(HOME, "Documents"),
    os.path.join(HOME, "Desktop"),
]

DRIVE_ROOT = os.path.join(HOME, "Videos", "DRIVE")

SKIP_DIR_MARKERS = [
    "\\node_modules\\", "\\.git\\", "\\AppData\\", "\\.cursor\\",
    "\\.cache\\", "\\site-packages\\", "\\.venv\\", "\\dist\\", "\\build\\",
]

TRASH_MARKERS = ["_trash_", "trash", "duplicate"]


def is_belentani(path: str) -> bool:
    p = path.lower()
    if "belentani" in os.path.basename(p):
        return True
    parts = p.split(os.sep)
    return any("belentani" in part for part in parts)


def sha256(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def walk_html(root):
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        low = (dirpath + os.sep).lower()
        dirnames[:] = [d for d in dirnames if not any(m in low + d.lower() + "\\" for m in SKIP_DIR_MARKERS)]
        for name in filenames:
            if name.lower().endswith(".html"):
                yield os.path.normpath(os.path.join(dirpath, name))


def find_html(drive=False):
    seen = set()
    roots = list(ROOTS)
    if drive:
        roots.append(DRIVE_ROOT)
    for root in roots:
        root = os.path.normpath(root)
        for full in walk_html(root):
            if full in seen:
                continue
            seen.add(full)
            if is_belentani(full):
                yield full
    for name in os.listdir(HOME):
        full = os.path.normpath(os.path.join(HOME, name))
        if full in seen or not os.path.isfile(full) or not name.lower().endswith(".html"):
            continue
        seen.add(full)
        if is_belentani(full):
            yield full


def score(path: str) -> tuple:
    p = path.lower()
    trash = 0 if any(t in p for t in TRASH_MARKERS) else 1
    local = 0 if "videos\\drive" in p else 1
    return (-trash, -local, -len(path), p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=r"Documents\Proyectos\belentani-unify")
    ap.add_argument("--copy", action="store_true")
    ap.add_argument("--drive", action="store_true")
    args = ap.parse_args()

    outdir = os.path.join(HOME, args.out) if not os.path.isabs(args.out) else args.out
    os.makedirs(outdir, exist_ok=True)

    groups = defaultdict(list)
    total = 0
    total_bytes = 0
    for i, f in enumerate(find_html(drive=args.drive), 1):
        try:
            h = sha256(f)
        except OSError:
            continue
        sz = os.path.getsize(f)
        groups[h].append((f, sz))
        total += 1
        total_bytes += sz
        if i % 200 == 0:
            print(f"  ... {i} HTML procesados", flush=True)

    winners = []
    dup_groups = 0
    for h, items in groups.items():
        items.sort(key=lambda it: score(it[0]))
        if len(items) > 1:
            dup_groups += 1
        winners.append({"hash": h[:12], "size": items[0][1], "keep": items[0][0],
                        "dups": [i[0] for i in items[1:]]})

    winners.sort(key=lambda w: w["keep"].lower())
    uniq_bytes = sum(w["size"] for w in winners)

    report = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "html_found": total,
        "html_total_mb": round(total_bytes / 1048576, 1),
        "unique_files": len(winners),
        "duplicate_groups": dup_groups,
        "unique_mb": round(uniq_bytes / 1048576, 1),
        "winners": winners,
    }
    with open(os.path.join(outdir, "belentani_html_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with open(os.path.join(outdir, "belentani_html_index.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["hash", "size_bytes", "keep_path", "dups_count", "dup_paths"])
        for it in winners:
            w.writerow([it["hash"], it["size"], it["keep"], len(it["dups"]), " | ".join(it["dups"])])

    print(f"HTML encontrados : {total}  ({round(total_bytes/1048576,1)} MB)")
    print(f"Archivos unicos  : {len(winners)}  ({round(uniq_bytes/1048576,1)} MB)")
    print(f"Grupos duplicados: {dup_groups}")
    print(f"Reporte          : {outdir}")

    if args.copy:
        dest = os.path.join(outdir, "html-source")
        os.makedirs(dest, exist_ok=True)
        used = set()
        copied = 0
        for it in winners:
            base = os.path.basename(it["keep"])
            stem, ext = os.path.splitext(base)
            name = base
            if name.lower() in used:
                name = f"{stem}__{it['hash']}{ext}"
            used.add(name.lower())
            try:
                shutil.copy2(it["keep"], os.path.join(dest, name))
                copied += 1
            except OSError as e:
                print(f"  ! {it['keep']}: {e}")
        print(f"Copiados a html-source: {copied}")


if __name__ == "__main__":
    main()
