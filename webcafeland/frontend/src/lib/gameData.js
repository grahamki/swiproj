// Each word has a canonical SWI split for “truth” in the game.
export const SEED_WORDS = [
  {
    word: "unbelievable",
    morphemes: [
      { morpheme: "un", type: "prefix", meaning: "not" },
      { morpheme: "believe", type: "root", meaning: "to consider true" },
      { morpheme: "able", type: "suffix", meaning: "capable of" }
    ],
    families: ["believe", "believer", "believable", "disbelief"]
  },
  {
    word: "construction",
    morphemes: [
      { morpheme: "con", type: "prefix", meaning: "together/with" },
      { morpheme: "struct", type: "root", meaning: "build" },
      { morpheme: "ion", type: "suffix", meaning: "act or result" }
    ],
    families: ["construct", "instruct", "structure", "reconstruction"]
  },
  {
    word: "dysfunctional",
    morphemes: [
      { morpheme: "dys", type: "prefix", meaning: "bad/abnormal" },
      { morpheme: "function", type: "root", meaning: "purpose/work" },
      { morpheme: "al", type: "suffix", meaning: "relating to" }
    ],
    families: ["function", "functional", "malfunction"]
  }
];
