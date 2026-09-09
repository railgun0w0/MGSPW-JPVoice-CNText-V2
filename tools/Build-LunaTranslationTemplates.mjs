#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Workbook } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const v2Root = path.resolve(scriptDir, "..");
const translationRoot = path.join(v2Root, "build", "translation");
const worklistPath = path.join(translationRoot, "translation_worklist.csv");
const outputRoot = path.join(v2Root, "work", "luna_translation_templates");

const sourceSpecs = {
  OHD: "jpn_ohd_master.csv",
  LOOSE_OLANG: "jpn_loose_olang_master.csv",
  STAGEDAT_OLANG: "jpn_stagedat_text_master.csv",
  SLOT_OLANG: "jpn_slot_olang_master.csv",
  YPK_GTT: "jpn_gtt_master.csv",
};

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
  "build_status",
  "ingame_status",
  "translation_basis",
  "notes",
  "mlg_cn_reference",
  "mlg_cn_reference_variants",
  "eng_reference",
  "eng_reference_variants",
  "reference_status",
  "reference_method",
  "reference_reason",
];

function csvField(value) {
  const text = value === undefined || value === null ? "" : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function encodeCsv(rows) {
  const lines = [columns.map(csvField).join(",")];
  for (const row of rows) lines.push(columns.map((column) => csvField(row[column])).join(","));
  return "\uFEFF" + lines.join("\r\n") + "\r\n";
}

async function readCsv(filePath, sheetName) {
  const text = (await fs.readFile(filePath, "utf8")).replace(/^\uFEFF/, "");
  const workbook = await Workbook.fromCSV(text, { sheetName });
  const sheet = workbook.worksheets.getItem(sheetName);
  const used = sheet.getUsedRange(true);
  if (!used || used.rowCount < 2) return [];
  const values = used.values;
  const headers = values[0].map(String);
  return values.slice(1).map((valuesRow) =>
    Object.fromEntries(headers.map((header, index) => [header, valuesRow[index] ?? ""]))
  );
}

async function writeValidatedCsv(filePath, sheetName, rows) {
  const csvText = encodeCsv(rows);
  const workbook = await Workbook.fromCSV(csvText.replace(/^\uFEFF/, ""), { sheetName });
  const sheet = workbook.worksheets.getItem(sheetName);
  const used = sheet.getUsedRange(true);
  if (!used || used.rowCount - 1 !== rows.length || used.columnCount !== columns.length) {
    throw new Error(`${sheetName}: artifact-tool dimensions do not match generated rows`);
  }
  const inspected = await workbook.inspect({
    kind: "region",
    sheetId: sheetName,
    range: `A1:U${Math.min(rows.length + 1, 6)}`,
    maxChars: 6000,
  });
  if (!inspected.ndjson) throw new Error(`${sheetName}: artifact-tool inspection returned no data`);
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, csvText, "utf8");
}

function upper(value) {
  return String(value ?? "").toUpperCase();
}

function numeric(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : Number.MAX_SAFE_INTEGER;
}

function textControls(text) {
  return (String(text ?? "").match(/<[^<>]*>|\$[A-Za-z0-9_]+/g) ?? []).join(" | ");
}

function utf8Bytes(text) {
  return Buffer.byteLength(String(text ?? ""), "utf8");
}

function distinctNonEmpty(values) {
  const result = [];
  const seen = new Set();
  for (const value of values) {
    const text = value === undefined || value === null ? "" : String(value);
    if (text === "" || seen.has(text)) continue;
    seen.add(text);
    result.push(text);
  }
  return result;
}

function distinctEvidence(values) {
  const result = [];
  const seen = new Set();
  for (const value of values) {
    const text = value === undefined || value === null ? "" : String(value);
    if (seen.has(text)) continue;
    seen.add(text);
    result.push(text);
  }
  return result;
}

function serializeEvidence(values) {
  const distinct = distinctEvidence(values);
  if (!distinct.length || (distinct.length === 1 && distinct[0] === "")) return "";
  return distinct.length === 1 ? distinct[0] : JSON.stringify(distinct);
}

function fallbackReason(row) {
  const status = String(row.reference_status ?? "");
  const method = String(row.reference_method ?? "");
  const rawReason = String(row.reference_reason ?? "");
  if (rawReason) return rawReason;
  if (!status && !method) return "";
  const parts = [`master status=${status || "UNSPECIFIED"}`];
  if (method) parts.push(`mapping method=${method}`);
  if (status === "AUX_CN_ATTACHED") {
    parts.push("candidate attached as auxiliary evidence only; verify against JPN and context");
  } else if (status === "AUX_UNCHANGED") {
    parts.push("auxiliary bank retains the JPN text; no translated candidate is present");
  } else if (status === "AUX_EMPTY") {
    parts.push("auxiliary bank is empty at this coordinate; do not infer a candidate");
  } else if (/VERIFY_FAILED|NO_RELIABLE|NO_AUX_RESOURCE/i.test(status)) {
    parts.push("master verification is weak or failed; do not rely on this reference");
  }
  return parts.join("; ");
}

function aggregateReason(group, mlgVariants, engVariants) {
  const evidence = serializeEvidence(group.items.map((item) => fallbackReason(item.row)));
  const flags = [];
  if (mlgVariants.length || engVariants.length) {
    flags.push("auxiliary candidates only; JPN remains authoritative; verify against JPN text and context");
  }
  if (mlgVariants.length > 1 || engVariants.length > 1) {
    flags.push("multiple candidates aggregated from all real JPN references; split/merge/order mismatch remains possible");
  }
  const statuses = distinctEvidence(group.items.map((item) => String(item.row.reference_status ?? "")));
  const methods = distinctEvidence(group.items.map((item) => String(item.row.reference_method ?? "")));
  if (statuses.length > 1) flags.push("reference_status conflict across real JPN references; review all statuses");
  if (methods.length > 1) flags.push("reference_method conflict across real JPN references; review all methods");
  if (!evidence && !flags.length) return "";
  return [evidence, ...flags].filter(Boolean).join("; ");
}

function sourceOrder(resourceClass, row, originalIndex) {
  const page = numeric(row.page);
  const tag = numeric(row.tag_index);
  const variant = numeric(row.payload_variant_index);
  const archive = numeric(row.archive_entry_index);
  if (resourceClass === "YPK_GTT") {
    return [numeric(row.record_index), numeric(row.segment_index), originalIndex];
  }
  if (resourceClass === "OHD") {
    return [page, tag, variant, numeric(row.record_index), originalIndex];
  }
  return [page, tag, variant, archive, numeric(row.entity_index), numeric(row.reference_index), originalIndex];
}

function compareOrder(a, b) {
  for (let index = 0; index < Math.max(a.length, b.length); index += 1) {
    const left = a[index] ?? 0;
    const right = b[index] ?? 0;
    if (left !== right) return left - right;
  }
  return 0;
}

function sourceIdentity(resourceClass, row) {
  if (resourceClass === "YPK_GTT") {
    return `record${row.record_index}:segment${row.segment_index}:timing${row.timing_start}-${row.timing_end}`;
  }
  if (resourceClass === "OHD") {
    return `record${row.record_index}:offset${row.record_offset}:size${row.record_size}`;
  }
  return `page${row.page}:tag${row.tag_index}:entity${row.entity_index}:key${row.entity_key}:ref${row.reference_index}:ord${row.ordinal_in_entity}`;
}

function referenceValue(resourceClass, row) {
  if (resourceClass === "YPK_GTT" || resourceClass === "OHD") return "";
  return String(row.reference_index ?? "");
}

function buildRows(resourceClass, fileId, sourceRows) {
  const ordered = sourceRows
    .map((row, originalIndex) => ({ row, originalIndex, order: [originalIndex] }));
  const groups = new Map();
  for (const item of ordered) {
    const text = String(item.row.jpn_text ?? "");
    let group = groups.get(text);
    if (!group) {
      group = { text, items: [], firstOrder: item.order };
      groups.set(text, group);
    }
    group.items.push(item);
  }
  const uniqueGroups = [...groups.values()];
  return uniqueGroups.map((group, uniqueIndex) => {
    const first = group.items[0].row;
    const firstPos = ordered.findIndex((item) => item === group.items[0]);
    let previous = "";
    for (let index = firstPos - 1; index >= 0; index -= 1) {
      const candidate = String(ordered[index].row.jpn_text ?? "");
      if (candidate !== group.text) {
        previous = candidate;
        break;
      }
    }
    let next = "";
    for (let index = firstPos + 1; index < ordered.length; index += 1) {
      const candidate = String(ordered[index].row.jpn_text ?? "");
      if (candidate !== group.text) {
        next = candidate;
        break;
      }
    }
    const references = group.items.map((item) => referenceValue(resourceClass, item.row)).filter(Boolean);
    const identities = group.items.map((item) => sourceIdentity(resourceClass, item.row));
    const entityContext = identities.join(";");
    const mlgVariants = distinctNonEmpty(group.items.map((item) => item.row.mlg_cn_reference));
    const engVariants = distinctNonEmpty(group.items.map((item) => item.row.eng_reference));
    return {
      file_id: fileId,
      unique_index: uniqueIndex,
      first_reference_index: references[0] ?? "",
      reference_indices: references.join(";"),
      reference_count: references.length ? references.length : "",
      scene_context: "",
      entity_context: entityContext,
      previous_jpn_text: previous,
      jpn_text: group.text,
      next_jpn_text: next,
      jpn_control_tokens: textControls(group.text),
      cn_text: "",
      cn_control_tokens: "",
      control_structure_status: "NOT_CHECKED",
      jpn_utf8_bytes: utf8Bytes(group.text),
      cn_utf8_bytes: "",
      translation_status: "NOT_STARTED",
      build_status: "NOT_BUILT",
      ingame_status: "NOT_TESTED",
      translation_basis: "JPN_PRIMARY; MLG_CN_CONTEXT_AUXILIARY",
      notes: `mechanical template; resource_class=${resourceClass}; source_objects=${group.items.length}`,
      mlg_cn_reference: mlgVariants[0] ?? "",
      mlg_cn_reference_variants: JSON.stringify(mlgVariants),
      eng_reference: engVariants[0] ?? "",
      eng_reference_variants: JSON.stringify(engVariants),
      reference_status: serializeEvidence(group.items.map((item) => item.row.reference_status)),
      reference_method: serializeEvidence(group.items.map((item) => item.row.reference_method)),
      reference_reason: aggregateReason(group, mlgVariants, engVariants),
    };
  });
}

const worklist = await readCsv(worklistPath, "worklist");
const sourceRowsByClass = new Map();
const referenceMasterRoot = path.join(outputRoot, "reference_masters");
for (const [resourceClass, relativePath] of Object.entries(sourceSpecs)) {
  sourceRowsByClass.set(
    resourceClass,
    await readCsv(path.join(referenceMasterRoot, relativePath), resourceClass.slice(0, 24))
  );
}

const failures = [];
const classCounts = new Map();
let generatedFiles = 0;
let sourceObjects = 0;
let uniqueRows = 0;
const auditRows = [];

for (const work of worklist) {
  const resourceClass = String(work.resource_class);
  const fileId = upper(work.file_id);
  try {
    if (!sourceRowsByClass.has(resourceClass)) throw new Error(`no source master mapping for ${resourceClass}`);
    const sourceRows = sourceRowsByClass.get(resourceClass)
      .filter((row) => upper(row.file_id) === fileId);
    if (!sourceRows.length) throw new Error(`no JPN master rows for ${fileId}`);
    const rows = buildRows(resourceClass, fileId, sourceRows);
    await writeValidatedCsv(path.join(outputRoot, resourceClass, `${fileId}.csv`), "template", rows);
    generatedFiles += 1;
    sourceObjects += sourceRows.length;
    uniqueRows += rows.length;
    auditRows.push(...rows.map((row) => ({ ...row, resource_class: resourceClass })));
    classCounts.set(resourceClass, (classCounts.get(resourceClass) ?? 0) + 1);
  } catch (error) {
    failures.push({ resourceClass, fileId, reason: error instanceof Error ? error.message : String(error) });
  }
}

console.log(`TEMPLATE_ROOT=${outputRoot}`);
console.log(`TOTAL_FILE_IDS=${worklist.length}`);
console.log(`GENERATED_CSV=${generatedFiles}`);
console.log(`SOURCE_OBJECTS=${sourceObjects}`);
console.log(`UNIQUE_TEMPLATE_ROWS=${uniqueRows}`);
console.log(`RESOURCE_CLASS_COUNTS=${JSON.stringify(Object.fromEntries([...classCounts.entries()].sort()))}`);
const jsonArrayLength = (value) => {
  try {
    const parsed = JSON.parse(String(value ?? ""));
    return Array.isArray(parsed) ? parsed.length : 0;
  } catch {
    return 0;
  }
};
const riskPattern = /NO_RELIABLE|VERIFY_FAILED|NO_AUX_RESOURCE|AUX_EMPTY/i;
const lowConfidenceRows = auditRows.filter((row) =>
  riskPattern.test(String(row.reference_status)) ||
  jsonArrayLength(row.mlg_cn_reference_variants) > 1 ||
  jsonArrayLength(row.eng_reference_variants) > 1 ||
  String(row.reference_status).startsWith("[") ||
  String(row.reference_method).startsWith("[")
).length;
console.log(`MLG_CN_REFERENCE_ROWS=${auditRows.filter((row) => String(row.mlg_cn_reference ?? "") !== "").length}`);
console.log(`ENG_REFERENCE_ROWS=${auditRows.filter((row) => String(row.eng_reference ?? "") !== "").length}`);
console.log(`MLG_CN_MULTI_VARIANT_ROWS=${auditRows.filter((row) => jsonArrayLength(row.mlg_cn_reference_variants) > 1).length}`);
console.log(`ENG_MULTI_VARIANT_ROWS=${auditRows.filter((row) => jsonArrayLength(row.eng_reference_variants) > 1).length}`);
console.log(`NO_AUXILIARY_REFERENCE_ROWS=${auditRows.filter((row) => jsonArrayLength(row.mlg_cn_reference_variants) === 0 && jsonArrayLength(row.eng_reference_variants) === 0).length}`);
console.log(`LOW_CONFIDENCE_OR_MISMATCH_RISK_ROWS=${lowConfidenceRows}`);
console.log("RISK_DEFINITION=master weak/failed statuses, empty auxiliary status, multiple candidate variants, or conflicting status/method evidence");
function sampleRows(resourceClass, count) {
  const rows = auditRows.filter((row) => row.resource_class === resourceClass);
  const scored = rows.map((row) => {
    const key = `${row.file_id}:${row.unique_index}:${row.jpn_text}`;
    let hash = 2166136261;
    for (const char of key) hash = Math.imul(hash ^ char.charCodeAt(0), 16777619);
    return { row, hash: hash >>> 0 };
  });
  return scored.sort((a, b) => a.hash - b.hash).slice(0, count).map(({ row }) => ({
    resource_class: row.resource_class,
    file_id: row.file_id,
    unique_index: row.unique_index,
    jpn_text: row.jpn_text,
    mlg_cn_reference: row.mlg_cn_reference,
    mlg_cn_reference_variants: row.mlg_cn_reference_variants,
    eng_reference: row.eng_reference,
    eng_reference_variants: row.eng_reference_variants,
    reference_status: row.reference_status,
    reference_method: row.reference_method,
    reference_reason: row.reference_reason,
  }));
}
for (const [resourceClass, count] of [["SLOT_OLANG", 2], ["LOOSE_OLANG", 1], ["STAGEDAT_OLANG", 1], ["YPK_GTT", 2], ["OHD", 1]]) {
  console.log(`SAMPLES_${resourceClass}=${JSON.stringify(sampleRows(resourceClass, count))}`);
}
console.log(`FAILURES=${JSON.stringify(failures)}`);
