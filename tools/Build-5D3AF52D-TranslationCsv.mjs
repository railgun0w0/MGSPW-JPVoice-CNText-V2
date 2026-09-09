#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { Workbook } from "@oai/artifact-tool";

const inputPath = process.argv[2];
const outputPath = process.argv[3];
if (!inputPath || !outputPath) {
  throw new Error("usage: Build-5D3AF52D-TranslationCsv.mjs INPUT.jsonl OUTPUT.csv");
}

const columns = [
  "file_id",
  "unique_index",
  "first_reference_index",
  "reference_indices",
  "reference_count",
  "scene_context",
  "entity_context",
  "previous_jpn_text",
  "jpn_text",
  "next_jpn_text",
  "jpn_control_tokens",
  "cn_text",
  "cn_control_tokens",
  "control_structure_status",
  "jpn_utf8_bytes",
  "cn_utf8_bytes",
  "translation_status",
  "translation_basis",
  "notes",
];

function csvField(value) {
  const text = value === undefined || value === null ? "" : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

const source = await fs.readFile(inputPath, "utf8");
const rows = source.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
if (rows.length !== 110) throw new Error(`expected 110 rows, found ${rows.length}`);
const csvText = "\uFEFF" + [
  columns.map(csvField).join(","),
  ...rows.map((row) => columns.map((column) => csvField(row[column])).join(",")),
].join("\r\n") + "\r\n";

const workbook = await Workbook.fromCSV(csvText.replace(/^\uFEFF/, ""), { sheetName: "5D3AF52D" });
const sheet = workbook.worksheets.getItem("5D3AF52D");
const used = sheet.getUsedRange(true);
if (!used || used.rowCount - 1 !== rows.length) {
  throw new Error("artifact-tool row-count validation failed");
}
const inspected = await workbook.inspect({
  kind: "region",
  sheetId: "5D3AF52D",
  range: "A1:S6",
  maxChars: 6000,
});
if (!inspected.ndjson) throw new Error("artifact-tool did not return inspection data");
if (sheet.getRange("A1").values?.[0]?.[0] !== "file_id" ||
    sheet.getRange("L1").values?.[0]?.[0] !== "cn_text") {
  throw new Error("artifact-tool validation did not observe required headers");
}
if (rows.some((row) => !row.jpn_text || !row.cn_text || row.translation_status !== "COMPLETE")) {
  throw new Error("translation worktable contains incomplete rows");
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.writeFile(outputPath, csvText, "utf8");
process.stdout.write(JSON.stringify({ CSV_PATH: outputPath, ROWS: rows.length }) + "\n");
