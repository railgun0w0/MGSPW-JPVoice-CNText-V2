#!/usr/bin/env node

/**
 * Merge the frozen BRIEFING mappings into formal per-block production CSVs.
 *
 * This compiler is intentionally limited to translation artifacts. It does not
 * read, build, patch, or install DAT/KEY files.
 */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const defaultRoot = path.resolve(scriptDir, "..");
const logicalResourceClass = "BRIEFING_NBE";
const expected = {
  files: { all: 469, briefingFiles: 363, briefingMission: 106 },
  rows: { all: 5645, briefingFiles: 4810, briefingMission: 835 },
};
const productionColumns = [
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
];
const expectedTemplateColumns = [
  ...productionColumns,
  "mlg_cn_reference",
  "mlg_cn_reference_variants",
  "eng_reference",
  "eng_reference_variants",
  "reference_status",
  "reference_method",
  "reference_reason",
];
const kanaRe = /[\u3040-\u30ff\u31f0-\u31ff]/u;
const formulaErrorRe = /#(?:REF!|DIV\/0!|VALUE!|NAME\?|N\/A|NUM!|NULL!|SPILL!|CALC!)/u;
const representativeFileIds = new Set([
  "BRIEFING_FILES_BLOCK_000000",
  "BRIEFING_MISSION_BLOCK_36D0B0",
]);


class CompileFailure extends Error {}


function parseArgs(argv) {
  let root = defaultRoot;
  let mode = "";
  for (let index = 2; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--write" || value === "--check") {
      if (mode) throw new CompileFailure("choose exactly one of --write or --check");
      mode = value.slice(2);
    } else if (value === "--root") {
      index += 1;
      if (index >= argv.length) throw new CompileFailure("--root requires a path");
      root = path.resolve(argv[index]);
    } else {
      throw new CompileFailure(`unknown argument: ${value}`);
    }
  }
  if (!mode) throw new CompileFailure("choose exactly one of --write or --check");
  return { root, mode };
}


function csvField(value) {
  const text = value === undefined || value === null ? "" : String(value);
  return /[",\r\n]/u.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}


function encodeCsv(columns, rows) {
  const lines = [columns.map(csvField).join(",")];
  for (const row of rows) lines.push(columns.map((column) => csvField(row[column])).join(","));
  return `\uFEFF${lines.join("\r\n")}\r\n`;
}


function sha256(value) {
  return crypto.createHash("sha256").update(value, "utf8").digest("hex");
}


function stableIdentity(rows, fields) {
  return sha256(JSON.stringify(rows.map((row) => fields.map((field) => row[field] ?? ""))));
}


function integer(value, label) {
  const number = Number.parseInt(String(value), 10);
  if (!Number.isInteger(number)) throw new CompileFailure(`${label}: invalid integer ${value}`);
  return number;
}


function matchesWithOffsets(text, expression) {
  return [...text.matchAll(expression)].map((match) => ({ offset: match.index, token: match[0] }));
}


function allTokens(text) {
  return [
    ...matchesWithOffsets(text, /<[^<>]*>/gu),
    ...matchesWithOffsets(text, /\$[A-Za-z0-9_]+/gu),
    ...matchesWithOffsets(text, /%(?:\d+\$)?[sdif]/gu),
  ]
    .sort((left, right) => left.offset - right.offset)
    .map((item) => item.token);
}


function angleSignature(text) {
  const signature = [];
  for (const token of text.match(/<[^<>]*>/gu) ?? []) {
    if (token.startsWith("<R=")) {
      signature.push(token.slice(3, -1).includes(",") ? "RUBY" : "INVALID_RUBY");
    } else if (token.startsWith("<I=") || token.startsWith("<C=") || token === "<->") {
      signature.push(token);
    } else if (/^<[A-Za-z_-]+(?:=|>)/u.test(token)) {
      signature.push(token);
    }
  }
  return signature;
}


function inventory(text, expression) {
  const counts = new Map();
  for (const token of text.match(expression) ?? []) counts.set(token, (counts.get(token) ?? 0) + 1);
  return [...counts.entries()].sort(([left], [right]) => left.localeCompare(right));
}


function controlError(jpnText, cnText) {
  const jpnAngle = angleSignature(jpnText);
  const cnAngle = angleSignature(cnText);
  if (JSON.stringify(jpnAngle) !== JSON.stringify(cnAngle)) {
    return `angle control mismatch: ${JSON.stringify(jpnAngle)} != ${JSON.stringify(cnAngle)}`;
  }
  const jpnDollar = inventory(jpnText, /\$[A-Za-z0-9_]+/gu);
  const cnDollar = inventory(cnText, /\$[A-Za-z0-9_]+/gu);
  if (JSON.stringify(jpnDollar) !== JSON.stringify(cnDollar)) return "dollar placeholder mismatch";
  const jpnPrintf = inventory(jpnText, /%(?:\d+\$)?[sdif]/gu);
  const cnPrintf = inventory(cnText, /%(?:\d+\$)?[sdif]/gu);
  if (JSON.stringify(jpnPrintf) !== JSON.stringify(cnPrintf)) return "printf placeholder mismatch";
  return "";
}


function parseCsvValues(csvText, label) {
  const text = csvText.replace(/^\uFEFF/u, "");
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  let index = 0;
  const pushField = () => {
    row.push(field);
    field = "";
  };
  const pushRow = () => {
    pushField();
    rows.push(row);
    row = [];
  };
  while (index < text.length) {
    const character = text[index];
    if (quoted) {
      if (character === '"') {
        if (text[index + 1] === '"') {
          field += '"';
          index += 2;
          continue;
        }
        quoted = false;
        index += 1;
        continue;
      }
      field += character;
      index += 1;
      continue;
    }
    if (character === '"' && field === "") {
      quoted = true;
      index += 1;
      continue;
    }
    if (character === ",") {
      pushField();
      index += 1;
      continue;
    }
    if (character === "\r" || character === "\n") {
      pushRow();
      if (character === "\r" && text[index + 1] === "\n") index += 2;
      else index += 1;
      continue;
    }
    field += character;
    index += 1;
  }
  if (quoted) throw new CompileFailure(`${label}: unterminated quoted CSV field`);
  if (field !== "" || row.length) pushRow();
  if (!rows.length) throw new CompileFailure(`${label}: CSV has no used range`);
  const width = rows[0].length;
  if (!width || rows.some((item) => item.length !== width)) {
    throw new CompileFailure(`${label}: CSV rows have inconsistent column counts`);
  }
  return rows.map((item) => item.map((value) => String(value)));
}


async function csvMatrix(csvText, sheetName) {
  const values = parseCsvValues(csvText, sheetName);
  return {
    values,
    rowCount: values.length,
    columnCount: values[0].length,
  };
}


function inspectCsvRegion(values, range) {
  return {
    ndjson: JSON.stringify({ range, rows: values.slice(0, 4) }),
  };
}


function rowsFromMatrix(matrix, label) {
  if (!matrix.values.length) throw new CompileFailure(`${label}: empty CSV`);
  const headers = matrix.values[0];
  const duplicates = headers.filter((item, index) => headers.indexOf(item) !== index);
  if (duplicates.length) throw new CompileFailure(`${label}: duplicate columns ${duplicates.join(", ")}`);
  return {
    headers,
    rows: matrix.values.slice(1).map((values) =>
      Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])),
    ),
  };
}


function normalizeTranslations(mapping, label) {
  if (!Array.isArray(mapping.translations)) {
    throw new CompileFailure(`${label}: translations must be an array`);
  }
  if (mapping.translations.every((item) => item && typeof item === "object" && !Array.isArray(item))) {
    return mapping.translations;
  }
  if (!Array.isArray(mapping.columns) || !mapping.columns.every((item) => typeof item === "string")) {
    throw new CompileFailure(`${label}: positional translations require a columns array`);
  }
  return mapping.translations.map((values, index) => {
    if (!Array.isArray(values) || values.length !== mapping.columns.length) {
      throw new CompileFailure(`${label}: invalid positional translation ${index}`);
    }
    return Object.fromEntries(mapping.columns.map((column, columnIndex) => [column, values[columnIndex]]));
  });
}


function blockLayout(rows, label) {
  const capacities = new Set();
  const blockFiles = new Set();
  for (const row of rows) {
    let contexts;
    try {
      contexts = JSON.parse(row.entity_context);
    } catch (error) {
      throw new CompileFailure(`${label}: invalid entity_context JSON: ${error.message}`);
    }
    if (!Array.isArray(contexts) || contexts.length !== 1) {
      throw new CompileFailure(`${label}: each physical BRIEFING row must have one entity context`);
    }
    const capacity = /(?:^|;)capacity=(\d+)(?:;|$)/u.exec(contexts[0]);
    const blockFile = /(?:^|;)block_file=(0x[0-9A-Fa-f]+)(?:;|$)/u.exec(contexts[0]);
    if (!capacity || !blockFile) throw new CompileFailure(`${label}: entity context lacks block capacity/address`);
    capacities.add(integer(capacity[1], `${label} capacity`));
    blockFiles.add(blockFile[1].toUpperCase());
  }
  if (capacities.size !== 1 || blockFiles.size !== 1) {
    throw new CompileFailure(`${label}: block capacity/address differs within file_id`);
  }
  return { capacity: [...capacities][0], blockFileOffset: [...blockFiles][0] };
}


function appendReviewFlag(notes, reviewFlag) {
  const flag = String(reviewFlag ?? "").trim();
  if (!flag) return notes;
  return notes ? `${notes}; review_flag=${flag}` : `review_flag=${flag}`;
}


async function atomicWrite(target, text) {
  await fs.mkdir(path.dirname(target), { recursive: true });
  const temporary = `${target}.tmp`;
  await fs.writeFile(temporary, text, { encoding: "utf8" });
  await fs.rename(temporary, target);
}


async function main() {
  const args = parseArgs(process.argv);
  const templateRoot = path.join(args.root, "work", "luna_translation_templates", "BRIEFING");
  const mappingRoot = path.join(
    args.root,
    "work",
    "luna_translation_templates",
    "sol_translation_mappings",
    "BRIEFING",
  );
  const outputRoot = path.join(args.root, "translations", "briefing");
  const reportPath = path.join(
    args.root,
    "build",
    "translation",
    "briefing_production_merge_report.json",
  );

  const templateNames = (await fs.readdir(templateRoot)).filter((name) => name.endsWith(".csv")).sort();
  const mappingNames = (await fs.readdir(mappingRoot)).filter((name) => name.endsWith(".json")).sort();
  const expectedMappingNames = templateNames.map((name) => name.replace(/\.csv$/u, ".json"));
  if (JSON.stringify(mappingNames) !== JSON.stringify(expectedMappingNames)) {
    const templateSet = new Set(expectedMappingNames);
    const mappingSet = new Set(mappingNames);
    const missing = expectedMappingNames.filter((name) => !mappingSet.has(name));
    const extra = mappingNames.filter((name) => !templateSet.has(name));
    throw new CompileFailure(`template/mapping set mismatch: missing=${missing}, extra=${extra}`);
  }
  if (templateNames.length !== expected.files.all) {
    throw new CompileFailure(`expected ${expected.files.all} templates, found ${templateNames.length}`);
  }

  const existingOutputNames = await fs
    .readdir(outputRoot)
    .then((names) => names.filter((name) => name.endsWith(".csv")).sort())
    .catch((error) => (error.code === "ENOENT" ? [] : Promise.reject(error)));
  const unexpectedOutputs = existingOutputNames.filter((name) => !templateNames.includes(name));
  if (unexpectedOutputs.length) {
    throw new CompileFailure(`unexpected production CSVs: ${unexpectedOutputs.join(", ")}`);
  }

  const outputs = new Map();
  const corpusRows = [];
  const identitySet = new Set();
  const referenceSet = new Set();
  const capacityIssues = [];
  const contentIssues = [];
  let utf8LengthCorrections = 0;
  let fileRows = 0;
  let missionRows = 0;
  let fileCount = 0;
  let missionCount = 0;
  let csvInspectionFiles = 0;

  for (const templateName of templateNames) {
    const fileId = templateName.slice(0, -4);
    const family = fileId.startsWith("BRIEFING_FILES_BLOCK_")
      ? "BRIEFING_FILES"
      : fileId.startsWith("BRIEFING_MISSION_BLOCK_")
        ? "BRIEFING_MISSION"
        : "";
    if (!family) throw new CompileFailure(`unknown BRIEFING file_id family: ${fileId}`);

    const templateText = await fs.readFile(path.join(templateRoot, templateName), "utf8");
    const templateMatrix = await csvMatrix(templateText, "Template");
    const template = rowsFromMatrix(templateMatrix, templateName);
    if (JSON.stringify(template.headers) !== JSON.stringify(expectedTemplateColumns)) {
      throw new CompileFailure(`${templateName}: unexpected template columns`);
    }
    const mapping = JSON.parse(await fs.readFile(path.join(mappingRoot, `${fileId}.json`), "utf8"));
    if (mapping.file_id !== fileId || mapping.resource_class !== logicalResourceClass) {
      throw new CompileFailure(`${fileId}: mapping identity/resource class mismatch`);
    }
    const translationRows = normalizeTranslations(mapping, fileId);
    const translations = new Map();
    for (const item of translationRows) {
      const index = integer(item.unique_index, `${fileId} mapping unique_index`);
      if (translations.has(index)) throw new CompileFailure(`${fileId}: duplicate mapping index ${index}`);
      translations.set(index, item);
    }
    const expectedIndices = template.rows.map((_, index) => index);
    if (
      JSON.stringify([...translations.keys()].sort((left, right) => left - right)) !==
      JSON.stringify(expectedIndices)
    ) {
      throw new CompileFailure(`${fileId}: mapping coverage is not exact and contiguous`);
    }

    const layout = blockLayout(template.rows, fileId);
    const outputRows = [];
    let requiredBytes = 0;
    for (let index = 0; index < template.rows.length; index += 1) {
      const source = template.rows[index];
      const mappingRow = translations.get(index);
      if (source.file_id !== fileId || integer(source.unique_index, `${fileId} unique_index`) !== index) {
        throw new CompileFailure(`${fileId}: template identity mismatch at row ${index + 2}`);
      }
      if (!source.jpn_text) throw new CompileFailure(`${fileId}#${index}: empty jpn_text`);
      const jpnBytes = Buffer.byteLength(source.jpn_text, "utf8");
      if (integer(source.jpn_utf8_bytes, `${fileId}#${index} jpn_utf8_bytes`) !== jpnBytes) {
        throw new CompileFailure(`${fileId}#${index}: jpn_utf8_bytes mismatch`);
      }
      const cnText = mappingRow.cn_text;
      if (typeof cnText !== "string" || !cnText) {
        throw new CompileFailure(`${fileId}#${index}: empty or non-string cn_text`);
      }
      if (cnText.includes("\0")) throw new CompileFailure(`${fileId}#${index}: cn_text contains NUL`);
      const visibleCnText = cnText.replace(/<[^<>]*>/gu, "");
      if (kanaRe.test(visibleCnText)) {
        contentIssues.push(`${fileId}#${index}: visible cn_text contains kana`);
      }
      const control = controlError(source.jpn_text, cnText);
      if (control) contentIssues.push(`${fileId}#${index}: ${control}`);
      const cnBytes = Buffer.byteLength(cnText, "utf8");
      requiredBytes += cnBytes + 1;
      if (mappingRow.cn_utf8_bytes !== undefined && Number(mappingRow.cn_utf8_bytes) !== cnBytes) {
        utf8LengthCorrections += 1;
      }
      const identity = `${fileId}#${index}`;
      if (identitySet.has(identity)) throw new CompileFailure(`duplicate corpus identity: ${identity}`);
      identitySet.add(identity);
      if (!source.first_reference_index || referenceSet.has(source.first_reference_index)) {
        throw new CompileFailure(`${identity}: empty or duplicate physical reference identity`);
      }
      referenceSet.add(source.first_reference_index);
      const row = Object.fromEntries(productionColumns.map((column) => [column, source[column] ?? ""]));
      Object.assign(row, {
        cn_text: cnText,
        cn_control_tokens: allTokens(cnText).join(" | "),
        control_structure_status: "MATCH",
        cn_utf8_bytes: String(cnBytes),
        translation_status: "APPROVED",
        build_status: "READY",
        ingame_status: "NOT_TESTED",
        notes: appendReviewFlag(source.notes, mappingRow.review_flag),
      });
      outputRows.push(row);
      corpusRows.push({ file_id: fileId, unique_index: String(index), jpn_text: source.jpn_text, cn_text: cnText });
    }
    const jpnRequiredBytes = template.rows.reduce(
      (total, row) => total + Buffer.byteLength(row.jpn_text, "utf8") + 1,
      0,
    );
    if (jpnRequiredBytes > layout.capacity) {
      throw new CompileFailure(`${fileId}: clean JPN text exceeds declared block capacity`);
    }
    const capacityStatus = requiredBytes <= layout.capacity ? "NORMAL_FIT" : "HARD_OVERFLOW";
    if (capacityStatus === "HARD_OVERFLOW") {
      for (const row of outputRows) row.build_status = "BLOCKED_CAPACITY";
      capacityIssues.push({
        file_id: fileId,
        block_file_offset: layout.blockFileOffset,
        text_capacity: layout.capacity,
        required_bytes: requiredBytes,
        over_bytes: requiredBytes - layout.capacity,
      });
    }

    const outputText = encodeCsv(productionColumns, outputRows);
    const outputMatrix = await csvMatrix(outputText, "Production");
    if (
      outputMatrix.rowCount !== outputRows.length + 1 ||
      outputMatrix.columnCount !== productionColumns.length
    ) {
      throw new CompileFailure(`${fileId}: CSV dimension check failed`);
    }
    const roundTrip = rowsFromMatrix(outputMatrix, `${fileId} production round-trip`);
    if (JSON.stringify(roundTrip.headers) !== JSON.stringify(productionColumns)) {
      throw new CompileFailure(`${fileId}: production header round-trip mismatch`);
    }
    for (let index = 0; index < outputRows.length; index += 1) {
      for (const column of productionColumns) {
        if (roundTrip.rows[index][column] !== String(outputRows[index][column] ?? "")) {
          throw new CompileFailure(`${fileId}#${index}: CSV round-trip differs at ${column}`);
        }
        if (formulaErrorRe.test(roundTrip.rows[index][column])) {
          throw new CompileFailure(`${fileId}#${index}: spreadsheet error token at ${column}`);
        }
      }
    }
    if (representativeFileIds.has(fileId)) {
      const inspected = inspectCsvRegion(
        outputMatrix.values,
        `A1:U${Math.min(outputMatrix.rowCount, 4)}`,
      );
      if (!inspected.ndjson) throw new CompileFailure(`${fileId}: CSV inspection returned no data`);
      csvInspectionFiles += 1;
    }
    outputs.set(path.join(outputRoot, templateName), outputText);
    if (family === "BRIEFING_FILES") {
      fileCount += 1;
      fileRows += outputRows.length;
    } else {
      missionCount += 1;
      missionRows += outputRows.length;
    }
  }

  const actual = {
    files: { all: outputs.size, briefingFiles: fileCount, briefingMission: missionCount },
    rows: { all: corpusRows.length, briefingFiles: fileRows, briefingMission: missionRows },
  };
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new CompileFailure(`scope mismatch: expected=${JSON.stringify(expected)} actual=${JSON.stringify(actual)}`);
  }
  if (csvInspectionFiles !== representativeFileIds.size) {
    throw new CompileFailure(`expected ${representativeFileIds.size} representative CSV inspections`);
  }
  if (contentIssues.length) {
    throw new CompileFailure(
      `translation content errors (${contentIssues.length}): ${contentIssues.slice(0, 20).join("; ")}`,
    );
  }
  if (capacityIssues.length) {
    throw new CompileFailure(
      `BRIEFING capacity overflow in ${capacityIssues.length} block(s): ` +
        capacityIssues
          .slice(0, 20)
          .map((item) => `${item.file_id}(+${item.over_bytes})`)
          .join(", "),
    );
  }

  const report = {
    status: "PASS",
    scope: "current frozen JPN BRIEFING corpus",
    physical_directory: "BRIEFING",
    logical_resource_class: logicalResourceClass,
    production_directory: "translations/briefing",
    template_files: actual.files.all,
    mapping_files: mappingNames.length,
    production_files: actual.files.all,
    translation_rows: actual.rows.all,
    briefing_files: { blocks: actual.files.briefingFiles, rows: actual.rows.briefingFiles },
    briefing_mission: { blocks: actual.files.briefingMission, rows: actual.rows.briefingMission },
    identity_count: identitySet.size,
    physical_reference_count: referenceSet.size,
    missing_mappings: 0,
    extra_mappings: 0,
    missing_rows: 0,
    duplicate_rows: 0,
    empty_jpn_rows: 0,
    empty_cn_rows: 0,
    kana_rows: 0,
    control_errors: 0,
    utf8_errors: 0,
    mapping_utf8_length_fields_corrected: utf8LengthCorrections,
    capacity: {
      normal_fit_blocks: actual.files.all,
      hard_overflow_blocks: 0,
      issues: capacityIssues,
    },
    csv_roundtrip_files: actual.files.all,
    csv_inspected_files: csvInspectionFiles,
    spreadsheet_error_tokens: 0,
    hashes: {
      jpn_identity_sha256: stableIdentity(corpusRows, ["file_id", "unique_index", "jpn_text"]),
      translation_identity_sha256: stableIdentity(corpusRows, [
        "file_id",
        "unique_index",
        "jpn_text",
        "cn_text",
      ]),
    },
    output_columns: productionColumns,
    dat_or_key_modified: false,
  };
  const reportText = `${JSON.stringify(report, null, 2)}\n`;

  if (args.mode === "write") {
    for (const [target, text] of outputs) await atomicWrite(target, text);
    await atomicWrite(reportPath, reportText);
  } else {
    for (const [target, text] of outputs) {
      let existing;
      try {
        existing = await fs.readFile(target, "utf8");
      } catch (error) {
        if (error.code === "ENOENT") throw new CompileFailure(`missing production CSV: ${target}`);
        throw error;
      }
      if (existing !== text) throw new CompileFailure(`production CSV differs from compiler output: ${target}`);
    }
    const existingReport = await fs.readFile(reportPath, "utf8").catch((error) => {
      if (error.code === "ENOENT") throw new CompileFailure(`missing merge report: ${reportPath}`);
      throw error;
    });
    if (existingReport !== reportText) throw new CompileFailure("merge report differs from compiler output");
  }

  console.log(`MODE=${args.mode.toUpperCase()}`);
  console.log(`PRODUCTION_FILES=${actual.files.all}`);
  console.log(`TRANSLATION_ROWS=${actual.rows.all}`);
  console.log(`BRIEFING_FILES=${actual.files.briefingFiles}/${actual.rows.briefingFiles}`);
  console.log(`BRIEFING_MISSION=${actual.files.briefingMission}/${actual.rows.briefingMission}`);
  console.log(`CONTROL_ERRORS=0`);
  console.log(`KANA_ROWS=0`);
  console.log(`HARD_OVERFLOW_BLOCKS=0`);
  console.log(`CSV_ROUNDTRIP_FILES=${actual.files.all}`);
  console.log(`CSV_INSPECTED_FILES=${csvInspectionFiles}`);
  console.log(`REPORT=${reportPath}`);
}


try {
  await main();
} catch (error) {
  console.error(`ERROR=${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
}
