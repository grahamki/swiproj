from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import os
import re
import json
from dotenv import load_dotenv

# Try optional Anthropic import (fallback to heuristic if not available or no key)
try:
    import anthropic
    from anthropic.types.text_block import TextBlock
except Exception:
    anthropic = None
    TextBlock = None

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Be explicit: allow all origins to hit any /api/*, expose debug headers
CORS(app, resources={r"/api/*": {"origins": "*"}}, expose_headers=["X-Analysis-Source", "X-Morpheme-Count", "X-Meaning"])

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"ok": True})

# Preflight handler so browsers don’t block cross-origin calls to :5001
@app.route('/api/<path:subpath>', methods=['OPTIONS'])
def api_options(subpath):
    resp = make_response('', 204)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp

def _extract_word(req):
    """Try JSON, then form (x-www-form-urlencoded), then querystring, then raw JSON."""
    try:
        data = req.get_json(silent=True) or {}
    except Exception:
        data = {}
    w = (data.get('word') or '').strip() if isinstance(data, dict) else ''
    if not w:
        try:
            w = (req.form.get('word') or '').strip()
        except Exception:
            w = ''
    if not w:
        try:
            w = (req.args.get('word') or '').strip()
        except Exception:
            w = ''
    if not w:
        try:
            raw = (req.data or b'').decode('utf-8', 'ignore')
            if raw:
                j = json.loads(raw)
                if isinstance(j, dict):
                    w = (j.get('word') or '').strip()
        except Exception:
            pass
    return w

# Analyze morphemes
@app.route('/api/analyze-morpheme', methods=['POST'])
def analyze_morpheme():
    data = request.get_json(silent=True) or {}
    word = _extract_word(request)
    if not word:
        return jsonify({"error": "ERROR TRY AGAIN"}), 500

    atype = (data.get('type') or data.get('analysis_type') or 'morphemes').lower()

    # morphemes-only: Anthropic only; otherwise error
    if atype == 'morphemes':
        if ANTHROPIC_API_KEY and anthropic is not None:
            try:
                result = analyze_with_anthropic_morphemes(word)
                if result and isinstance(result, dict):
                    result["source"] = "anthropic"
                    return jsonify(result)
            except Exception as e:
                print("Anthropic error:", e)
        # no heuristic fallback
        resp = jsonify({"error": "ERROR TRY AGAIN"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp, 500

    # Other tabs derive from a single full analysis (Anthropic only)
    if ANTHROPIC_API_KEY and anthropic is not None:
        try:
            full = analyze_with_anthropic_full(word)
            if isinstance(full, dict):
                if atype == 'meaning':
                    piece = {"meaning": full.get("meaning", "")}
                elif atype == 'etymology':
                    piece = {
                        "historical_origin": full.get("historical_origin", ""),
                        "morphological_relatives": full.get("morphological_relatives", []),
                        "etymological_relatives": full.get("etymological_relatives", [])
                    }
                elif atype == 'graphemes':
                    piece = {"graphemes": full.get("graphemes", [])}
                elif atype == 'relatives':
                    piece = {
                        "morphological_relatives": full.get("morphological_relatives", []),
                        "etymological_relatives": full.get("etymological_relatives", [])
                    }
                else:
                    piece = {"word": full.get("word", word), "morphemes": full.get("morphemes", [])}
                piece["source"] = "anthropic"
                return jsonify(piece)
        except Exception as e:
            print("Anthropic full error:", e)

    # no heuristic fallback
    resp = jsonify({"error": "ERROR TRY AGAIN"})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp, 500

# --- Heuristic enrichment helpers ---
_DIGRAPHS = [
    "tion","sion","tch","dge","igh",
    "ch","sh","ph","th","gh","ck","ng","wh","qu",
    "ea","ee","oo","ou","ow","oi","oy","ai","ay","au","aw",
    "er","ar","or","ur","ir","ie","ei"
]

def _split_graphemes(word: str):
    w = (word or "").strip()
    out = []
    i = 0
    low = w.lower()
    while i < len(w):
        match = None
        for g in _DIGRAPHS:
            if low.startswith(g, i):
                match = w[i:i+len(g)]
                break
        if match:
            out.append({"grapheme": match, "ipa": ""})
            i += len(match)
        else:
            out.append({"grapheme": w[i], "ipa": ""})
            i += 1
    return out

def _past_participle(base: str):
    s = base or ""
    if not s:
        return ""
    if s.endswith("e"):
        return s + "d"
    if re.search(r"[^aeiou]y$", s):
        return s[:-1] + "ied"
    return s + "ed"

def _progressive(base: str):
    s = base or ""
    if not s:
        return ""
    if s.endswith("e") and not s.endswith("ee"):
        return s[:-1] + "ing"
    return s + "ing"

def _maybe_fix_root_for_suffix(root: str, suffix: str):
    # Fix common truncated -able/-ible roots ending in 'v' -> add 'e' (believ -> believe)
    if suffix in ("able", "ible") and re.search(r"[^e]v$", root or ""):
        return (root or "") + "e"
    return root

def _compose_meaning(prefix: str, root: str, suffix: str):
    # Very light templates; better than empty
    neg_prefixes = {"un","in","im","il","ir","non","dis"}
    neg = prefix.lower() in neg_prefixes if prefix else False
    r = root or ""
    s = suffix or ""

    if s in ("able","ible"):
        base = _past_participle(r)
        return f"{'Not ' if neg else ''}capable of being {base}."
    if s in ("ness",):
        return f"State or quality of being {r}."
    if s in ("ment",):
        return f"Result of {_progressive(r)}."
    if s in ("tion","sion","ion","ation"):
        return f"The act or process of {_progressive(r)}."
    if s in ("er","or"):
        return f"One who {r}s."
    if s in ("less",):
        return f"Without {r}."
    if s in ("ful",):
        return f"Full of {r}."

    # Generic fallback
    parts = []
    if prefix: parts.append(prefix)
    parts.append(r)
    if suffix: parts.append(suffix)
    return "Word formed from: " + " + ".join(parts) + "."

def _build_relatives(root: str, prefix: str = "", suffix: str = ""):
    r = (root or "").strip()
    if not r:
        return []
    forms = [
        r, r + "s", _past_participle(r), _progressive(r),
        r + "er", r + "ers"
    ]
    # Common derivations
    forms += [r + "able", r + "ible", "re" + r, "mis" + r, "dis" + r]
    # If panel word uses 'un' + r + 'able', include it
    if suffix in ("able","ible"):
        forms.append(r + suffix)
        if prefix:
            forms.append(prefix + r + suffix)
        else:
            forms.append("un" + r + suffix)
    # Dedup preserving order; filter trivials
    seen = set(); out = []
    for f in forms:
        k = f.strip().lower()
        if not k or k in seen: continue
        seen.add(k); out.append(f)
    return out[:20]

def _enrich_from_morphemes(word: str, obj: dict):
    """Fill missing fields (meaning, relatives, graphemes); lightly fix root for -able/-ible."""
    morphs = obj.get("morphemes") or []
    pref = next((m for m in morphs if m.get("type") == "prefix"), None)
    root = next((m for m in morphs if m.get("type") == "root"), None)
    suff = next((m for m in morphs if m.get("type") == "suffix"), None)

    # Try to fix truncated root for able/ible
    if root and suff:
        fixed = _maybe_fix_root_for_suffix(root.get("morpheme") or "", (suff.get("morpheme") or "").lower())
        if fixed and fixed != (root.get("morpheme") or ""):
            root["morpheme"] = fixed

    # Meaning
    if not obj.get("meaning"):
        obj["meaning"] = _compose_meaning(pref.get("morpheme") if pref else "", root.get("morpheme") if root else "", (suff.get("morpheme") if suff else ""))

    # Relatives
    if not obj.get("morphological_relatives"):
        obj["morphological_relatives"] = _build_relatives(root.get("morpheme") if root else "", pref.get("morpheme") if pref else "", (suff.get("morpheme") if suff else ""))
    if not obj.get("etymological_relatives"):
        # fallback: at least include the base root
        base = root.get("morpheme") if root else ""
        obj["etymological_relatives"] = [base] if base else []

    # Graphemes
    if not obj.get("graphemes"):
        obj["graphemes"] = _split_graphemes(word or "")

    return obj

def _normalize_full_result(word, obj):
    """Ensure minimal full-analysis shape; enrich morphemes if too short; coerce alt keys."""
    try:
        if not isinstance(obj, dict):
            obj = {}
    except Exception:
        obj = {}

    # Map common alternate keys to canonical keys
    if not obj.get("meaning"):
        for k in ("definition", "overall_meaning", "overallMeaning", "gloss"):
            if obj.get(k):
                obj["meaning"] = obj.get(k)
                break
    if "morphological_relatives" not in obj and obj.get("morphologicalRelatives"):
        obj["morphological_relatives"] = obj.get("morphologicalRelatives")
    if "etymological_relatives" not in obj and obj.get("etymologicalRelatives"):
        obj["etymological_relatives"] = obj.get("etymologicalRelatives")
    if not obj.get("historical_origin"):
        for k in ("etymology", "origin", "history", "historicalOrigin"):
            if obj.get(k):
                obj["historical_origin"] = obj.get(k)
                break
    # Accept alternative morpheme shape {prefix:{part},root:{part},suffix:{part}}
    if not obj.get("morphemes") and any(isinstance(obj.get(k), dict) for k in ("prefix","root","suffix")):
        mor = []
        if obj.get("prefix", {}).get("part"):
            mor.append({"morpheme": obj["prefix"]["part"], "type": "prefix", "meaning": obj["prefix"].get("meaning","")})
        if obj.get("root", {}).get("part"):
            mor.append({"morpheme": obj["root"]["part"], "type": "root", "meaning": obj["root"].get("meaning","")})
        if obj.get("suffix", {}).get("part"):
            mor.append({"morpheme": obj["suffix"]["part"], "type": "suffix", "meaning": obj["suffix"].get("meaning","")})
        obj["morphemes"] = mor

    obj.setdefault("word", word)
    obj.setdefault("morphemes", [])
    obj.setdefault("meaning", "")
    obj.setdefault("morphological_relatives", [])
    obj.setdefault("etymological_relatives", [])
    obj.setdefault("historical_origin", "")
    obj.setdefault("graphemes", [])

    # If morphemes missing or too short, use heuristic fallback
    mor = obj.get("morphemes")
    if not isinstance(mor, list) or len(mor) <= 1:
        fallback = get_mock_analysis(word, analysis_type='morphemes').get("morphemes", [])
        if isinstance(fallback, list) and len(fallback) > len(mor or []):
            obj["morphemes"] = fallback

    # De-dup relatives while preserving order
    def dedup(seq):
        seen = set(); out = []
        for x in seq or []:
            k = str(x).strip().lower()
            if k and k not in seen:
                seen.add(k); out.append(x)
        return out
    obj["morphological_relatives"] = dedup(obj.get("morphological_relatives"))
    obj["etymological_relatives"] = dedup(obj.get("etymological_relatives"))

    # Graphemes: coerce various shapes
    g = obj.get("graphemes", [])
    if isinstance(g, list):
        fixed = []
        for it in g:
            if isinstance(it, str):
                fixed.append({"grapheme": it, "ipa": ""})
            elif isinstance(it, dict):
                grapheme = it.get("grapheme") or it.get("graph") or it.get("letters") or ""
                ipa = it.get("ipa") or it.get("IPA") or it.get("phoneme") or it.get("symbol") or ""
                fixed.append({"grapheme": str(grapheme), "ipa": str(ipa)})
        obj["graphemes"] = fixed
    else:
        obj["graphemes"] = []

    # Enrich missing sections so the panel always has content
    obj = _enrich_from_morphemes(word, obj)
    return obj

def _debug_log_result(tag: str, word: str, result: dict):
    try:
        print(f"[analyze-word:{tag}] word='{word}' "
              f"src={result.get('source')} "
              f"morphs={len(result.get('morphemes') or [])} "
              f"meaning={'yes' if (result.get('meaning') or '').strip() else 'no'} "
              f"rel_morph={len(result.get('morphological_relatives') or [])} "
              f"rel_ety={len(result.get('etymological_relatives') or [])} "
              f"graphemes={len(result.get('graphemes') or [])}")
    except Exception as e:
        print("[analyze-word:log-error]", e)

@app.route('/api/analyze-word', methods=['POST', 'GET'])
def analyze_word_full():
    """Full analysis for a word (Anthropic only)."""
    # Accept JSON, form-encoded, or query param
    data = request.get_json(silent=True) or {}
    word = _extract_word(request)
    if not word:
        resp = jsonify({"error": "ERROR TRY AGAIN"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp, 500

    if ANTHROPIC_API_KEY and anthropic is not None:
        try:
            result = analyze_with_anthropic_full(word)
            if isinstance(result, dict):
                result["source"] = "anthropic"
                resp = jsonify(result)
                resp.headers['X-Analysis-Source'] = 'anthropic'
                resp.headers['X-Morpheme-Count'] = str(len(result.get('morphemes') or []))
                resp.headers['X-Meaning'] = '1' if (result.get('meaning') or '').strip() else '0'
                resp.headers['Access-Control-Allow-Origin'] = '*'
                resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
                resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
                return resp
        except Exception as e:
            print("Anthropic full error:", e)

    # no heuristic fallback
    resp = jsonify({"error": "ERROR TRY AGAIN"})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp, 500

def analyze_with_anthropic_morphemes(word):
    """Ask Anthropic for a JSON morpheme breakdown; no heuristic fallback."""
    prompt = f"""
    Break the word "{word}" into morphemes and return JSON only.
    Schema:
    {{
      "word": "<word>",
      "morphemes": [{{ "morpheme": "<str>", "type": "prefix|root|suffix", "meaning": "<short>" }}]
    }}
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=400,
        temperature=0,
        system="Return only valid minified JSON. No prose.",
        messages=[{"role": "user", "content": prompt}],
    )

    content = None
    if TextBlock:
        content = next((b.text for b in response.content if isinstance(b, TextBlock)), None)
    if content is None:
        content = getattr(response, "content", "") or ""

    content = content.strip()
    if content.startswith("```"):
        first_nl = content.find("\n")
        content = content[first_nl + 1 :] if first_nl != -1 else content
    if content.endswith("```"):
        content = content[:-3]

    # Parse strictly; raise on any issue
    result = json.loads(content)
    if not isinstance(result, dict):
        raise ValueError("Anthropic morphemes: not an object")
    result.setdefault("word", word)
    result.setdefault("morphemes", [])
    return result

def analyze_with_anthropic_full(word):
    """Anthropic comprehensive JSON; no heuristic fallback or normalization."""
    prompt = f"""
Break the word "{word}" into morphemes and graphemes, and return the result as a JSON object.
You are a linguist AI that breaks down English words into morphemes, graphemes, and explains their meaning, sound, and origin.

Return JSON with keys:
- word
- morphemes: [{{morpheme, type, meaning}}]
- meaning
- morphological_relatives
- etymological_relatives
- historical_origin
- graphemes: [{{grapheme, ipa}}]
"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=700,
        temperature=0,
        system="Return only valid minified JSON. No prose.",
        messages=[{"role": "user", "content": prompt}],
    )

    content = None
    if TextBlock:
        content = next((b.text for b in response.content if isinstance(b, TextBlock)), None)
    if content is None:
        content = getattr(response, "content", "") or ""
    content = content.strip()

    if content.startswith("```"):
        first_nl = content.find("\n")
        content = content[first_nl + 1 :] if first_nl != -1 else content
    if content.endswith("```"):
        content = content[:-3]

    result = json.loads(content)
    if not isinstance(result, dict):
        raise ValueError("Anthropic full: not an object")
    return result

# Simple heuristic fallback that extracts prefix/root/suffix
def get_mock_analysis(word, analysis_type='morphemes'):
    w = re.sub(r"[^A-Za-z\-']", "", word)
    if not w or re.search(r"\d", w):
        return {"word": word, "morphemes": []}

    prefixes = {
        "anti": "against", "auto": "self", "bi": "two", "co": "together",
        "contra": "against", "de": "down/away", "dis": "not/opposite",
        "en": "cause to", "em": "cause to", "ex": "out", "fore": "before",
        "im": "not", "in": "not/into", "inter": "between", "mis": "wrongly",
        "non": "not", "over": "too much", "pre": "before", "pro": "forward",
        "re": "again", "sub": "under", "super": "above", "trans": "across",
        "un": "not", "under": "below"
    }
    suffixes = {
        "able": "capable of", "ible": "capable of", "al": "relating to",
        "ed": "past tense", "en": "made of", "er": "one who/more",
        "est": "most", "ful": "full of", "ic": "relating to", "ing": "action",
        "ion": "act/state", "tion": "act", "ation": "act",
        "ity": "state/quality", "ive": "tending to", "less": "without",
        "ly": "in the manner of", "ment": "result", "ness": "state",
        "ous": "full of", "s": "plural", "es": "plural"
    }

    # find longest matching prefix/suffix
    p = ""
    for cand in sorted(prefixes.keys(), key=len, reverse=True):
        if w.lower().startswith(cand):
            p = cand
            break

    s = ""
    for cand in sorted(suffixes.keys(), key=len, reverse=True):
        if w.lower().endswith(cand) and len(w) > len(cand):
            s = cand
            break

    start = len(p)
    end_trim = len(s)
    core = w[start: len(w) - (end_trim if end_trim else 0)]
    segments = []

    if p:
        segments.append({"morpheme": p, "type": "prefix", "meaning": prefixes[p]})
    if core:
        segments.append({"morpheme": core, "type": "root", "meaning": "root/base"})
    if s:
        segments.append({"morpheme": s, "type": "suffix", "meaning": suffixes[s]})

    if not segments:
        segments = [{"morpheme": word, "type": "root", "meaning": "root/base"}]

    return {"word": word, "morphemes": segments}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
