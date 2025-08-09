const KEY = "swi.game.state.v1";

export function saveSession(data) {
  try { localStorage.setItem(KEY, JSON.stringify(data)); } catch {}
}
export function loadSession() {
  try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch { return null; }
}
export function clearSession() {
  try { localStorage.removeItem(KEY); } catch {}
}
