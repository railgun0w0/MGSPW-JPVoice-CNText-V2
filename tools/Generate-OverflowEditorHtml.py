from __future__ import annotations

import csv
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build" / "translation" / "fixed_capacity_issues.csv"
OUTPUT = ROOT / "build" / "translation" / "overflow_manual_editor.html"


HTML_TEMPLATE = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GTT 超容量文本手动编辑器</title>
<style>
:root { color-scheme: dark; font-family: Segoe UI, Microsoft YaHei, sans-serif; }
body { margin: 0; background: #111827; color: #e5e7eb; }
header { position: sticky; top: 0; z-index: 2; padding: 16px 22px; background: #1f2937; border-bottom: 1px solid #374151; }
h1 { margin: 0 0 8px; font-size: 22px; }
.note { color: #cbd5e1; font-size: 13px; line-height: 1.5; }
.toolbar { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; align-items: center; }
button, select, input { border: 1px solid #4b5563; border-radius: 5px; background: #111827; color: #e5e7eb; padding: 7px 9px; }
button { cursor: pointer; background: #2563eb; border-color: #3b82f6; }
button.secondary { background: #374151; border-color: #6b7280; }
input { min-width: 220px; }
#summary { margin-left: auto; color: #bfdbfe; font-size: 13px; }
main { padding: 18px 22px 60px; max-width: 1500px; margin: auto; }
.record { border: 1px solid #374151; border-radius: 8px; margin: 0 0 16px; overflow: hidden; background: #1f2937; }
.record-head { display: flex; flex-wrap: wrap; gap: 14px; padding: 10px 14px; align-items: center; border-bottom: 1px solid #374151; }
.record-title { font-weight: 700; color: #f8fafc; }
.meta { color: #cbd5e1; font-size: 12px; }
.status { font-weight: 700; padding: 3px 7px; border-radius: 999px; font-size: 12px; }
.status.HARD_OVERFLOW { background: #7f1d1d; color: #fecaca; }
.status.ALIGNMENT_SPILL { background: #78350f; color: #fde68a; }
.status.NORMAL_FIT { background: #14532d; color: #bbf7d0; }
.record-body { padding: 10px 14px 14px; }
.capacity { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12px; color: #d1d5db; margin-bottom: 10px; }
.capacity strong { color: #f8fafc; }
.segment { display: grid; grid-template-columns: minmax(240px, 1fr) minmax(320px, 1.25fr); gap: 12px; border-top: 1px solid #374151; padding: 12px 0; }
.segment:first-child { border-top: 0; padding-top: 0; }
.segment-label { color: #93c5fd; font-size: 12px; margin-bottom: 5px; }
pre { white-space: pre-wrap; word-break: break-word; margin: 0; padding: 9px; min-height: 38px; border-radius: 5px; background: #111827; color: #f3f4f6; font: 13px/1.5 Consolas, monospace; }
textarea { width: 100%; min-height: 60px; box-sizing: border-box; resize: vertical; border: 1px solid #4b5563; border-radius: 5px; background: #0f172a; color: #f8fafc; padding: 8px; font: 13px/1.5 Segoe UI, Microsoft YaHei, sans-serif; }
.segment-info { grid-column: 2; color: #9ca3af; font-size: 12px; }
.hidden { display: none; }
@media (max-width: 800px) { .segment { grid-template-columns: 1fr; } .segment-info { grid-column: 1; } #summary { margin-left: 0; width: 100%; } }
</style>
</head>
<body>
<header>
  <h1>GTT 超容量文本手动编辑器</h1>
  <div class="note">只修改中文 timed text。每个 segment 自动按 UTF-8 字节数计算，并为每个 segment 加 1 个 NUL。不会修改 record_size 或 aligned_size。↵ 表示实际换行。</div>
  <div class="toolbar">
    <input id="search" placeholder="筛选 file_id / record / 文本">
    <select id="filter"><option value="ALL">全部状态</option><option value="HARD_OVERFLOW">HARD_OVERFLOW</option><option value="ALIGNMENT_SPILL">ALIGNMENT_SPILL</option><option value="NORMAL_FIT">NORMAL_FIT</option></select>
    <button id="recalc" class="secondary">重新计算</button>
    <button id="copy">复制 JSON</button>
    <button id="downloadJson">下载 JSON</button>
    <button id="downloadCsv">下载 CSV</button>
    <span id="summary"></span>
  </div>
</header>
<main id="records"></main>
<script>
const DATA = __DATA__;
const encoder = new TextEncoder();
const state = DATA.map(x => ({...x, cn_texts: [...x.cn_texts]}));
const el = id => document.getElementById(id);
const bytes = s => encoder.encode(s).length;
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const shown = s => String(s).replace(/\\n/g, '↵').replace(/\n/g, '↵');

function calc(r) {
  r.segment_bytes = r.cn_texts.map(bytes);
  r.required = r.segment_bytes.reduce((a, n) => a + n + 1, 0);
  r.over_nominal_bytes = Math.max(0, r.required - r.nominal_capacity);
  r.over_aligned_bytes = Math.max(0, r.required - r.aligned_capacity);
  r.status = r.required > r.aligned_capacity ? 'HARD_OVERFLOW' : (r.required > r.nominal_capacity ? 'ALIGNMENT_SPILL' : 'NORMAL_FIT');
}
state.forEach(calc);

function render() {
  state.forEach(calc);
  const query = el('search').value.trim().toLowerCase();
  const filter = el('filter').value;
  let visible = 0, hard = 0, spill = 0, fit = 0;
  const root = el('records');
  root.innerHTML = '';
  for (const r of state) {
    const hay = [r.file_id, r.record_index, r.jpn_texts.join(' '), r.cn_texts.join(' ')].join(' ').toLowerCase();
    const show = (!query || hay.includes(query)) && (filter === 'ALL' || r.status === filter);
    if (!show) continue;
    visible++;
    if (r.status === 'HARD_OVERFLOW') hard++; else if (r.status === 'ALIGNMENT_SPILL') spill++; else fit++;
    const card = document.createElement('section');
    card.className = 'record';
    const over = r.over_aligned_bytes ? `，超出硬容量 ${r.over_aligned_bytes} bytes` : '';
    card.innerHTML = `<div class="record-head"><span class="record-title">${esc(r.file_id)} / record ${r.record_index}</span><span class="meta">segments=${r.segment_count}</span><span class="meta">header=${r.header_size}</span><span class="meta">record=${r.record_size}</span><span class="meta">aligned=${r.aligned_size}</span><span class="status ${r.status}">${r.status}</span></div><div class="record-body"><div class="capacity"><span>nominal capacity <strong>${r.nominal_capacity}</strong></span><span>aligned capacity <strong>${r.aligned_capacity}</strong></span><span>required <strong>${r.required}</strong></span><span>剩余 <strong>${r.aligned_capacity-r.required}</strong>${over}</span></div></div>`;
    const body = card.querySelector('.record-body');
    r.jpn_texts.forEach((jp, i) => {
      const row = document.createElement('div');
      row.className = 'segment';
      row.innerHTML = `<div><div class="segment-label">segment ${i} · JPN</div><pre>${esc(shown(jp))}</pre></div><div><div class="segment-label">segment ${i} · CN（可编辑）</div><textarea data-file="${esc(r.file_id)}" data-record="${r.record_index}" data-segment="${i}"></textarea></div><div class="segment-info" data-info="${esc(r.file_id)}:${r.record_index}:${i}"></div>`;
      row.querySelector('textarea').value = r.cn_texts[i] || '';
      row.querySelector('textarea').addEventListener('input', e => {
        r.cn_texts[i] = e.target.value;
        render();
      });
      body.appendChild(row);
      row.querySelector('.segment-info').textContent = `当前 ${r.segment_bytes[i]} bytes + NUL = ${r.segment_bytes[i]+1} bytes`;
    });
    root.appendChild(card);
  }
  el('summary').textContent = `显示 ${visible}/${state.length} 条 · HARD ${hard} · SPILL ${spill} · FIT ${fit}`;
}

function exportRows() {
  return state.map(r => ({file_id:r.file_id, record_index:r.record_index, segment_count:r.segment_count, header_size:r.header_size, record_size:r.record_size, aligned_size:r.aligned_size, nominal_capacity:r.nominal_capacity, aligned_capacity:r.aligned_capacity, required:r.required, status:r.status, cn_texts:r.cn_texts, segment_bytes:r.segment_bytes}));
}
function save(name, text, type) {
  const blob = new Blob([text], {type});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 500);
}
function csvCell(v) { const s = String(v ?? ''); return '"' + s.replace(/"/g, '""') + '"'; }
function csvText() {
  const out = [['file_id','record_index','segment_index','segment_count','header_size','record_size','aligned_size','nominal_capacity','aligned_capacity','required','status','jpn_text','cn_text','text_byte_length']];
  for (const r of state) r.jpn_texts.forEach((jp,i) => out.push([r.file_id,r.record_index,i,r.segment_count,r.header_size,r.record_size,r.aligned_size,r.nominal_capacity,r.aligned_capacity,r.required,r.status,jp,r.cn_texts[i],r.segment_bytes[i]]));
  return '\ufeff' + out.map(row => row.map(csvCell).join(',')).join('\n');
}
el('recalc').onclick = render;
el('search').oninput = render;
el('filter').onchange = render;
el('copy').onclick = async () => { await navigator.clipboard.writeText(JSON.stringify(exportRows(), null, 2)); alert('已复制 JSON'); };
el('downloadJson').onclick = () => save('gtt_overflow_manual_edits.json', JSON.stringify(exportRows(), null, 2), 'application/json;charset=utf-8');
el('downloadCsv').onclick = () => save('gtt_overflow_manual_edits.csv', csvText(), 'text/csv;charset=utf-8');
render();
</script>
</body>
</html>
'''


def main() -> None:
    rows: list[dict[str, object]] = []
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("status") != "HARD_OVERFLOW":
                continue
            rows.append(
                {
                    "file_id": row["file_id"],
                    "record_index": int(row["record_index"]),
                    "segment_count": int(row["segment_count"]),
                    "header_size": int(row["header_size"]),
                    "record_size": int(row["record_size"]),
                    "aligned_size": int(row["aligned_size"]),
                    "nominal_capacity": int(row["nominal_capacity"]),
                    "aligned_capacity": int(row["aligned_capacity"]),
                    "jpn_texts": json.loads(row["jpn_texts"]),
                    "cn_texts": json.loads(row["cn_texts"]),
                }
            )
    data = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    OUTPUT.write_text(HTML_TEMPLATE.replace("__DATA__", data), encoding="utf-8")
    print(f"OUTPUT={OUTPUT}")
    print(f"RECORDS={len(rows)}")


if __name__ == "__main__":
    main()
