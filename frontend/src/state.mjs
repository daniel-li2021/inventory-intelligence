export const pages = [
  "overview",
  "explore",
  "investigate",
  "compare",
  "decide",
  "history",
  "execution",
  "evaluation",
];
const fields = [
  "snapshot",
  "item",
  "type",
  "style",
  "color",
  "size",
  "location",
  "status",
  "q",
  "view",
  "archive",
  "schema",
  "scenario",
  "sort",
  "direction",
];
export function parseRoute(hash) {
  const [path, search = ""] = hash.replace(/^#\/?/, "").split("?");
  const params = new URLSearchParams(search);
  const state = { page: pages.includes(path) ? path : "overview", offset: 0 };
  for (const key of fields) {
    const value = params.get(key);
    if (key === "scenario" && value) {
      state.scenario =
        value.length <= 4096 ? value : "invalid-shared-assumptions";
      continue;
    }
    if (value && value.length <= 256) state[key] = value;
  }
  const offset = Number(params.get("offset"));
  state.offset =
    Number.isSafeInteger(offset) && offset >= 0 && offset <= 10000 ? offset : 0;
  return state;
}
export function routeHash(state) {
  const params = new URLSearchParams();
  for (const key of fields) if (state[key]) params.set(key, String(state[key]));
  if (state.offset) params.set("offset", String(state.offset));
  return `#/${pages.includes(state.page) ? state.page : "overview"}${params.size ? "?" + params : ""}`;
}
export function preset(state, type) {
  return {
    ...state,
    page: "explore",
    type,
    style: "",
    color: "",
    size: "",
    location: "",
    status: "",
    q: "",
    offset: 0,
  };
}
export function bindingMismatch(state, context) {
  return Boolean(
    (state.archive && state.archive !== context.archive_id) ||
      (state.schema && state.schema !== context.schema_version),
  );
}
export function saveView(state, context) {
  return {
    ...state,
    ...(context.cutoff ? { snapshot: state.snapshot || context.cutoff } : {}),
    archive: context.archive_id,
    schema: context.schema_version,
  };
}
export function readSavedViews(serialized) {
  try {
    const value = JSON.parse(serialized || "[]");
    if (!Array.isArray(value)) return [];
    return value
      .filter(
        (v) =>
          v &&
          typeof v.name === "string" &&
          v.name.length <= 100 &&
          v.state &&
          typeof v.state === "object" &&
          !Array.isArray(v.state),
      )
      .slice(-10)
      .map((v) => ({ name: v.name, state: parseRoute(routeHash(v.state)) }));
  } catch {
    return [];
  }
}
export function scenarioOverrides(draft) {
  const result = {};
  for (const [key, value] of Object.entries(draft)) {
    if (
      typeof value !== "string" ||
      !/^\d+$/.test(value) ||
      !Number.isSafeInteger(Number(value))
    )
      throw Error("Scenario assumptions must be whole nonnegative integers.");
    result[key] = Number(value);
  }
  return result;
}
export function readSharedScenario(text, allowed) {
  if (!text) return {};
  let value;
  try {
    value = JSON.parse(text);
  } catch {
    throw Error(
      "Invalid shared assumptions. Reset assumptions to use the saved baseline.",
    );
  }
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw Error(
      "Invalid shared assumptions. Reset assumptions to use the saved baseline.",
    );
  if (Object.keys(value).some((key) => !allowed.includes(key)))
    throw Error(
      "Shared assumptions contain an unsupported control. Reset assumptions to use the saved baseline.",
    );
  scenarioOverrides(value);
  return value;
}
export function requestQuery(state) {
  const params = new URLSearchParams({
    page: String(Math.floor((state.offset || 0) / 20) + 1),
    page_size: "20",
    sort: state.sort || "priority",
  });
  for (const [field, key] of [
    ["snapshot", "cutoff"],
    ["type", "category"],
    ["style", "style_id"],
    ["color", "color"],
    ["size", "size"],
    ["location", "warehouse_id"],
    ["status", "status"],
    ["q", "search"],
  ])
    if (state[field]) params.set(key, String(state[field]));
  return params;
}
