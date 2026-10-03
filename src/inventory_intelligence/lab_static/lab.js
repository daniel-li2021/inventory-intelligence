"use strict";

// This layer renders structured evidence. All business quantities and deltas
// are supplied by the Python adapter; arithmetic below is display geometry only.
(() => {
  const $ = (id) => document.getElementById(id);
  const colors = { baseline: "#61776b", scenario: "#245f51", baselineBacklog: "#947154", backlog: "#b65329", demand: "#366b8f" };
  let result = null;
  let defaults = null;
  let schema = null;
  let busy = false;
  let requestId = 0;
  let controller = null;
  let returnFocus = null;
  const form = $("scenario-form");

  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  }
  function clear(id) { const node = $(id); node.replaceChildren(); return node; }
  function exact(value) { return value === null || value === undefined ? "Not assessable" : String(value); }
  function numeric(value) {
    if (value === null || value === undefined || value === "") return null;
    if (typeof value === "number") return Number.isFinite(value) ? value : null;
    const parts = String(value).split("/");
    const answer = Number(parts[0]) / (parts.length === 2 ? Number(parts[1]) : 1);
    return Number.isFinite(answer) ? answer : null;
  }
  function percentage(value) {
    const answer = numeric(value);
    return answer === null ? "Undefined" : `${(answer * 100).toFixed(1)}%`;
  }
  function deltaText(value, rate = false) {
    const answer = numeric(value);
    if (answer === null) return "Δ Not assessable";
    const display = rate ? `${(answer * 100).toFixed(1)} percentage points` : exact(value);
    return `Δ ${answer > 0 ? "+" : ""}${display}`;
  }
  function codeBlock(value) {
    return el("pre", JSON.stringify(value, null, 2), "evidence-json");
  }
  function empty(id, text = "Scenario evidence is incomplete. This output is not assessable; no value is substituted.") {
    clear(id).append(el("p", text, "empty-state"));
  }
  function table(target, caption, headers, rows, rowLabels = false) {
    const wrapper = el("div", null, "table-scroll");
    wrapper.tabIndex = 0;
    wrapper.setAttribute("role", "region");
    wrapper.setAttribute("aria-label", caption || "Scrollable evidence table");
    const node = el("table");
    if (caption) node.append(el("caption", caption));
    const head = el("thead");
    const headRow = el("tr");
    headers.forEach((heading) => { const cell = el("th", heading); cell.scope = "col"; headRow.append(cell); });
    head.append(headRow);
    node.append(head);
    const body = el("tbody");
    rows.forEach((values) => {
      const row = el("tr");
      values.forEach((value, index) => {
        const cell = el(rowLabels && index === 0 ? "th" : "td", value === null || value === undefined ? "Undefined" : value);
        if (rowLabels && index === 0) cell.scope = "row";
        row.append(cell);
      });
      body.append(row);
    });
    node.append(body);
    wrapper.append(node);
    target.append(wrapper);
    return node;
  }

  function chart(id, description, labels, series) {
    const root = clear(id);
    const valid = series.filter((entry) => entry.values.some((value) => numeric(value) !== null));
    if (!valid.length) { root.append(el("p", "No assessable trajectory to display.", "empty-state")); return; }
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 760 230");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", description + ". Exact values are available in the table below.");
    svg.classList.add("chart");
    const title = document.createElementNS(ns, "title"); title.textContent = description; svg.append(title);
    const values = valid.flatMap((entry) => entry.values.map(numeric).filter((value) => value !== null));
    const low = Math.min(0, ...values), high = Math.max(1, ...values);
    const range = high - low;
    const top = 18, bottom = 194, left = 48, right = 743;
    const y = (value) => bottom - ((value - low) / range) * (bottom - top);
    const x = (index) => labels.length < 2 ? left : left + index / (labels.length - 1) * (right - left);
    function svgEl(tag, attrs, text) {
      const node = document.createElementNS(ns, tag);
      Object.entries(attrs).forEach(([name, value]) => node.setAttribute(name, String(value)));
      if (text !== undefined) node.textContent = text;
      svg.append(node); return node;
    }
    for (let index = 0; index <= 4; index++) {
      const value = low + range * index / 4;
      svgEl("line", { x1: left, x2: right, y1: y(value), y2: y(value), class: "grid" });
      svgEl("text", { x: left - 9, y: y(value) + 3, "text-anchor": "end" }, Number(value.toFixed(1)));
    }
    if (low < 0) svgEl("line", { x1: left, x2: right, y1: y(0), y2: y(0), class: "zero-line" });
    [0, Math.floor((labels.length - 1) / 2), labels.length - 1].filter((value, index, all) => value >= 0 && all.indexOf(value) === index).forEach((index) => {
      svgEl("text", { x: x(index), y: 220, "text-anchor": index === 0 ? "start" : index === labels.length - 1 ? "end" : "middle" }, labels[index]);
    });
    valid.forEach((entry) => {
      let path = "", joined = false;
      entry.values.forEach((value, index) => {
        const number = numeric(value);
        if (number === null) { joined = false; return; }
        path += `${joined ? "L" : "M"}${x(index).toFixed(2)},${y(number).toFixed(2)} `;
        joined = true;
      });
      svgEl("path", { d: path, fill: "none", stroke: entry.color, "stroke-width": 2.4, "stroke-linejoin": "round", "stroke-linecap": "round", ...(entry.longDashed ? { "stroke-dasharray": "12 5" } : entry.dotted ? { "stroke-dasharray": "1 5" } : entry.dashed ? { "stroke-dasharray": "5 4" } : {}) });
      if (entry.values.length === 1) svgEl("circle", { cx: x(0), cy: y(numeric(entry.values[0])), r: 3, fill: entry.color });
    });
    root.append(svg);
    const legend = el("div", null, "chart-legend");
    valid.forEach((entry) => { const item = el("span", entry.label, "legend-item" + (entry.longDashed ? " long-dashed" : entry.dotted ? " dotted" : entry.dashed ? " dashed" : "")); item.style.setProperty("--series-color", entry.color); legend.append(item); });
    root.append(legend);
  }

  const groups = [
    ["Demand & service", [["demand_percent", "Demand multiplier", "% of baseline demand"], ["service_target_percent", "Service threshold", "% · comparison only"], ["reservation_qty", "Reserved quantity", "pieces · due day 0"], ["safety_qty", "Safety quantity", "pieces · explicit policy"]]],
    ["Supply timing", [["lead_days", "Declared lead time", "full calendar days"], ["supplier_delay_days", "Supplier delay", "days · simulation only"], ["inbound_day", "Confirmed inbound", "arrival day · confirmed receipt"], ["review_days", "Review interval", "days · simulator policy"]]],
    ["Order constraints", [["pack_size", "Pack size", "whole pieces per pack"], ["moq", "Minimum order", "whole pieces"]]],
  ];
  function buildControls(data) {
    defaults = data.defaults; schema = data.controls;
    const root = clear("controls");
    groups.forEach(([title, fields]) => {
      const fieldset = el("fieldset"); fieldset.append(el("legend", title));
      const grid = el("div", null, "fields");
      fields.forEach(([key, label, unit]) => {
        const rule = schema[key];
        if (!rule) throw new Error(`Missing scenario control schema: ${key}`);
        const wrapper = el("label", null, "control-field");
        const input = el("input"); input.type = "number"; input.name = key; input.id = `control-${key}`;
        input.min = rule.min; input.max = rule.max; input.step = "1"; input.required = true; input.value = defaults[key] ?? rule.default;
        input.setAttribute("aria-describedby", `hint-${key}`);
        const name = el("span", label); name.id = `label-${key}`;
        input.setAttribute("aria-labelledby", name.id);
        wrapper.append(name, input);
        const hint = el("small", `${unit} · ${rule.min}–${rule.max}`); hint.id = `hint-${key}`; wrapper.append(hint); grid.append(wrapper);
      });
      fieldset.append(grid); root.append(fieldset);
    });
    const fieldset = el("fieldset"); fieldset.append(el("legend", "Evidence gate"));
    const label = el("label", null, "control-field wide"); label.append(el("span", "Supply evidence"));
    const select = el("select"); select.name = "evidence_case"; select.id = "control-evidence_case";
    (schema.evidence_case?.options || ["clean", "incomplete_supply"]).forEach((value) => { const option = el("option", value === "clean" ? "Complete / trusted" : "Incomplete / block decision"); option.value = value; select.append(option); });
    select.value = defaults.evidence_case || "clean"; label.append(select); fieldset.append(label); root.append(fieldset);
  }
  function payload() {
    const output = {};
    Object.keys(schema).forEach((key) => {
      const input = form.elements.namedItem(key);
      if (input) output[key] = key === "evidence_case" ? input.value : Number(input.value);
    });
    return output;
  }
  function setInputs(values) {
    Object.entries(values).forEach(([key, value]) => { const input = form.elements.namedItem(key); if (input) input.value = value; });
    markStale();
  }
  function sameInputs(left, right) { return Object.keys(schema).every((key) => left[key] === right[key]); }
  function markStale() {
    form.querySelectorAll("input").forEach((input) => { if (input.validity.valid) input.removeAttribute("aria-invalid"); });
    if (!result || !schema) return;
    const stale = !sameInputs(payload(), result.scenario.parameters);
    const status = $("scenario-status"); status.classList.toggle("stale", stale);
    status.textContent = stale ? "Inputs changed. Run to update the displayed results." : "Displayed results match these assumptions.";
    $("live-status").textContent = stale ? "Inputs changed. Displayed results remain from the previous run." : "Displayed results match the scenario inputs.";
    $("form-errors").hidden = true;
  }
  function setBusy(value) {
    if (value) returnFocus = form.contains(document.activeElement) ? document.activeElement : null;
    busy = value;
    form.querySelectorAll("input, select, button").forEach((node) => { node.disabled = value || !schema; });
    document.querySelectorAll("[data-preset]").forEach((node) => { node.disabled = value || !schema; });
    $("run-button").textContent = value ? "Evaluating…" : "Run scenario ↗";
    $("assessment").setAttribute("aria-busy", String(value));
    if (!value) {
      if (returnFocus && document.activeElement === document.body) returnFocus.focus();
      returnFocus = null;
    }
  }

  function renderTrust(data) {
    const meta = data.metadata;
    const root = clear("trust-strip"); root.append(el("span", null, "status-dot"), el("strong", `${meta.key.sku_id} / ${meta.key.warehouse_id}`));
    root.append(el("span", null, "divider"), el("span", "Synthetic finished garment · whole pieces"), el("span", null, "divider"));
    const cutoff = el("time", `Trusted at ${meta.cutoff}`); cutoff.dateTime = meta.cutoff; root.append(cutoff);
    root.append(el("span", "Recorded replay, not live inventory"));
  }
  function renderAssessment(data) {
    const blocked = data.scenario.status !== "assessable";
    const root = clear("assessment"); root.classList.toggle("blocked", blocked);
    root.append(el("span", blocked ? "NOT ASSESSABLE" : "ASSESSABLE", "status-label"));
    const text = el("div"); text.append(el("b", blocked ? "The evidence gate blocks this scenario." : "The scenario is backed by structured evidence."));
    const reasonLabels = { incomplete_or_mismatched_supply: "Supply evidence is incomplete or inconsistent.", ineligible_or_unavailable_forecast: "A forecast cannot be assessed from the available evidence." };
    text.append(el("p", blocked ? `${data.scenario.reasons.map((reason) => reasonLabels[reason] || "Inspect the decision trace for the blocking evidence.").join(" ")} The clean baseline remains available below.` : "Compare a deterministic proposal and simulated outcomes with the default clean replay."));
    root.append(text);
    const warnings = clear("warnings"); warnings.hidden = !data.warnings?.length;
    if (data.warnings?.length) { const box = el("div", null, "warnings"); const list = el("ul"); data.warnings.forEach((warning) => list.append(el("li", typeof warning === "string" ? warning : JSON.stringify(warning)))); box.append(list); warnings.append(box); }
  }
  function renderMetrics(data) {
    const root = clear("metrics");
    const entries = [
      ["proposed_order_qty", "Recommended replenishment", false, "pieces · prefix proposal"],
      ["immediate_fill_rate", "Immediate fill rate", true, "new demand · scored days"],
      ["cycle_service", "Shortage-free cycles", true, "complete review cycles"],
      ["total_cost", "Total synthetic cost", false, "scored + runoff cost units"],
      ["shortage_days", "Simulated shortage days", false, "days with ending backlog"],
      ["average_on_hand", "Average physical stock", false, "pieces · scored days"],
      ["backlog_piece_days", "Backlog exposure", false, "piece-days · scored days"],
    ];
    entries.forEach(([key, label, rate, detail]) => {
      const value = data.comparison[key];
      const card = el("article", null, "metric-card"); card.append(el("p", label, "metric-label"));
      const metric = el("p", value?.scenario === null || value?.scenario === undefined ? (data.scenario.status === "assessable" ? "Undefined" : "Not assessable") : rate ? percentage(value.scenario) : exact(value.scenario), "metric-value");
      if (value?.scenario === null || value?.scenario === undefined) metric.classList.add("unavailable");
      metric.title = `Exact scenario value: ${exact(value?.scenario)}`; card.append(metric);
      const comparison = el("p", null, "metric-comparison"); comparison.append(el("span", "Baseline "), el("b", rate ? percentage(value?.baseline) : exact(value?.baseline)), el("br"), el("span", detail)); card.append(comparison);
      const delta = el("span", deltaText(value?.delta, rate), "metric-delta"); delta.title = `Exact delta: ${exact(value?.delta)}`; card.append(delta); root.append(card);
    });
    const forecast = data.scenario.forecast;
    const card = el("article", null, "metric-card"); card.append(el("p", "Forecast demand", "metric-label"));
    card.append(el("p", forecast ? exact(forecast.total) : "Not assessable", "metric-value" + (!forecast ? " unavailable" : "")));
    card.append(el("p", `Baseline ${exact(data.baseline.forecast?.total)} · ${data.baseline.forecast?.horizon ?? "—"}-day window`, "metric-comparison"), el("span", forecast ? `${forecast.method} · ${forecast.horizon} days` : "Evidence blocked", "metric-delta")); root.append(card);
  }
  function keyValues(root, pairs) {
    const list = el("dl", null, "key-values"); pairs.forEach(([label, value]) => { const row = el("div"); row.append(el("dt", label), el("dd", exact(value))); list.append(row); }); root.append(list);
  }
  function renderInventory(data) {
    const root = clear("inventory");
    const confirmed = (side) => {
      const supply = data[side].trace.find((node) => node.stage === "supply")?.data.inbound;
      return supply ? supply.filter((row) => row.status === "confirmed").map((row) => `${exact(row.remaining_qty)} pieces`).join(", ") || "No confirmed inbound records" : "Not assessable";
    };
    keyValues(root, [["Trusted on-hand", data.metadata.on_hand], ["Confirmed inbound · baseline", data.metadata.confirmed_inbound_qty === undefined ? confirmed("baseline") : `${exact(data.metadata.confirmed_inbound_qty)} pieces`], ["Confirmed inbound · scenario", confirmed("scenario")], ["Inbound arrival · baseline", `Day ${data.baseline.parameters.inbound_day}`], ["Inbound assumption · scenario", `Day ${data.scenario.parameters.inbound_day}`], ["Reserved · baseline → scenario", `${data.baseline.parameters.reservation_qty} → ${data.scenario.parameters.reservation_qty} pieces`], ["Pending inbound", "Excluded from planning"]]);
    root.append(el("p", "Reservations are prior demand due on day 0, disjoint from the declared new demand trace.", "table-note"));
  }
  function renderRisk(data) {
    const root = clear("risk");
    ["baseline", "scenario"].forEach((side) => {
      const risk = data[side].risk;
      const row = el("div", null, "risk-row"); row.append(el("strong", side === "baseline" ? "Clean baseline" : "Current scenario"));
      if (!risk) { row.append(el("p", "Not assessable. The evidence gate suppresses risk outputs.")); root.append(row); return; }
      const badge = el("span", risk.stockout_days.length ? "Prefix projection shortage" : "No prefix projection shortage", "risk-badge" + (!risk.stockout_days.length ? " good" : ""));
      row.append(badge); row.append(el("p", `Before arrival: ${risk.pre_arrival_shortage_days.length ? risk.pre_arrival_shortage_days.join(", ") : "No shortages"}.`));
      if (risk.stockout_days.length) row.append(el("p", `Stockout dates: ${risk.stockout_days.join(", ")}.`));
      row.append(el("p", `Periodic simulation: ${exact(data[side].simulation?.metrics.shortage_days)} scored days with ending backlog.`));
      row.append(el("p", `Peak surplus above safety: ${exact(risk.peak_excess_qty)} pieces · excess exposure: ${exact(risk.excess_piece_days)} piece-days.`));
      row.append(el("p", risk.meets_service_target === null
        ? `Immediate fill has an undefined denominator; the ${percentage(risk.service_target)} service threshold remains unassessed.`
        : `Immediate fill ${risk.meets_service_target ? "meets" : "falls below"} the ${percentage(risk.service_target)} service threshold.`)); root.append(row);
    });
    root.append(el("p", data.scenario.risk?.definition || data.baseline.risk?.definition || "", "table-note"));
  }
  function renderCosts(data) {
    const root = clear("costs"); const rows = [];
    const phases = [["scored", "Scored window"], ["runoff", "Runoff"]];
    phases.forEach(([phase, label]) => {
      ["holding", "backlog", "setup", "total"].forEach((component) => {
        const comp = data.comparison.costs?.[phase]?.[component];
        rows.push([`${label} · ${component}`, exact(data.baseline.costs?.[phase]?.[component]), exact(data.scenario.costs?.[phase]?.[component]), deltaText(comp?.delta)]);
      });
    });
    rows.push(["Combined total", exact(data.baseline.costs?.total), exact(data.scenario.costs?.total), deltaText(data.comparison.total_cost?.delta)]);
    const node = table(root, "All cost quantities are supplied by the deterministic simulator.", ["Window / component", "Baseline", "Scenario", "Scenario − baseline"], rows, true);
    node.querySelector("tbody tr:last-child").classList.add("total-row");
    const rates = data.baseline.costs?.rates;
    root.append(el("p", rates ? `Synthetic rates: holding ${exact(rates.holding)} / piece-day · backlog ${exact(rates.backlog)} / piece-day · setup ${exact(rates.setup)} / placed order. No currency or commercial cost claim.` : "Synthetic cost rates unavailable.", "table-note"));
    const window = (side) => {
      const assumptions = data[side].simulation?.assumptions;
      return assumptions ? `${assumptions.scored_days} scored + ${assumptions.runoff_days} runoff days` : "Not assessable";
    };
    root.append(el("p", `Accounting windows: baseline ${window("baseline")}; scenario ${window("scenario")}. Runoff length changes with lead time, delay and review interval; combined totals can cover different durations.`, "table-note"));
  }
  function renderForecast(data) {
    const baseline = data.baseline.forecast, scenario = data.scenario.forecast;
    const forecast = scenario || baseline;
    if (!forecast) { empty("forecast-chart"); empty("forecast-table"); clear("forecast-source"); return; }
    $("forecast-caption").textContent = `${forecast.method} model · ${forecast.horizon}-day forecast · counterfactual demand is supplied as whole-piece structured evidence`;
    const labels = forecast.predictions.map((_, index) => `Day ${index}`);
    chart("forecast-chart", "Baseline and scenario daily forecast", labels, [
      { label: "Baseline forecast", values: baseline?.predictions || [], color: colors.baseline, dotted: true },
      { label: "Scenario forecast", values: scenario?.predictions || [], color: colors.scenario },
      { label: "Scenario declared demand", values: scenario?.demand || [], color: colors.demand, dashed: true },
    ]);
    const root = clear("forecast-table");
    table(root, "Exact values; demand is a declared synthetic future trace, not an observed prediction score.", ["Day", "Baseline forecast", "Scenario forecast", "Baseline demand", "Scenario demand"], labels.map((label, index) => [label, exact(baseline?.predictions[index]), exact(scenario?.predictions[index]), exact(baseline?.demand[index]), exact(scenario?.demand[index])]), true);
    const source = clear("forecast-source"); source.append(el("p", `Saved forecast run: ${baseline?.source_run_id || "Unavailable"}`, "table-note"));
    const disclosure = el("details", null, "data-disclosure"); disclosure.append(el("summary", "Training evidence / exact service denominators"), codeBlock({ baseline_training: baseline?.training ?? null, scenario_training: scenario?.training ?? null, baseline_service: data.baseline.simulation?.metrics ?? null, scenario_service: data.scenario.simulation?.metrics ?? null })); source.append(disclosure);
    if (!scenario) source.prepend(el("p", "Scenario forecast is not assessable; only the baseline is drawn.", "table-note"));
  }
  function renderPlan(data) {
    const baseline = data.baseline.plan, scenario = data.scenario.plan;
    const baselineRows = baseline?.projection || [], scenarioRows = scenario?.projection || [];
    const rows = baselineRows.length > scenarioRows.length ? baselineRows : scenarioRows;
    const labels = rows.map((row) => row.day);
    $("plan-caption").textContent = `Prefix-stock-v1 · baseline ${baselineRows.length} days / scenario ${scenarioRows.length || "not assessable"} · scenario proposal arrival ${scenario?.order_arrival_day || "not assessable"}`;
    chart("plan-chart", "Prefix planning balance with and without the proposed order", labels, [
      { label: "Baseline with proposal", values: baselineRows.map((row) => row.balance_with_order), color: colors.baseline, dotted: true },
      { label: "Scenario with proposal", values: scenarioRows.map((row) => row.balance_with_order), color: colors.scenario },
      { label: "Scenario without proposal", values: scenarioRows.map((row) => row.balance_without_order), color: colors.backlog, dashed: true },
    ]);
    const root = clear("plan-table");
    ["baseline", "scenario"].forEach((side) => {
      const plan = data[side].plan;
      if (!plan) { root.append(el("p", "Scenario projection and recommendation are not assessable.", "empty-state")); return; }
      table(root, `${side === "baseline" ? "Baseline" : "Scenario"} · exact prefix projection`, ["Day", "Forecast", "Inbound", "Reservation", "Without order", "With order"], plan.projection.map((row) => [row.day, row.forecast, row.inbound, row.reservations, row.balance_without_order, row.balance_with_order]), true);
      root.append(el("p", `Raw requirement ${exact(plan.unrounded_need)} → whole-piece ceiling ${exact(plan.whole_piece_need)} → proposed ${exact(plan.proposed_order_qty)} pieces; rounding extra ${exact(plan.rounding_extra)}. Arrival ${plan.order_arrival_day}.`, "table-note"));
    });
  }
  function simulationRows(data, side, scored) { return (data[side].simulation?.days || []).filter((row) => row.scored === scored); }
  function renderSimulationChart(data, id, scored) {
    const baseline = simulationRows(data, "baseline", scored), scenario = simulationRows(data, "scenario", scored);
    // Union day indices for differing runoff lengths; each series is aligned by
    // its recorded day, rather than assuming equal scenario calendar windows.
    const days = [...new Set([...baseline, ...scenario].map((row) => row.day))].sort((a, b) => a - b);
    const values = (rows, field) => { const byDay = new Map(rows.map((row) => [row.day, row[field]])); return days.map((day) => byDay.get(day) ?? null); };
    chart(id, scored ? "Scored physical stock and backlog" : "Runoff physical stock and backlog", days.map((day) => `Day ${day}`), [
      { label: "Baseline stock", values: values(baseline, "on_hand"), color: colors.baseline, longDashed: true },
      { label: "Scenario stock", values: values(scenario, "on_hand"), color: colors.scenario },
      { label: "Baseline backlog", values: values(baseline, "backlog"), color: colors.baselineBacklog, dotted: true },
      { label: "Scenario backlog", values: values(scenario, "backlog"), color: colors.backlog, dashed: true },
    ]);
  }
  function renderSimulationTable(data, id, scored) {
    const root = clear(id);
    ["baseline", "scenario"].forEach((side) => {
      if (!data[side].simulation) { root.append(el("p", "Scenario simulated outcomes are not assessable.", "empty-state")); return; }
      table(root, `${side === "baseline" ? "Baseline" : "Scenario"} · ${scored ? "scored demand window" : "runoff only"}`, ["Day", "Demand", "Prior due", "Receipts", "Order", "On-hand", "Backlog", "Filled", "Cost"], simulationRows(data, side, scored).map((row) => [row.day, row.new_demand, row.prior_demand, row.receipts, row.order_qty, row.on_hand, row.backlog, row.fulfilled_units, row.total_cost]), true);
    });
  }
  function renderSimulation(data) {
    const scenario = data.scenario.simulation, baseline = data.baseline.simulation;
    $("simulation-caption").textContent = `Periodic inventory-position policy · ${baseline?.assumptions?.scored_days ?? "not assessable"} scored days · delay is hidden from simulated ordering`;
    renderSimulationChart(data, "simulation-chart", true); renderSimulationTable(data, "simulation-table", true);
    renderSimulationChart(data, "runoff-chart", false); renderSimulationTable(data, "runoff-table", false);
    clear("terminal").append(codeBlock({ baseline_terminal: baseline?.terminal ?? null, scenario_terminal: scenario?.terminal ?? null }));
    clear("reviews").append(codeBlock({ baseline: baseline ? { assumptions: baseline.assumptions, reviews: baseline.reviews } : null, scenario: scenario ? { assumptions: scenario.assumptions, reviews: scenario.reviews } : null }));
  }
  function renderTrace() {
    if (!result) return;
    const side = $("trace-side").value, evidence = result[side];
    const root = clear("trace");
    evidence.trace.forEach((node, index) => {
      const disclosure = el("details", null, "trace-node"); const summary = el("summary");
      summary.append(el("span", String(index + 1).padStart(2, "0"), "trace-step"));
      const label = el("span", node.label, "trace-label"); label.append(el("small", node.stage));
      const arrow = el("span", "+", "trace-arrow"); arrow.setAttribute("aria-hidden", "true");
      summary.append(label, arrow); disclosure.append(summary);
      const body = el("div", null, "trace-body"); body.append(el("p", node.explanation));
      const references = el("div", null, "references"); (node.references || []).forEach((reference) => references.append(el("span", `${reference.source}: ${reference.id}`, "reference"))); body.append(references, codeBlock(node.data));
      disclosure.append(body); root.append(disclosure);
    });
    if (!evidence.trace.length) root.append(el("p", "No trace evidence was supplied.", "empty-state"));
  }
  function render(data) {
    result = data;
    renderTrust(data); renderAssessment(data); renderMetrics(data); renderInventory(data); renderRisk(data); renderCosts(data);
    renderForecast(data); renderPlan(data); renderSimulation(data); renderTrace();
    clear("provenance").append(codeBlock({ contract_version: data.contract_version, metadata: data.metadata, baseline_run_id: data.baseline.run_id, scenario_run_id: data.scenario.run_id, baseline_parameters: data.baseline.parameters, scenario_parameters: data.scenario.parameters }));
    $("export-button").disabled = false;
    markStale();
  }
  async function request(url, options = {}) {
    controller?.abort(); controller = new AbortController();
    const current = ++requestId;
    const timeout = setTimeout(() => controller?.abort(), 30000);
    try {
      const response = await fetch(url, { ...options, signal: controller.signal, headers: { "Accept": "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}) } });
      const data = await response.json();
      if (!response.ok) {
        const details = Array.isArray(data.detail) ? data.detail.map((item) => `${item.loc?.slice(1).join(".") || "Scenario"}: ${item.msg}`).join("; ") : typeof data.detail === "string" ? data.detail : `Request failed (${response.status})`;
        throw new Error(details);
      }
      if (current !== requestId) return null;
      return data;
    } finally { clearTimeout(timeout); }
  }
  function errorMessage(error) { return error.name === "AbortError" ? "Evaluation did not finish within 30 seconds. Retry the request." : error.message || "Unable to load the local evidence service."; }
  async function initialize() {
    if (busy) return;
    setBusy(true); $("global-error").hidden = true;
    try {
      const data = await request("/api/lab");
      if (!data) return;
      buildControls(data); render(data); $("live-status").textContent = "Default clean baseline and scenario are ready.";
    } catch (error) {
      if (!result) {
        clear("trust-strip").append(el("strong", "Synthetic evidence unavailable"));
        clear("assessment").append(el("p", "Not assessable. No replay results are available."));
        clear("controls").append(el("p", "Scenario controls require validated replay evidence."));
      }
      const root = clear("global-error"); root.hidden = false; root.append(el("p", `${errorMessage(error)} Start the local Lab server and retry.`));
      const retry = el("button", "Retry loading evidence", "button secondary"); retry.type = "button"; retry.addEventListener("click", initialize); root.append(retry);
      $("live-status").textContent = "Evidence could not be loaded.";
    } finally { setBusy(false); }
  }
  form.addEventListener("input", markStale); form.addEventListener("change", markStale);
  form.addEventListener("invalid", (event) => { event.target.setAttribute("aria-invalid", "true"); }, true);
  form.addEventListener("submit", async (event) => {
    event.preventDefault(); if (busy || !schema || !form.reportValidity()) return;
    const submitted = payload(); setBusy(true); $("form-errors").hidden = true; $("live-status").textContent = "Evaluating scenario.";
    try {
      const data = await request("/api/scenarios", { method: "POST", body: JSON.stringify(submitted) });
      if (!data) return;
      render(data); $("live-status").textContent = data.scenario.status === "assessable" ? "Scenario complete. Comparison and evidence trace updated." : "Scenario evidence is incomplete. Outputs are not assessable. Clean baseline remains available.";
    } catch (error) {
      const root = clear("form-errors"); root.hidden = false; root.append(el("p", errorMessage(error)), el("p", "The displayed results remain from the previous successful run.")); root.focus(); $("live-status").textContent = "Scenario failed. Previous results are retained.";
    } finally { setBusy(false); }
  });
  $("reset-button").addEventListener("click", () => { if (defaults) setInputs(defaults); });
  document.querySelectorAll("[data-preset]").forEach((button) => button.addEventListener("click", () => {
    if (busy || !defaults) return;
    const values = { ...defaults };
    if (button.dataset.preset === "demand") values.demand_percent = 125;
    if (button.dataset.preset === "delay") values.supplier_delay_days = 3;
    if (button.dataset.preset === "blocked") values.evidence_case = "incomplete_supply";
    setInputs(values); $("run-button").focus();
  }));
  $("trace-side").addEventListener("change", renderTrace);
  $("export-button").addEventListener("click", () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2) + "\n"], { type: "application/json" });
    const url = URL.createObjectURL(blob); const link = el("a"); link.href = url; link.download = "inventory-decision-lab-comparison.json";
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    $("live-status").textContent = "The displayed comparison and exact evidence were downloaded as JSON.";
  });
  initialize();
})();
