import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import assert from "node:assert/strict";
const base = "../src/inventory_intelligence/product_static/";
const files = readdirSync(base);
const sums = { js: 0, css: 0 };
for (const file of files) {
  const kind = file.split(".").pop();
  if (kind in sums) sums[kind] += gzipSync(readFileSync(base + file)).length;
}
assert.ok(sums.js <= 250 * 1024, `JS gzip budget exceeded: ${sums.js}`);
assert.ok(sums.css <= 40 * 1024, `CSS gzip budget exceeded: ${sums.css}`);
const receipt = {
  frozen_budgets_bytes: {
    js_gzip: 256000,
    css_gzip: 40960,
    initial_data: 204800,
  },
  measured_bytes: { js_gzip: sums.js, css_gzip: sums.css },
  files,
};
writeFileSync("bundle-receipt.json", JSON.stringify(receipt, null, 2) + "\n");
console.log(JSON.stringify(receipt));
