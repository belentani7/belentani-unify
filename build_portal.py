#!/usr/bin/env python3
"""Genera el portal unificado (index.html) y el manifiesto a partir del reporte."""
import html
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "html-source")

with open(os.path.join(HERE, "belentani_html_report.json"), encoding="utf-8") as f:
    rep = json.load(f)

rows = []
used = set()
for w in rep["winners"]:
    base = os.path.basename(w["keep"])
    stem, ext = os.path.splitext(base)
    name = base
    if name.lower() in used:
        name = f"{stem}__{w['hash']}{ext}"
    used.add(name.lower())
    rows.append((name, w["size"], w["keep"]))
rows.sort(key=lambda r: r[0].lower())

items = "\n".join(
    f'<li data-n="{html.escape(n.lower())}"><a href="html-source/{n}" target="_blank">{html.escape(n)}</a>'
    f'<span class="sz">{s/1048576:.2f} MB</span></li>'
    for n, s, _ in rows
)

page = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Belentani Unified - Portal ({len(rows)} HTML)</title>
<style>
:root{{--bg:#0a0b10;--fg:#e8e6ff;--accent:#7c5cff;--card:#141624}}
*{{box-sizing:border-box}}
body{{margin:0;font:15px/1.5 system-ui,Segoe UI,sans-serif;background:var(--bg);color:var(--fg)}}
header{{padding:28px 24px;border-bottom:1px solid #22263a;position:sticky;top:0;background:rgba(10,11,16,.92);backdrop-filter:blur(8px)}}
h1{{margin:0 0 4px;font-size:22px}}
.meta{{color:#8b8fb0;font-size:13px}}
input{{margin-top:14px;width:100%;max-width:520px;padding:10px 14px;border-radius:10px;border:1px solid #2c3048;background:#0e1018;color:var(--fg);font-size:15px}}
main{{max-width:1100px;margin:0 auto;padding:16px 24px 60px}}
ul{{list-style:none;padding:0;margin:0}}
li{{display:flex;justify-content:space-between;gap:16px;padding:11px 14px;border-bottom:1px solid #1a1d2c}}
li:hover{{background:var(--card)}}
a{{color:var(--fg);text-decoration:none;word-break:break-all}}
a:hover{{color:var(--accent)}}
.sz{{color:#8b8fb0;font-size:12px;white-space:nowrap;font-variant-numeric:tabular-nums}}
.stats{{display:flex;gap:24px;flex-wrap:wrap;margin:16px 0 24px;padding:16px;background:var(--card);border-radius:12px}}
.stat b{{display:block;font-size:20px;color:var(--accent)}}
.stat span{{font-size:12px;color:#8b8fb0}}
</style>
</head>
<body>
<header>
  <h1>BELENTANI · Unified Portal</h1>
  <div class="meta">Generado {datetime.now().isoformat(timespec='seconds')} · dedupe sha256 · local</div>
  <input id="q" placeholder="Filtrar por nombre..." autofocus>
</header>
<main>
  <div class="stats">
    <div class="stat"><b>{len(rows)}</b><span>HTML únicos</span></div>
    <div class="stat"><b>{rep['duplicate_groups']}</b><span>grupos duplicados</span></div>
    <div class="stat"><b>{rep['html_found']}</b><span>HTML encontrados</span></div>
    <div class="stat"><b>{sum(s for _,s,_ in rows)/1048576:.0f} MB</b><span>tamaño único</span></div>
  </div>
  <ul id="list">
{items}
  </ul>
</main>
<script>
const q=document.getElementById('q'),items=[...document.querySelectorAll('#list li')];
q.addEventListener('input',()=>{{const v=q.value.toLowerCase();let n=0;
  for(const li of items){{const show=li.dataset.n.includes(v);li.style.display=show?'':'none';if(show)n++;}}}});
</script>
</body>
</html>
"""
with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
    f.write(page)

with open(os.path.join(HERE, "MANIFEST.md"), "w", encoding="utf-8") as f:
    f.write(f"# Belentani Unified — Manifiesto\n\n")
    f.write(f"- Generado: {datetime.now().isoformat(timespec='seconds')}\n")
    f.write(f"- HTML encontrados: {rep['html_found']} ({rep['html_total_mb']} MB)\n")
    f.write(f"- HTML únicos: {rep['unique_files']} ({rep['unique_mb']} MB)\n")
    f.write(f"- Grupos duplicados: {rep['duplicate_groups']}\n\n")
    f.write("## Archivos únicos\n\n| # | Archivo | MB | Origen |\n|---|---|---|---|\n")
    for i, (n, s, orig) in enumerate(rows, 1):
        f.write(f"| {i} | `{n}` | {s/1048576:.2f} | `{orig}` |\n")

print(f"index.html -> {len(rows)} enlaces")
print(f"MANIFEST.md -> {len(rows)} filas")
