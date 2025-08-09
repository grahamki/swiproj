export const GAME_STATES = {
  READY: "READY",
  IN_TRIAL: "IN_TRIAL",
  FEEDBACK: "FEEDBACK",
  DONE: "DONE",
};

export function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = (Math.random() * (i + 1)) | 0;
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function buildDecoys(correct) {
  const PREFIX_DECOYS = ["re", "pre", "mis", "non"];
  const SUFFIX_DECOYS = ["ness", "ment", "less", "ful", "ize", "ity"];
  const used = new Set(correct.map(m => m.morpheme.toLowerCase()));
  const mk = (m, type) => ({ morpheme: m, type, meaning: "" });
  const pick = (arr, n, type) => arr.filter(x => !used.has(x)).slice(0, n).map(x => mk(x, type));
  return [...pick(PREFIX_DECOYS, 1, "prefix"), ...pick(SUFFIX_DECOYS, 2, "suffix")];
}

export function makeTrial(entry) {
  const correct = entry.morphemes.map((m, i) => ({ ...m, id: `gold-${i}-${m.morpheme}` }));
  const decoys = buildDecoys(correct).map((m, i) => ({ ...m, id: `decoy-${i}-${m.morpheme}` }));
  const tiles = shuffle([...correct, ...decoys]);
  return {
    word: entry.word,
    correct,
    tiles,
    placed: { prefix: null, root: null, suffix: null },
    hintUsed: false,
    startTs: Date.now(),
  };
}

export function scoreTrial(trial) {
  const { correct, placed, startTs } = trial;
  const gold = {
    prefix: correct.find(m => m.type === "prefix")?.morpheme?.toLowerCase() || null,
    root:   correct.find(m => m.type === "root")?.morpheme?.toLowerCase()   || null,
    suffix: correct.find(m => m.type === "suffix")?.morpheme?.toLowerCase() || null,
  };

  const ans = {
    prefix: placed.prefix?.morpheme?.toLowerCase() || null,
    root:   placed.root?.morpheme?.toLowerCase()   || null,
    suffix: placed.suffix?.morpheme?.toLowerCase() || null,
  };

  // Only evaluate slots that exist in gold; ignore others
  const perSlot = {
    prefix: gold.prefix ? (ans.prefix === gold.prefix) : true,
    root:   gold.root   ? (ans.root   === gold.root)   : true,
    suffix: gold.suffix ? (ans.suffix === gold.suffix) : true,
  };

  const required = ['prefix','root','suffix'].filter(k => gold[k]);
  const correctCount = required.filter(k => perSlot[k]).length;

  return {
    correct: correctCount === required.length,
    perSlot,
    latencyMs: Date.now() - startTs
  };
}
