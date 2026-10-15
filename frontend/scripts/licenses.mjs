import { readFileSync, writeFileSync } from "node:fs";
const lock = JSON.parse(readFileSync("package-lock.json"));
const inventory = Object.entries(lock.packages)
  .filter(([path]) => path)
  .map(([path, p]) => ({
    package: path.replace(/^.*node_modules\//, ""),
    version: p.version,
    license: p.license || "See package license",
    development_only: Boolean(p.dev),
    integrity: p.integrity,
  }));
writeFileSync(
  "dependency-licenses.json",
  JSON.stringify(
    {
      source:
        "npm lockfile metadata; React MIT; Lucide ISC; TypeScript Apache-2.0",
      packages: inventory,
    },
    null,
    2,
  ) + "\n",
);
const notices = [
  "React and its supporting runtime are distributed under the following licenses.\n",
];
for (const name of ["react", "react-dom", "scheduler", "lucide-react"]) {
  const metadata = JSON.parse(
    readFileSync(`node_modules/${name}/package.json`),
  );
  notices.push(
    `${name} ${metadata.version}\n${"=".repeat(60)}\n${readFileSync(`node_modules/${name}/LICENSE`, "utf8")}`,
  );
}
writeFileSync(
  "../src/inventory_intelligence/product_static/THIRD_PARTY_LICENSES.txt",
  notices.join("\n\n").trimEnd() + "\n",
);
