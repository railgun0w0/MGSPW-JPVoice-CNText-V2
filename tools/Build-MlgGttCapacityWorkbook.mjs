import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = String.raw`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2`;
const inputPath = `${root}\\build\\analysis\\mlg_gtt_capacity_analysis.json`;
const outputPath = `${root}\\build\\analysis\\mlg_gtt_capacity_analysis.xlsx`;
const data = JSON.parse(await fs.readFile(inputPath, "utf8"));

const workbook = Workbook.create();
const fontName = "Arial";
const dark = "#1F4E78";
const light = "#D9EAF7";
const warning = "#FFF2CC";
const textColor = "#1F2937";

function colName(number) {
  let result = "";
  for (let n = number; n > 0; n = Math.floor((n - 1) / 26)) {
    result = String.fromCharCode(65 + ((n - 1) % 26)) + result;
  }
  return result;
}

function safeValue(value) {
  if (value === null || value === undefined) return null;
  if (typeof value === "string" && value.startsWith("=")) return `'${value}`;
  return value;
}

function addDataSheet(name, title, subtitle, rows, columns, tableName) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  sheet.getRange("A1").values = [[title]];
  sheet.getRange("A1").format.font = { name: fontName, size: 15, bold: true, color: dark };
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A2").format.font = { name: fontName, size: 10, italic: true, color: "#4B5563" };
  const matrix = [columns, ...rows.map((row) => columns.map((column) => safeValue(row[column])) )];
  const endColumn = colName(columns.length);
  const endRow = 3 + matrix.length;
  sheet.getRangeByIndexes(3, 0, matrix.length, columns.length).values = matrix;
  const table = sheet.tables.add(`A4:${endColumn}${endRow}`, true, tableName);
  table.style = "TableStyleMedium2";
  sheet.getRange(`A4:${endColumn}4`).format = {
    fill: dark,
    font: { name: fontName, size: 10, bold: true, color: "#FFFFFF" },
    wrapText: true,
    verticalAlignment: "center",
  };
  if (rows.length) {
    sheet.getRange(`A5:${endColumn}${endRow}`).format.font = {
      name: fontName,
      size: 9,
      color: textColor,
    };
    sheet.getRange(`A5:${endColumn}${endRow}`).format.verticalAlignment = "top";
  }
  sheet.freezePanes.freezeRows(4);
  sheet.freezePanes.freezeColumns(Math.min(4, columns.length));
  sheet.getRange(`A1:${endColumn}${Math.min(endRow, 40)}`).format.autofitColumns();
  sheet.getRange(`A1:${endColumn}${Math.min(endRow, 40)}`).format.autofitRows();
  for (let index = 0; index < columns.length; index += 1) {
    const column = columns[index];
    const range = sheet.getRange(`${colName(index + 1)}:${colName(index + 1)}`);
    if (column.includes("texts") || column.includes("boundaries") || column === "cn_occurrences") {
      range.format.columnWidth = 42;
      range.format.wrapText = true;
    } else if (column === "classification" || column === "file_id") {
      range.format.columnWidth = 22;
    } else {
      range.format.columnWidth = 15;
    }
  }
  return sheet;
}

const summary = workbook.worksheets.add("Summary");
summary.showGridLines = false;
summary.getRange("A1").values = [["MLG GTT capacity behavior"]];
summary.getRange("A1").format.font = { name: fontName, size: 16, bold: true, color: dark };
summary.getRange("A2").values = [["MLG original versus existing MLG Chinese patch; ENG lane YPK payload variants deduplicated by complete bytes"]];
summary.getRange("A2").format.font = { name: fontName, size: 10, italic: true, color: "#4B5563" };

const metricRows = [
  ["Metric", "Value"],
  ["UNIQUE_ENG_YPK", data.summary.UNIQUE_ENG_YPK],
  ["CN_PAYLOAD_VARIANTS", data.summary.CN_PAYLOAD_VARIANTS],
  ["TOTAL_RECORD_PAIRS", data.summary.TOTAL_RECORD_PAIRS],
  ["SAME_FRAME_FIT", data.summary.SAME_FRAME_FIT],
  ["ALIGNMENT_SPILL", data.summary.ALIGNMENT_SPILL],
  ["FRAME_GREW", data.summary.FRAME_GREW],
  ["FRAME_SHRANK", data.summary.FRAME_SHRANK],
  ["SAME_FRAME_APPARENT_OVERFLOW", data.summary.SAME_FRAME_APPARENT_OVERFLOW],
  ["TOPOLOGY_CHANGED", data.summary.TOPOLOGY_CHANGED],
  ["RECORD_COUNT_CHANGED", data.summary.RECORD_COUNT_CHANGED],
  ["UNCLASSIFIED", data.summary.UNCLASSIFIED],
  ["YPK_SIZE_GREW", data.summary.YPK_SIZE_GREW],
  ["MAX_YPK_SIZE_GROWTH", data.summary.MAX_YPK_SIZE_GROWTH],
  ["MAX_FRAME_GREW_ALIGNED_BYTES", data.summary.MAX_FRAME_GREW_ALIGNED_BYTES],
  ["MAX_FRAME_GREW_RECORD_SIZE_BYTES", data.summary.MAX_FRAME_GREW_RECORD_SIZE_BYTES],
  ["MAX_ALIGNMENT_SPILL_BYTES", data.summary.MAX_ALIGNMENT_SPILL_BYTES],
];
summary.getRange(`A4:B${3 + metricRows.length}`).values = metricRows;
const summaryTable = summary.tables.add(`A4:B${3 + metricRows.length}`, true, "CapacitySummary");
summaryTable.style = "TableStyleMedium2";
summary.getRange("D4:E9").values = [
  ["Question", "Observed result"],
  ["Uses original alignment slack", "Yes"],
  ["Grows GTT record/frame", "No observed case"],
  ["Shifts following records", "No observed case"],
  ["Grows complete YPK", "No observed case"],
  ["Answer", "A. Only uses original record alignment slack"],
];
summary.getRange("D4:E4").format = {
  fill: dark,
  font: { name: fontName, size: 10, bold: true, color: "#FFFFFF" },
};
summary.getRange("D5:E9").format.font = { name: fontName, size: 10, color: textColor };
summary.getRange("D9:E9").format = { fill: warning, font: { name: fontName, size: 10, bold: true, color: textColor } };
summary.getRange("A4:B4").format = {
  fill: dark,
  font: { name: fontName, size: 10, bold: true, color: "#FFFFFF" },
};
summary.getRange("A5:B20").format.font = { name: fontName, size: 10, color: textColor };
summary.getRange("A:A").format.columnWidth = 39;
summary.getRange("B:B").format.columnWidth = 18;
summary.getRange("D:D").format.columnWidth = 31;
summary.getRange("E:E").format.columnWidth = 43;
summary.getRange("A1:E20").format.autofitRows();

const pairColumns = [
  "file_id", "cn_variant", "cn_occurrences", "record_index", "classification",
  "eng_offset", "cn_offset", "offset_delta", "eng_segment_count", "cn_segment_count",
  "eng_header_size", "cn_header_size", "eng_record_size", "cn_record_size",
  "record_size_delta", "eng_aligned_size", "cn_aligned_size", "aligned_size_delta",
  "eng_nominal_capacity", "eng_aligned_capacity", "eng_alignment_slack", "cn_required",
  "slack_bytes_used", "next_eng_offset", "next_cn_offset", "next_offset_delta",
  "subsequent_record_shifted", "eng_ypk_size", "cn_ypk_size", "ypk_size_delta",
  "ypk_size_grew", "eng_texts", "cn_texts", "eng_boundaries", "cn_boundaries",
];

const exceptions = addDataSheet(
  "Exceptions",
  "Capacity and topology exceptions",
  "All ALIGNMENT_SPILL, FRAME_GREW, FRAME_SHRANK, SAME_FRAME_APPARENT_OVERFLOW and TOPOLOGY_CHANGED record pairs",
  data.exceptions,
  pairColumns,
  "ExceptionRecords",
);
exceptions.getRange("E:E").conditionalFormats.add("containsText", {
  text: "ALIGNMENT_SPILL",
  format: { fill: warning, font: { bold: true, color: "#7F6000" } },
});

addDataSheet(
  "Record pairs",
  "All deduplicated GTT record pairs",
  "One row per corresponding record in each unique MLG Chinese payload variant",
  data.record_pairs,
  pairColumns,
  "AllRecordPairs",
);

const variantColumns = [
  "file_id", "cn_variant", "cn_occurrences", "eng_record_count", "cn_record_count",
  "eng_ypk_size", "cn_ypk_size", "ypk_size_delta", "ypk_size_grew",
];
addDataSheet(
  "YPK variants",
  "Deduplicated Chinese YPK payload variants",
  "Complete payload bytes define a variant; repeated physical occurrences are shown in cn_occurrences",
  data.ypk_variants,
  variantColumns,
  "YpkVariants",
);

const countColumns = [
  "file_id", "cn_variant", "cn_occurrences", "eng_record_count", "cn_record_count",
  "record_count_delta", "eng_ypk_size", "cn_ypk_size", "ypk_size_delta", "classification",
];
const countRows = data.record_count_changes.length
  ? data.record_count_changes
  : [{ classification: "No RECORD_COUNT_CHANGED variants" }];
addDataSheet(
  "Record counts",
  "Record-count differences",
  "This sheet lists every YPK variant whose ENG and CN GTT record counts differ",
  countRows,
  countColumns,
  "RecordCountChanges",
);

await fs.mkdir(`${root}\\build\\analysis`, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);

const summaryInspect = await workbook.inspect({
  kind: "table",
  range: "Summary!A1:E20",
  include: "values,formulas",
  tableMaxRows: 20,
  tableMaxCols: 6,
});
console.log(summaryInspect.ndjson);
const errorInspect = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errorInspect.ndjson);
for (const [sheetName, range] of [
  ["Summary", "A1:E20"],
  ["Exceptions", "A1:AI20"],
  ["Record pairs", "A1:AI20"],
  ["YPK variants", "A1:I20"],
  ["Record counts", "A1:J8"],
]) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(
    `${root}\\build\\analysis\\preview_${sheetName.replaceAll(" ", "_")}.png`,
    new Uint8Array(await preview.arrayBuffer()),
  );
}
console.log(JSON.stringify({ outputPath, sheets: 5, recordPairs: data.record_pairs.length, exceptions: data.exceptions.length }));
