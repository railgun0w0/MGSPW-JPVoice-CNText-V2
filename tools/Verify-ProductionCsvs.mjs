#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Workbook } from "@oai/artifact-tool";


const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");
const samples = [
  ["YPK_GTT", "translations/ypk_gtt/1C79F2AD.csv", 21],
  ["OHD", "translations/ohd/1E4C1146.csv", 21],
  ["LOOSE_OLANG", "translations/loose_olang/0005EE2F.csv", 21],
  ["STAGEDAT_OLANG", "translations/stagedat_olang/LANG_BRIEFING.OLANG.csv", 21],
  ["SLOT_OLANG", "translations/slot_olang/5D3AF52D.csv", 21],
  ["WORKLIST", "build/translation/translation_worklist.csv", 19],
  ["CAPACITY", "build/translation/fixed_capacity_issues.csv", 18],
];

let totalRows = 0;
for (const [label, relativePath, expectedColumns] of samples) {
  const text = (await fs.readFile(path.join(root, relativePath), "utf8")).replace(/^\uFEFF/, "");
  const workbook = await Workbook.fromCSV(text, { sheetName: label.slice(0, 24) });
  const sheet = workbook.worksheets.getItem(label.slice(0, 24));
  const used = sheet.getUsedRange(true);
  if (!used || used.rowCount < 2 || used.columnCount !== expectedColumns) {
    throw new Error(
      `${label}: unexpected dimensions ${used?.rowCount ?? 0}x${used?.columnCount ?? 0}`
    );
  }
  const inspected = await workbook.inspect({
    kind: "region",
    sheetId: label.slice(0, 24),
    range: `A1:${String.fromCharCode(64 + Math.min(expectedColumns, 26))}${Math.min(used.rowCount, 4)}`,
    maxChars: 3000,
  });
  if (!inspected.ndjson) throw new Error(`${label}: artifact-tool inspection returned no data`);
  totalRows += used.rowCount - 1;
  console.log(`${label}_ROWS=${used.rowCount - 1}`);
}
console.log(`SAMPLED_ROWS=${totalRows}`);
console.log("ARTIFACT_TOOL_VALIDATION=PASS");
