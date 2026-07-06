// Anonymous session identity (ADR-012): UUID persisted in localStorage,
// sent as X-Session-Id on every API call.

const STORAGE_KEY = "ch_session_id";

export function getSessionId(): string {
  if (typeof window === "undefined") return "";
  let id = window.localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = crypto.randomUUID();
    window.localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}
