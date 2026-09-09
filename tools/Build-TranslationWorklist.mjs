#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Workbook } from "@oai/artifact-tool";


const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const v2Root = path.resolve(scriptDir, "..");
const translationRoot = path.join(v2Root, "build", "translation");
const canonicalRoot = path.join(v2Root, "translations");
const worklistPath = path.join(translationRoot, "translation_worklist.csv");
const catalogPath = path.join(translationRoot, "translation_text_catalog.csv");
const manifestPath = path.join(translationRoot, "compiled_translation_manifest.csv");
const slotCanonicalRoot = path.join(canonicalRoot, "slot_olang");
const batchDefinitionRoot = path.join(v2Root, "work", "translation_batches", "slot_olang");

const sources = [
  ["OHD", 10, path.join(translationRoot, "jpn_ohd", "jpn_ohd_master.csv")],
  ["LOOSE_OLANG", 20, path.join(translationRoot, "jpn_loose_olang", "jpn_loose_olang_master.csv")],
  ["STAGEDAT_OLANG", 30, path.join(translationRoot, "jpn_stagedat", "jpn_stagedat_text_master.csv")],
  ["SLOT_OLANG", 40, path.join(translationRoot, "jpn_slot_olang", "jpn_slot_olang_master.csv")],
  ["YPK_GTT", 50, path.join(translationRoot, "jpn_gtt", "jpn_gtt_master.csv")],
];

const priorityLabels = new Map([
  [10, "01_OHD"],
  [20, "02_LOOSE_OLANG"],
  [30, "03_STAGEDAT"],
  [40, "04_SLOT_OLANG"],
  [50, "05_YPK_GTT"],
]);

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

async function writeValidatedCsv(filePath, sheetName, columns, rows) {
  const csvText = encodeCsv(columns, rows);
  const workbook = await Workbook.fromCSV(csvText.replace(/^\uFEFF/, ""), { sheetName });
  const sheet = workbook.worksheets.getItem(sheetName);
  const used = sheet.getUsedRange(true);
  if (!used || used.rowCount - 1 !== rows.length || used.columnCount !== columns.length) {
    throw new Error(`${sheetName}: artifact-tool dimensions do not match source rows`);
  }
  const inspected = await workbook.inspect({
    kind: "region",
    sheetId: sheetName,
    range: `A1:${columnName(Math.min(columns.length, 20))}${Math.min(rows.length + 1, 6)}`,
    maxChars: 6000,
  });
  if (!inspected.ndjson) throw new Error(`${sheetName}: artifact-tool inspection returned no data`);
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, csvText, "utf8");
}

function columnName(count) {
  let value = count;
  let output = "";
  while (value > 0) {
    value -= 1;
    output = String.fromCharCode(65 + (value % 26)) + output;
    value = Math.floor(value / 26);
  }
  return output;
}

function textId(text) {
  return "TXT_" + crypto.createHash("sha256").update(text, "utf8").digest("hex").slice(0, 16).toUpperCase();
}

function controlTokens(text) {
  return JSON.stringify(text.match(/<[^<>]*>|\$[A-Za-z0-9_]+/g) ?? []);
}

function location(resourceClass, row) {
  if (resourceClass === "YPK_GTT") return `${row.file_id}:record${row.record_index}:segment${row.segment_index}`;
  if (resourceClass === "OHD") return `${row.file_id}:variant${row.payload_variant_index}:record${row.record_index}`;
  if (resourceClass === "LOOSE_OLANG") return `${row.file_id}:reference${row.reference_index}`;
  if (resourceClass === "SLOT_OLANG") return `page${row.page}:tag${row.tag_index}:${row.file_id}:reference${row.reference_index}`;
  return `page${row.page}:${row.archive_entry_name}:reference${row.reference_index}`;
}

function relativeToV2(filePath) {
  return path.relative(v2Root, filePath).split(path.sep).join("/");
}

const textGroups = new Map();
const resourceGroups = new Map();
const sourceRowsByClass = new Map();
let sourceRows = 0;
let sequence = 0;

for (const [resourceClass, priority, filePath] of sources) {
  const rows = await readCsv(filePath, resourceClass.slice(0, 24));
  sourceRowsByClass.set(resourceClass, rows);
  for (const row of rows) {
    sourceRows += 1;
    const text = String(row.jpn_text ?? "");
    if (!text) continue;

    let textGroup = textGroups.get(text);
    if (!textGroup) {
      textGroup = {
        work_id: textId(text),
        priority,
        first_sequence: sequence++,
        jpn_text: text,
        control_tokens: controlTokens(text),
        resource_classes: new Set(),
        source_row_count: 0,
        rows_with_aux_reference: 0,
        aux: new Set(),
        eng: new Set(),
        statuses: new Set(),
        locations: [],
        capacities: [],
        final: new Set(),
      };
      textGroups.set(text, textGroup);
    }
    textGroup.priority = Math.min(textGroup.priority, priority);
    textGroup.resource_classes.add(resourceClass);
    textGroup.source_row_count += 1;
    if (row.mlg_cn_reference) {
      textGroup.aux.add(String(row.mlg_cn_reference));
      textGroup.rows_with_aux_reference += 1;
    }
    if (row.eng_reference) textGroup.eng.add(String(row.eng_reference));
    if (row.reference_status) textGroup.statuses.add(String(row.reference_status));
    if (row.cn_text) textGroup.final.add(String(row.cn_text));
    if (textGroup.locations.length < 8) textGroup.locations.push(`${resourceClass}:${location(resourceClass, row)}`);
    if ((resourceClass === "YPK_GTT" || resourceClass === "OHD") && row.text_capacity !== "") {
      const capacity = Number(row.text_capacity);
      if (Number.isFinite(capacity)) textGroup.capacities.push(capacity);
    }

    const fileId = String(row.file_id ?? "").toUpperCase();
    if (!fileId) throw new Error(`${resourceClass}: row has no file_id`);
    const resourceKey = `${resourceClass}:${fileId}`;
    let resourceGroup = resourceGroups.get(resourceKey);
    if (!resourceGroup) {
      resourceGroup = {
        priority,
        resourceClass,
        fileId,
        objectCount: 0,
        uniqueTexts: new Set(),
        pages: new Set(),
        variants: new Set(),
        referenceStatuses: new Set(),
      };
      resourceGroups.set(resourceKey, resourceGroup);
    }
    resourceGroup.objectCount += 1;
    resourceGroup.uniqueTexts.add(text);
    if (row.page !== "") resourceGroup.pages.add(String(row.page));
    if (row.payload_variant_index !== "") resourceGroup.variants.add(String(row.payload_variant_index));
    if (row.reference_status) resourceGroup.referenceStatuses.add(String(row.reference_status));
  }
}

const catalogRows = [...textGroups.values()]
  .sort((a, b) => a.priority - b.priority || a.first_sequence - b.first_sequence)
  .map((group) => {
    const aux = [...group.aux];
    const eng = [...group.eng];
    const final = [...group.final];
    let translationStatus;
    let reviewReason = "";
    if (final.length === 1) translationStatus = "FINAL_EXISTING";
    else if (final.length > 1) {
      translationStatus = "FINAL_CONFLICT";
      reviewReason = "multiple existing final translations";
    } else if (aux.length > 1) {
      translationStatus = "REFERENCE_CONFLICT";
      reviewReason = "multiple auxiliary Chinese candidates for the same JPN text";
    } else if (aux.length === 1) translationStatus = "REFERENCE_AVAILABLE";
    else {
      translationStatus = "NEEDS_TRANSLATION";
      reviewReason = "no auxiliary Chinese reference";
    }
    return {
      text_id: group.work_id,
      priority: priorityLabels.get(group.priority),
      catalog_status: translationStatus,
      resource_classes: [...group.resource_classes].join(";"),
      source_row_count: group.source_row_count,
      rows_with_aux_reference: group.rows_with_aux_reference,
      jpn_text: group.jpn_text,
      control_tokens: group.control_tokens,
      mlg_cn_reference: aux[0] ?? "",
      mlg_cn_reference_variants: JSON.stringify(aux),
      mlg_cn_variant_count: aux.length,
      eng_reference: eng[0] ?? "",
      eng_reference_variants: JSON.stringify(eng),
      eng_variant_count: eng.length,
      reference_statuses: [...group.statuses].join(";"),
      minimum_fixed_text_capacity: group.capacities.length ? Math.min(...group.capacities) : "",
      example_locations: JSON.stringify(group.locations),
      review_reason: reviewReason,
      existing_cn_text: final[0] ?? "",
      cn_utf8_byte_length: final.length === 1 ? Buffer.byteLength(final[0], "utf8") : "",
    };
  });

const catalogColumns = [
  "text_id", "priority", "catalog_status", "resource_classes", "source_row_count",
  "rows_with_aux_reference", "jpn_text", "control_tokens", "mlg_cn_reference",
  "mlg_cn_reference_variants", "mlg_cn_variant_count", "eng_reference",
  "eng_reference_variants", "eng_variant_count", "reference_statuses",
  "minimum_fixed_text_capacity", "example_locations", "review_reason", "existing_cn_text",
  "cn_utf8_byte_length",
];

const fixtureColumns = [
  "file_id", "unique_index", "first_reference_index", "reference_indices", "reference_count",
  "scene_context", "entity_context", "previous_jpn_text", "jpn_text", "next_jpn_text",
  "jpn_control_tokens", "cn_text", "cn_control_tokens", "control_structure_status",
  "jpn_utf8_bytes", "cn_utf8_bytes", "translation_status", "build_status", "ingame_status",
  "translation_basis", "notes",
];

function controlSignature(text) {
  return (String(text).match(/<[^<>]*>|\$[A-Za-z0-9_]+/g) ?? []).map((token) => {
    if (token.startsWith("<R=")) return "R";
    if (token.startsWith("<I=")) return "I";
    if (token === "<->") return "-";
    if (token.startsWith("<")) return token.slice(1).split("=", 1)[0].replace(/>$/, "");
    return "$";
  });
}

function buildCanonicalRows(resource, masterRows) {
  const fileId = String(resource.file_id).toUpperCase();
  const ordered = masterRows
    .filter((row) => String(row.file_id).toUpperCase() === fileId)
    .sort((a, b) => Number(a.reference_index) - Number(b.reference_index));
  if (!ordered.length) throw new Error(`${fileId}: batch resource has no JPN master rows`);
  const translations = new Map(
    resource.translations.map((item) => [Number(item.reference_index), String(item.cn_text)])
  );
  if (translations.size !== resource.translations.length) {
    throw new Error(`${fileId}: duplicate reference translation in batch definition`);
  }
  const expectedIndices = new Set(ordered.map((row) => Number(row.reference_index)));
  if (translations.size !== expectedIndices.size || [...translations.keys()].some((index) => !expectedIndices.has(index))) {
    throw new Error(`${fileId}: batch translations do not cover every JPN reference`);
  }
  const groups = new Map();
  for (const row of ordered) {
    const referenceIndex = Number(row.reference_index);
    const cnText = translations.get(referenceIndex);
    if (!cnText) throw new Error(`${fileId}: empty Chinese text at reference ${referenceIndex}`);
    const jpnText = String(row.jpn_text);
    const sourceSignature = JSON.stringify(controlSignature(jpnText));
    const targetSignature = JSON.stringify(controlSignature(cnText));
    if (sourceSignature !== targetSignature) {
      throw new Error(`${fileId}: control structure mismatch at reference ${referenceIndex}`);
    }
    let group = groups.get(jpnText);
    if (!group) {
      group = { first: referenceIndex, indices: [], rows: [], cnText };
      groups.set(jpnText, group);
    } else if (group.cnText !== cnText) {
      throw new Error(`${fileId}: duplicate JPN text has conflicting Chinese translations`);
    }
    group.indices.push(referenceIndex);
    group.rows.push(row);
  }
  const allJpn = new Map(ordered.map((row) => [Number(row.reference_index), String(row.jpn_text)]));
  const maxReference = Math.max(...allJpn.keys());
  return [...groups.entries()].map(([jpnText, group], uniqueIndex) => {
    let previous = "";
    for (let index = group.first - 1; index >= 0; index -= 1) {
      if (allJpn.has(index) && allJpn.get(index) !== jpnText) {
        previous = allJpn.get(index);
        break;
      }
    }
    let next = "";
    const last = Math.max(...group.indices);
    for (let index = last + 1; index <= maxReference; index += 1) {
      if (allJpn.has(index) && allJpn.get(index) !== jpnText) {
        next = allJpn.get(index);
        break;
      }
    }
    const entityContext = group.rows.map((row) =>
      `ref${row.reference_index}:entity${row.entity_index}:key${parseIntegerForLabel(row.entity_key)}:ord${row.ordinal_in_entity}`
    ).join(";");
    return {
      file_id: fileId,
      unique_index: uniqueIndex,
      first_reference_index: group.first,
      reference_indices: group.indices.join(";"),
      reference_count: group.indices.length,
      scene_context: resource.scene_context ?? "",
      entity_context: entityContext,
      previous_jpn_text: previous,
      jpn_text: jpnText,
      next_jpn_text: next,
      jpn_control_tokens: (jpnText.match(/<[^<>]*>|\$[A-Za-z0-9_]+/g) ?? []).join(" | "),
      cn_text: group.cnText,
      cn_control_tokens: (group.cnText.match(/<[^<>]*>|\$[A-Za-z0-9_]+/g) ?? []).join(" | "),
      control_structure_status: "MATCH",
      jpn_utf8_bytes: Buffer.byteLength(jpnText, "utf8"),
      cn_utf8_bytes: Buffer.byteLength(group.cnText, "utf8"),
      translation_status: resource.translation_status ?? "APPROVED",
      build_status: resource.build_status ?? "READY",
      ingame_status: resource.ingame_status ?? "NOT_TESTED",
      translation_basis: resource.translation_basis ?? "JPN_PRIMARY; MLG_CN_CONTEXT_AUXILIARY",
      notes: resource.notes ?? "",
    };
  });
}

function parseIntegerForLabel(value) {
  const text = String(value);
  return text || "0";
}

await fs.mkdir(slotCanonicalRoot, { recursive: true });
let batchFiles = [];
try {
  batchFiles = (await fs.readdir(batchDefinitionRoot)).filter((name) => name.toLowerCase().endsWith(".json"));
} catch (error) {
  if (error.code !== "ENOENT") throw error;
}
for (const batchFile of batchFiles.sort()) {
  const definition = JSON.parse(await fs.readFile(path.join(batchDefinitionRoot, batchFile), "utf8"));
  for (const resource of definition.resources ?? []) {
    const fileId = String(resource.file_id).toUpperCase();
    const canonicalRows = buildCanonicalRows(resource, sourceRowsByClass.get("SLOT_OLANG"));
    await writeValidatedCsv(path.join(slotCanonicalRoot, `${fileId}.csv`), fileId, fixtureColumns, canonicalRows);
  }
}

const canonicalInfos = new Map();
for (const filename of (await fs.readdir(slotCanonicalRoot)).filter((name) => name.toLowerCase().endsWith(".csv")).sort()) {
  const fileId = path.basename(filename, ".csv").toUpperCase();
  const filePath = path.join(slotCanonicalRoot, filename);
  const rows = await readCsv(filePath, `canonical_${fileId}`);
  if (!rows.length || rows.some((row) => String(row.file_id).toUpperCase() !== fileId)) {
    throw new Error(`${fileId}: canonical file identity mismatch`);
  }
  if (rows.some((row) => !row.jpn_text || !row.cn_text || row.control_structure_status !== "MATCH")) {
    throw new Error(`${fileId}: canonical translation contains incomplete or invalid rows`);
  }
  const references = new Set();
  for (const row of rows) {
    for (const referenceIndex of String(row.reference_indices).split(";").filter(Boolean)) {
      if (references.has(referenceIndex)) throw new Error(`${fileId}: duplicate canonical reference ${referenceIndex}`);
      references.add(referenceIndex);
    }
  }
  const statusSet = (column) => new Set(rows.map((row) => String(row[column])));
  canonicalInfos.set(fileId, {
    fileId,
    filePath,
    rows,
    references,
    translationStatus: statusSet("translation_status").size === 1 ? rows[0].translation_status : "STATUS_CONFLICT",
    buildStatus: statusSet("build_status").size === 1 ? rows[0].build_status : "STATUS_CONFLICT",
    ingameStatus: statusSet("ingame_status").size === 1 ? rows[0].ingame_status : "STATUS_CONFLICT",
  });
}

const worklistRows = [...resourceGroups.values()]
  .sort((a, b) => a.priority - b.priority || a.fileId.localeCompare(b.fileId))
  .map((group) => {
    const canonical = group.resourceClass === "SLOT_OLANG" ? canonicalInfos.get(group.fileId) : undefined;
    return {
      work_id: `${group.resourceClass}_${group.fileId}`,
      priority: priorityLabels.get(group.priority),
      resource_class: group.resourceClass,
      resource_id: group.fileId,
      file_id: group.fileId,
      jpn_object_count: group.objectCount,
      unique_jpn_text_count: group.uniqueTexts.size,
      page_count: group.pages.size,
      payload_variant_count: group.variants.size || 1,
      translation_status: canonical?.translationStatus ?? "NOT_STARTED",
      translated_unique_texts: canonical?.rows.length ?? 0,
      mapped_jpn_objects: canonical?.references.size ?? 0,
      control_status: canonical ? "MATCH" : "NOT_CHECKED",
      capacity_status: canonical ? "NOT_APPLICABLE" : "NOT_CHECKED",
      build_status: canonical?.buildStatus ?? "NOT_BUILT",
      ingame_status: canonical?.ingameStatus ?? "NOT_TESTED",
      translation_file: canonical ? relativeToV2(canonical.filePath) : "",
      reference_statuses: [...group.referenceStatuses].join(";"),
      notes: canonical ? String(canonical.rows[0].notes ?? "") : "",
    };
  });

const worklistColumns = [
  "work_id", "priority", "resource_class", "resource_id", "file_id", "jpn_object_count",
  "unique_jpn_text_count", "page_count", "payload_variant_count", "translation_status",
  "translated_unique_texts", "mapped_jpn_objects", "control_status", "capacity_status",
  "build_status", "ingame_status", "translation_file", "reference_statuses", "notes",
];

const manifestRows = [];
for (const canonicalInfo of [...canonicalInfos.values()].sort((a, b) => a.fileId.localeCompare(b.fileId))) {
  if (canonicalInfo.translationStatus !== "APPROVED") continue;
  const canonicalByReference = new Map();
  for (const row of canonicalInfo.rows) {
    for (const referenceIndex of String(row.reference_indices).split(";").filter(Boolean)) {
      canonicalByReference.set(referenceIndex, row);
    }
  }
  const slotRows = sourceRowsByClass.get("SLOT_OLANG").filter(
    (row) => String(row.file_id).toUpperCase() === canonicalInfo.fileId
  );
  if (!slotRows.length) throw new Error(`${canonicalInfo.fileId}: canonical file has no master rows`);
  for (const sourceRow of slotRows.slice().sort((a, b) =>
    Number(a.page) - Number(b.page) || Number(a.tag_index) - Number(b.tag_index) || Number(a.reference_index) - Number(b.reference_index)
  )) {
    const canonical = canonicalByReference.get(String(sourceRow.reference_index));
    if (!canonical) throw new Error(`${canonicalInfo.fileId}: no canonical translation for reference ${sourceRow.reference_index}`);
    if (canonical.jpn_text !== sourceRow.jpn_text) {
      throw new Error(`${canonicalInfo.fileId}: JPN text mismatch at reference ${sourceRow.reference_index}`);
    }
    manifestRows.push({
      resource_class: "SLOT_OLANG",
      resource_id: canonicalInfo.fileId,
      file_id: canonicalInfo.fileId,
      container: sourceRow.container,
      page: sourceRow.page,
      tag_index: sourceRow.tag_index,
      payload_variant_index: sourceRow.payload_variant_index,
      occurrence_count: sourceRow.occurrence_count,
      occurrence_locations: sourceRow.occurrence_locations,
      object_type: "reference",
      object_index: sourceRow.reference_index,
      record_index: "",
      reference_index: sourceRow.reference_index,
      segment_index: "",
      entity_index: sourceRow.entity_index,
      entity_key: sourceRow.entity_key,
      ordinal_in_entity: sourceRow.ordinal_in_entity,
      language_key: sourceRow.language_key,
      style: sourceRow.style,
      jpn_text: sourceRow.jpn_text,
      cn_text: canonical.cn_text,
      control_status: canonical.control_structure_status,
      capacity_status: "NOT_APPLICABLE",
      translation_status: canonical.translation_status,
      build_status: canonical.build_status,
      ingame_status: canonical.ingame_status,
      source_translation_file: relativeToV2(canonicalInfo.filePath),
    });
  }
}

const manifestColumns = [
  "resource_class", "resource_id", "file_id", "container", "page", "tag_index",
  "payload_variant_index", "occurrence_count", "occurrence_locations",
  "object_type", "object_index", "record_index", "reference_index", "segment_index",
  "entity_index", "entity_key", "ordinal_in_entity", "language_key", "style", "jpn_text",
  "cn_text", "control_status", "capacity_status", "translation_status", "build_status",
  "ingame_status", "source_translation_file",
];

await writeValidatedCsv(catalogPath, "text_catalog", catalogColumns, catalogRows);
await writeValidatedCsv(worklistPath, "worklist", worklistColumns, worklistRows);
await writeValidatedCsv(manifestPath, "compiled_manifest", manifestColumns, manifestRows);

console.log(`SOURCE_ROWS=${sourceRows}`);
console.log(`TEXT_CATALOG_ROWS=${catalogRows.length}`);
console.log(`WORKLIST_ROWS=${worklistRows.length}`);
console.log(`CANONICAL_FILES=${canonicalInfos.size}`);
console.log(`CANONICAL_TRANSLATION_ROWS=${[...canonicalInfos.values()].reduce((sum, item) => sum + item.rows.length, 0)}`);
console.log(`COMPILED_MANIFEST_ROWS=${manifestRows.length}`);
console.log(`WORKLIST_PATH=${worklistPath}`);
console.log(`CANONICAL_ROOT=${slotCanonicalRoot}`);
console.log(`MANIFEST_PATH=${manifestPath}`);
console.log(`CATALOG_PATH=${catalogPath}`);
