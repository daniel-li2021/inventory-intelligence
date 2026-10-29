const statusHelp = {
  404: "This selection is unavailable. Choose another item or cutoff.",
  409: "The saved archive has changed. Reopen the workspace with the current archive.",
  422: "This selection is invalid or unavailable. Choose another item or cutoff.",
  429: "The demo is busy. Wait a moment, then retry.",
  503: "Saved evidence is temporarily unavailable. Retry shortly.",
};

// Bound read requests; retries are always explicit and never replay a write.
export async function readJSON(path, signal, timeoutMs = 20000) {
  const controller = new AbortController();
  const cancel = () => controller.abort();
  signal?.addEventListener("abort", cancel, { once: true });
  if (signal?.aborted) controller.abort();
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  try {
    const response = await fetch(path, { signal: controller.signal, cache: "no-store" });
    if (!response.ok)
      throw Error(`${statusHelp[response.status] || "Unable to load saved evidence. Retry shortly."} (HTTP ${response.status})`);
    return await response.json();
  } catch (error) {
    if (timedOut) throw Error("The request took too long. Your selection is unchanged; retry when ready.");
    if (signal?.aborted) throw error;
    if (error instanceof TypeError) throw Error("Connection interrupted. Check your connection, then retry.");
    throw error;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", cancel);
  }
}
