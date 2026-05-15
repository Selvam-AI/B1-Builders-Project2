let frontendDebugEnabled =
  import.meta.env.VITE_DEBUG === "true" || localStorage.getItem("fithub_debug") === "true";

export function setFrontendDebugEnabled(value: boolean) {
  frontendDebugEnabled = value;
}

export function debugLog(label: string, data?: unknown) {
  if (!frontendDebugEnabled) {
    return;
  }
  if (data === undefined) {
    console.log(`[FitHub AI] ${label}`);
    return;
  }
  console.log(`[FitHub AI] ${label}`, data);
}
