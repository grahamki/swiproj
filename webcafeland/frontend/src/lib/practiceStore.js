const TRAY_KEY = "mh.clickedWords";
const SELECTED_KEY = "mh.practice.selected";

export const practiceStore = {
  getTrayWords() {
    try {
      const raw = localStorage.getItem(TRAY_KEY);
      const arr = JSON.parse(raw || "[]");
      const seen = new Set();
      const clean = [];
      for (const w of arr) {
        if (typeof w !== "string") continue;
        const trimmed = w.trim();
        const lc = trimmed.toLowerCase();
        if (!trimmed || seen.has(lc)) continue;
        seen.add(lc);
        clean.push(trimmed);
      }
      return clean;
    } catch {
      return [];
    }
  },

  setSelectedWords(words) {
    try {
      localStorage.setItem(SELECTED_KEY, JSON.stringify(words || []));
    } catch {}
  },

  getSelectedWords() {
    try {
      return JSON.parse(localStorage.getItem(SELECTED_KEY) || "[]");
    } catch {
      return [];
    }
  },

  clearSelected() {
    try {
      localStorage.removeItem(SELECTED_KEY);
    } catch {}
  }
};
