import test from "node:test";
import assert from "node:assert/strict";
import {
  parseRoute,
  routeHash,
  preset,
  bindingMismatch,
  saveView,
  requestQuery,
  readSavedViews,
  scenarioOverrides,
  readSharedScenario,
} from "../src/state.mjs";
test("shared routes preserve exact key/cutoff/scenario and bindings through reload", () => {
  const view = {
    page: "compare",
    item: "sku/a:west",
    snapshot: "2026-10-01",
    scenario: "demand-spike",
    location: "West",
    archive: "digest",
    schema: "v1",
    offset: 20,
  };
  assert.deepEqual(parseRoute(routeHash(view)), view);
});
test("manual/preset query uses identical canonical state", () => {
  const base = {
    page: "overview",
    offset: 40,
    q: "a",
    style: "tee",
    location: "West",
  };
  const view = preset(base, "risk");
  assert.equal(requestQuery(view).get("category"), "risk");
  assert.equal(requestQuery(view).get("page"), "1");
  assert.equal(requestQuery(view).has("warehouse_id"), false);
});
test("saved views explicitly block changed archive and schema", () => {
  const context = { archive_id: "a", schema_version: "v1" };
  const saved = saveView({ page: "history", offset: 0 }, context);
  assert.equal(bindingMismatch(saved, context), false);
  assert.equal(bindingMismatch(saved, { ...context, archive_id: "b" }), true);
  assert.equal(
    bindingMismatch(saved, { ...context, schema_version: "v2" }),
    true,
  );
});
test("malformed URL cannot select an arbitrary page or unbounded offset", () => {
  assert.equal(parseRoute("#/garbage?offset=1e99").page, "overview");
  assert.equal(parseRoute("#/explore?offset=-2").offset, 0);
  assert.equal(parseRoute("#/explore?q=" + "x".repeat(257)).q, undefined);
});

test("scenario values reject coercion, fractions, negatives and unsafe integers", () => {
  assert.deepEqual(
    scenarioOverrides({ lead_days: "7", demand_percent: "150" }),
    { lead_days: 7, demand_percent: 150 },
  );
  for (const value of [
    true,
    1,
    null,
    "-1",
    "1.5",
    "1e2",
    "9007199254740992",
    "",
  ])
    assert.throws(() => scenarioOverrides({ lead_days: value }));
});
test("corrupt browser saved views are ignored and canonicalized", () => {
  assert.deepEqual(readSavedViews('{"bad":"data"}'), []);
  assert.deepEqual(readSavedViews("not json"), []);
  assert.deepEqual(
    readSavedViews(
      JSON.stringify([
        {
          name: "History",
          state: { page: "history", item: "sku|site", offset: 999999 },
        },
      ]),
    )[0].state,
    { page: "history", item: "sku|site", offset: 0 },
  );
});

test("invalid shared scenarios fail closed instead of silently becoming baseline", () => {
  const allowed = ["lead_days"];
  assert.deepEqual(readSharedScenario('{"lead_days":"7"}', allowed), {
    lead_days: "7",
  });
  for (const text of [
    "garbage",
    "[]",
    "null",
    '{"lead_days":true}',
    '{"lead_days":"-1"}',
    '{"purchase":"100"}',
  ])
    assert.throws(() => readSharedScenario(text, allowed));
  assert.throws(() =>
    readSharedScenario(
      parseRoute("#/compare?scenario=" + "x".repeat(4097)).scenario,
      allowed,
    ),
  );
});

test("a saved default view freezes the actual cutoff", () => {
  assert.equal(
    saveView(
      { page: "explore", offset: 0 },
      { archive_id: "a", schema_version: "v1", cutoff: "2026-01-19" },
    ).snapshot,
    "2026-01-19",
  );
});
