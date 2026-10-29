import test from "node:test";
import assert from "node:assert/strict";
import { readJSON } from "../src/request.mjs";

test("read failures give an explicit recovery and retain the HTTP status", async t => {
  for (const [status, hint] of [[422, /another item or cutoff/], [409, /current archive/], [429, /Wait a moment/], [503, /Retry shortly/]]) {
    t.mock.method(globalThis, "fetch", async () => new Response("{}", { status }));
    await assert.rejects(readJSON("/saved"), error => hint.test(error.message) && error.message.includes(String(status)));
    t.mock.restoreAll();
  }
});

test("read timeouts finish with recovery guidance; cancellation stays cancellation", async t => {
  t.mock.method(globalThis, "fetch", async (_path, options) => new Promise((_resolve, reject) => {
    const abort = () => reject(new DOMException("Aborted", "AbortError"));
    if (options.signal.aborted) abort();
    else options.signal.addEventListener("abort", abort, {once: true});
  }));
  await assert.rejects(readJSON("/slow", undefined, 5), /took too long/);
  const controller = new AbortController();
  const pending = readJSON("/old", controller.signal);
  controller.abort();
  await assert.rejects(pending, {name: "AbortError"});
  await assert.rejects(readJSON("/already-cancelled", controller.signal), {name: "AbortError"});
});

test("reads preserve exact JSON and use no-store; network failures explain retry", async t => {
  const payload = {quantity: {numerator: "17", denominator: "3"}, source: "original"};
  t.mock.method(globalThis, "fetch", async (_path, options) => {
    assert.equal(options.cache, "no-store");
    return Response.json(payload);
  });
  assert.deepEqual(await readJSON("/saved"), payload);
  t.mock.restoreAll();
  t.mock.method(globalThis, "fetch", async () => { throw new TypeError("Failed to fetch"); });
  await assert.rejects(readJSON("/offline"), /Check your connection, then retry/);
});
