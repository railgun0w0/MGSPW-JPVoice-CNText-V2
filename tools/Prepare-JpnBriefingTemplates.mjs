#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Workbook } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");
const inputPath = path.join(
  root,
  "build",
  "translation",
  "jpn_briefing",
  "jpn_briefing_luna_rows.json",
);
const templateRoot = path.join(root, "work", "luna_translation_templates", "BRIEFING_NBE");
const stageRoot = path.join(
  root,
  "work",
  "luna_translation_templates",
  ".BRIEFING_NBE_stage",
);
const referenceMasterPath = path.join(
  root,
  "work",
  "luna_translation_templates",
  "reference_masters",
  "jpn_briefing_master.csv",
);
const reportPath = path.join(
  root,
  "build",
  "translation",
  "jpn_briefing",
  "jpn_briefing_template_report.json",
);

function csvField(value) {
  const text = value === undefined || value === null ? "" : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function encodeCsv(columns, rows) {
  const lines = [columns.map(csvField).join(",")];
  for (const row of rows) {
    lines.push(columns.map((column) => csvField(row[column])).join(","));
  }
  return `\uFEFF${lines.join("\r\n")}\r\n`;
}

function safeFileName(fileId) {
  return fileId.replaceAll(/[^A-Za-z0-9_.-]+/g, "_");
}

async function validateWithArtifactTool(csvText, sheetName, rows, columns) {
  const workbook = await Workbook.fromCSV(csvText.replace(/^\uFEFF/, ""), { sheetName });
  const sheet = workbook.worksheets.getItem(sheetName);
  const used = sheet.getUsedRange(true);
  if (!used || used.rowCount !== rows.length + 1 || used.columnCount !== columns.length) {
    throw new Error(
      `${sheetName}: artifact-tool dimensions ${used?.rowCount ?? 0}x${used?.columnCount ?? 0} ` +
        `do not match ${rows.length + 1}x${columns.length}`,
    );
  }
  const inspectColumn = String.fromCharCode(64 + Math.min(columns.length, 26));
  const inspected = await workbook.inspect({
    kind: "region",
    sheetId: sheetName,
    range: `A1:${inspectColumn}${Math.min(rows.length + 1, 4)}`,
    maxChars: 5000,
  });
  if (!inspected.ndjson) {
    throw new Error(`${sheetName}: artifact-tool inspection returned no result`);
  }
}

async function writeValidatedCsv(filePath, sheetName, columns, rows) {
  const csvText = encodeCsv(columns, rows);
  await validateWithArtifactTool(csvText, sheetName, rows, columns);
  // artifact-tool has no CSV export surface; preserve the validated UTF-8 BOM,
  // RFC-4180 quoting, and CRLF serialization used by the existing Luna generator.
  await fs.writeFile(filePath, csvText, "utf8");
}

const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
const templateColumns = payload.template_columns;
const masterColumns = payload.master_columns;
const templateRows = payload.template_rows;
const alignedMasterRows = payload.aligned_master_rows;

if (templateRows.length !== 5645 || alignedMasterRows.length !== 5645) {
  throw new Error("JPN BRIEFING aligned input must contain exactly 5645 rows");
}
if (new Set(templateRows.map((row) => row.file_id)).size !== 469) {
  throw new Error("JPN BRIEFING aligned input must contain exactly 469 file_ids");
}
if (templateRows.some((row) => String(row.cn_text ?? "") !== "")) {
  throw new Error("untranslated BRIEFING templates must not contain cn_text");
}

const rowsByFile = new Map();
for (const row of templateRows) {
  if (!rowsByFile.has(row.file_id)) rowsByFile.set(row.file_id, []);
  rowsByFile.get(row.file_id).push(row);
}
for (const rows of rowsByFile.values()) {
  rows.sort((left, right) => Number(left.unique_index) - Number(right.unique_index));
}

const resolvedTemplateRoot = path.resolve(templateRoot);
const resolvedStageRoot = path.resolve(stageRoot);
const expectedParent = path.resolve(root, "work", "luna_translation_templates");
if (path.dirname(resolvedTemplateRoot) !== expectedParent || path.dirname(resolvedStageRoot) !== expectedParent) {
  throw new Error("refusing to modify a template path outside luna_translation_templates");
}

await fs.rm(resolvedStageRoot, { recursive: true, force: true });
await fs.mkdir(resolvedStageRoot, { recursive: true });

let authoredRows = 0;
for (const [fileId, rows] of [...rowsByFile].sort(([left], [right]) => left.localeCompare(right))) {
  const outputPath = path.join(resolvedStageRoot, `${safeFileName(fileId)}.csv`);
  await writeValidatedCsv(outputPath, fileId.slice(0, 28), templateColumns, rows);
  authoredRows += rows.length;
}
if (authoredRows !== 5645) throw new Error(`authored row count mismatch: ${authoredRows}`);

const stagedFiles = (await fs.readdir(resolvedStageRoot)).filter((name) => name.endsWith(".csv"));
if (stagedFiles.length !== 469) {
  throw new Error(`staged template count mismatch: ${stagedFiles.length}`);
}

const masterStagePath = `${referenceMasterPath}.stage`;
await writeValidatedCsv(
  masterStagePath,
  "JPN_BRIEFING_MASTER",
  masterColumns,
  alignedMasterRows,
);

await fs.mkdir(resolvedTemplateRoot, { recursive: true });
const existingCsvFiles = (await fs.readdir(resolvedTemplateRoot)).filter((name) => name.endsWith(".csv"));
for (const fileName of existingCsvFiles) {
  await fs.rm(path.join(resolvedTemplateRoot, fileName), { force: true });
}
for (const fileName of stagedFiles) {
  await fs.rename(path.join(resolvedStageRoot, fileName), path.join(resolvedTemplateRoot, fileName));
}
await fs.rm(resolvedStageRoot, { recursive: true, force: true });
await fs.copyFile(masterStagePath, referenceMasterPath);
await fs.rm(masterStagePath, { force: true });

const finalFiles = (await fs.readdir(resolvedTemplateRoot)).filter((name) => name.endsWith(".csv"));
if (finalFiles.length !== 469) throw new Error(`final template count mismatch: ${finalFiles.length}`);

const finalReport = {
  ...payload.report,
  status: "PASS",
  template_root: templateRoot,
  reference_master: referenceMasterPath,
  template_file_count: finalFiles.length,
  template_row_count: authoredRows,
  schema_column_count: templateColumns.length,
  cn_text_nonempty_rows: 0,
};
await fs.writeFile(reportPath, `${JSON.stringify(finalReport, null, 2)}\n`, "utf8");
console.log(JSON.stringify(finalReport, null, 2));
