#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Workbook } from "@oai/artifact-tool";


const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const v2Root = path.resolve(scriptDir, "..");
const workDir = path.join(v2Root, "work", "text_master_rows");
const outputRoot = path.join(v2Root, "build", "translation");

const specs = [
  {
    key: "ohd",
    input: "enriched_ohd_rows.jsonl",
    output: path.join("jpn_ohd", "jpn_ohd_master.csv"),
    columns: [
      "resource_type", "container", "page", "page_entry_start", "page_entry_capacity",
      "tag_index", "file_id", "payload_variant_index", "occurrence_count",
      "occurrence_locations", "record_index", "record_offset", "record_size",
      "metadata_hex", "text_offset_in_record", "text_capacity", "text_encoding",
      "text_byte_length", "terminator_present", "text_group_id", "control_tokens",
      "jpn_text", "mlg_cn_reference", "eng_reference", "reference_status",
      "reference_method", "reference_reason", "cn_text",
    ],
  },
  {
    key: "loose_olang",
    input: "enriched_loose_olang_rows.jsonl",
    output: path.join("jpn_loose_olang", "jpn_loose_olang_master.csv"),
  },
  {
    key: "slot_olang",
    input: "enriched_slot_olang_rows.jsonl",
    output: path.join("jpn_slot_olang", "jpn_slot_olang_master.csv"),
  },
  {
    key: "stagedat",
    input: "enriched_stagedat_rows.jsonl",
    output: path.join("jpn_stagedat", "jpn_stagedat_text_master.csv"),
  },
];

const rbxColumns = [
  "resource_type", "container", "page", "page_entry_start", "page_entry_capacity",
  "tag_index", "file_id", "payload_variant_index", "occurrence_count",
  "occurrence_locations", "archive_entry_index", "archive_entry_name", "entity_index",
  "entity_key", "entity_key_occurrence", "reference_index", "ordinal_in_entity",
  "language_key", "style", "body_relative_offset", "text_absolute_offset",
  "text_encoding", "text_byte_length", "terminator_present", "text_group_id",
  "control_tokens", "jpn_text", "mlg_cn_reference", "eng_reference",
  "reference_status", "reference_method", "reference_reason", "cn_text",
];
for (const spec of specs) {
  if (!spec.columns) spec.columns = rbxColumns;
}

function csvField(value) {
  const text = value === null || value === undefined ? "" : String(value);
  if (/[",\r\n]/.test(text)) return `"${text.replaceAll('"', '""')}"`;
  return text;
}

function encodeCsv(columns, rows) {
  const lines = [columns.map(csvField).join(",")];
  for (const row of rows) lines.push(columns.map((column) => csvField(row[column])).join(","));
  return "\uFEFF" + lines.join("\r\n") + "\r\n";
}

async function readJsonl(filePath) {
  const text = await fs.readFile(filePath, "utf8");
  return text.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
}

async function validateCsv(csvText, label, expectedRows, expectedHeader = "resource_type") {
  const workbook = await Workbook.fromCSV(csvText.replace(/^\uFEFF/, ""), { sheetName: label });
  const sheet = workbook.worksheets.getItem(label);
  const used = sheet.getUsedRange(true);
  const actualRows = used ? used.rowCount - 1 : 0;
  if (actualRows !== expectedRows) {
    throw new Error(`${label}: artifact-tool row count ${actualRows} != ${expectedRows}`);
  }
  const firstCell = sheet.getRange("A1").values?.[0]?.[0];
  if (firstCell !== expectedHeader) {
    throw new Error(`${label}: artifact-tool validation did not see the header`);
  }
  const inspected = await workbook.inspect({
    kind: "region",
    sheetId: label,
    range: "A1:F3",
    maxChars: 2000,
  });
  if (!inspected.ndjson) {
    throw new Error(`${label}: artifact-tool range inspection returned no data`);
  }
}

const stats = JSON.parse(await fs.readFile(path.join(workDir, "extraction_stats.json"), "utf8"));
const referenceStats = JSON.parse(await fs.readFile(path.join(workDir, "auxiliary_reference_stats.json"), "utf8"));
const outputSummary = {};
for (const spec of specs) {
  const rows = await readJsonl(path.join(workDir, spec.input));
  const csvText = encodeCsv(spec.columns, rows);
  await validateCsv(csvText, spec.key, rows.length);
  const outputPath = path.join(outputRoot, spec.output);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, csvText, "utf8");
  outputSummary[spec.key] = { path: outputPath, rows: rows.length };
}

const gttColumns = [
  "file_id", "record_index", "segment_index", "segment_count", "header_size",
  "record_size", "aligned_size", "timing_start", "timing_end", "text_start",
  "text_end", "text_capacity", "jpn_text", "mlg_cn_reference", "eng_reference",
  "reference_status", "reference_method", "reference_reason", "cn_text",
];
const gttRowsData = await readJsonl(path.join(workDir, "enriched_gtt_rows.jsonl"));
const gttCsv = encodeCsv(gttColumns, gttRowsData);
await validateCsv(gttCsv, "gtt", gttRowsData.length, "file_id");
const gttPath = path.join(outputRoot, "jpn_gtt", "jpn_gtt_master.csv");
await fs.writeFile(gttPath, gttCsv, "utf8");
const gttRows = gttRowsData.length;

const manifestColumns = [
  "resource_class", "master_csv", "scope", "physical_resources", "unique_payloads",
  "total_parser_objects", "japanese_objects", "empty_japanese_objects_excluded",
  "exported_rows", "parse_errors", "translation_status", "structure_authority",
  "reference_policy", "aux_reference_rows", "eng_reference_rows",
  "documentation_reference",
];
const manifestRows = [
  {
    resource_class: "YPK_GTT",
    master_csv: "jpn_gtt/jpn_gtt_master.csv",
    scope: "36 canonical JPN YPK; one row per timed segment",
    physical_resources: 77,
    unique_payloads: 36,
    total_parser_objects: 1882,
    japanese_objects: gttRows,
    empty_japanese_objects_excluded: 0,
    exported_rows: gttRows,
    parse_errors: 0,
    translation_status: "1C79F2AD complete; remaining canonical YPK pending",
    structure_authority: "JPN canonical YPK and multi-segment boundaries",
    reference_policy: "MLG_CN first payload variant auxiliary; ENG disambiguation only",
    aux_reference_rows: referenceStats.gtt.mlg_cn_reference_rows,
    eng_reference_rows: referenceStats.gtt.eng_reference_rows,
    documentation_reference: "https://github.com/LittleBitUA/PEACE-WALKER-LOCALIZATION-TOOL/blob/main/docs/FORMATS.md",
  },
  ...[
    ["OHD", "jpn_ohd/jpn_ohd_master.csv", "ohd", "JPN lane OHD canonical payload variants; one row per record"],
    ["LOOSE_OLANG", "jpn_loose_olang/jpn_loose_olang_master.csv", "loose_olang", "JPN loose OLANG; non-empty Japanese references"],
    ["SLOT_OLANG", "jpn_slot_olang/jpn_slot_olang_master.csv", "slot_olang", "JPN SLOT OLANG canonical payload variants; non-empty Japanese references"],
    ["STAGEDAT_OLANG", "jpn_stagedat/jpn_stagedat_text_master.csv", "stagedat", "Reliable RBX/OLANG entries inside JPN STAGEDAT DAR pages; non-empty Japanese references"],
  ].map(([resourceClass, masterCsv, statsKey, scope]) => ({
    resource_class: resourceClass,
    master_csv: masterCsv,
    scope,
    physical_resources: stats[statsKey].physical_resources,
    unique_payloads: stats[statsKey].unique_payloads,
    total_parser_objects: stats[statsKey].total_parser_objects,
    japanese_objects: stats[statsKey].japanese_objects,
    empty_japanese_objects_excluded: stats[statsKey].empty_japanese_objects_excluded,
    exported_rows: stats[statsKey].rows,
    parse_errors: stats[statsKey].parse_errors,
    translation_status: "not translated under V2 policy",
    structure_authority: "target JPN resource",
    reference_policy: "MLG_CN first payload variant auxiliary; ENG disambiguation only",
    aux_reference_rows: referenceStats[statsKey].mlg_cn_reference_rows,
    eng_reference_rows: referenceStats[statsKey].eng_reference_rows,
    documentation_reference: resourceClass.includes("OLANG")
      ? "https://github.com/LittleBitUA/PEACE-WALKER-LOCALIZATION-TOOL/blob/main/docs/FORMATS.md#5-olang--the-text-tables"
      : "",
  })),
];
const manifestCsv = encodeCsv(manifestColumns, manifestRows);
await validateCsv(manifestCsv, "coverage", manifestRows.length, "resource_class");
const manifestPath = path.join(outputRoot, "text_coverage_manifest.csv");
await fs.mkdir(path.dirname(manifestPath), { recursive: true });
await fs.writeFile(manifestPath, manifestCsv, "utf8");

console.log(`YPK_ROWS=${gttRows}`);
for (const spec of specs) console.log(`${spec.key.toUpperCase()}_ROWS=${outputSummary[spec.key].rows}`);
console.log(`MANIFEST_ROWS=${manifestRows.length}`);
for (const spec of specs) console.log(`${spec.key.toUpperCase()}_CSV=${outputSummary[spec.key].path}`);
console.log(`MANIFEST_CSV=${manifestPath}`);
