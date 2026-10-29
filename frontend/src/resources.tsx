import React, { useEffect, useState } from "react";
import type { Exact } from "./types";
import { readJSON } from "./request.mjs";

export function exact(value: Exact | undefined): string {
  if (value === null || value === undefined) return "Unknown";
  if (typeof value === "string") return value;
  if (
    typeof value.numerator !== "string" ||
    typeof value.denominator !== "string"
  )
    return "Unknown";
  if (value.denominator === "1") return value.numerator;
  return `${value.numerator}/${value.denominator}`;
}
export function Download({
  data,
  name,
  label = "Export evidence",
  disabled = false,
}: {
  data: unknown;
  name: string;
  label?: string;
  disabled?: boolean;
}) {
  return (
    <button
      disabled={disabled}
      onClick={() => {
        const url = URL.createObjectURL(
          new Blob([JSON.stringify(data, null, 2)], {
            type: "application/json",
          }),
        );
        const a = document.createElement("a");
        a.href = url;
        a.download = `${name}.json`;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }}
    >
      {label}
    </button>
  );
}
export function useResource<T>(path: string | null, retry: number = 0) {
  const [state, set] = useState<{
    data?: T;
    error?: string;
    loading: boolean;
    path?: string;
  }>({ loading: true });
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    let active = true;
    set((s) => ({ ...s, error: undefined, loading: true }));
    readJSON(path, controller.signal)
      .then((data) => {
        if (active) set({ data, loading: false, path });
      })
      .catch((error) => {
        if (active && !controller.signal.aborted)
          set((s) => ({ ...s, error: error.message, loading: false }));
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [path, retry]);
  return { ...state, stale: Boolean(state.data && state.path !== path) };
}
export function Notice({
  loading,
  error,
  stale,
  retry,
  data,
}: {
  loading: boolean;
  error?: string;
  stale: boolean;
  retry: () => void;
  data?: unknown;
}) {
  return (
    <>
      {loading && (
        <p className="notice" role="status">
          Loading saved evidence…
        </p>
      )}
      {(error || stale) && (
        <div className="notice warning" role="alert">
          <strong>
            {error
              ? data
                ? "Unable to refresh. Last successful result is retained."
                : "Unable to load saved evidence. No result is available."
              : "This result belongs to the previous selection."}
          </strong>
          {error && <p>{error}</p>}
          <p>
            Review context before using it. Recommendations remain unavailable
            until this selection loads.
          </p>
          {error && <button onClick={retry}>Retry</button>}
        </div>
      )}
    </>
  );
}
