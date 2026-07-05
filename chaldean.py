"""Chaldean numerology — analyse a full name + DOB and suggest modifications
that move the namank into harmony with moolank and bhagyank.

Supports names of any length (any number of middle names).

Completeness of the modification search
---------------------------------------
A single edit (insert / delete / replace) can change a part's sanyuktank by at
most 8 (F = P = 8). Hence with a total edit budget of `max_mods`:

  necessary  (1)  |Δᵢ| ≤ 8·max_mods           for every part i
  necessary  (2)  Σᵢ |Δᵢ| ≤ 8·max_mods         joint budget bound
  sufficient (3)  Δᵢ reachable in mᵢ edits and Σ mᵢ ≤ max_mods

`find_valid_splits` enumerates every auspicious split satisfying (1) and (2).
`filter_by_reachability` keeps only those satisfying (3), where mᵢ is the
minimum-edit count via BFS over `single_mod_deltas`. (BFS is a lower bound on
the true minimum — exact for typical inputs; it can occasionally overstate
reachability when length or letter-multiplicity constraints bite, in which
case the downstream DFS simply returns no names for that split.)

For every reachable split we then enumerate ALL names per part at every depth
d ∈ [mᵢ, mᵢ + spare] (where spare = max_mods − Σmⱼ), and take the depth-
constrained Cartesian product, so no in-budget name is dropped.
"""

import heapq
from difflib import SequenceMatcher

import jellyfish


# --- Constants ---------------------------------------------------------------

LETTERS = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 8, 'G': 3,
    'H': 5, 'I': 1, 'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5,
    'O': 7, 'P': 8, 'Q': 1, 'R': 2, 'S': 3, 'T': 4, 'U': 6,
    'V': 6, 'W': 6, 'X': 5, 'Y': 1, 'Z': 7,
}

REVERSE_LETTERS = {
    1: ['A', 'I', 'J', 'Q', 'Y'],
    2: ['B', 'K', 'R'],
    3: ['C', 'G', 'L', 'S'],
    4: ['D', 'M', 'T'],
    5: ['E', 'H', 'N', 'X'],
    6: ['U', 'V', 'W'],
    7: ['O', 'Z'],
    8: ['F', 'P'],
}

MOOLANK_BHAGYANK = {
    1: {'friendly': [1, 2, 3, 5, 6, 9], 'neutral': [4, 7],       'enemy': [8]},
    2: {'friendly': [1, 2, 3, 5],       'neutral': [7, 6],       'enemy': [4, 8, 9]},
    3: {'friendly': [1, 2, 3, 5],       'neutral': [4, 7, 8, 9], 'enemy': [6]},
    4: {'friendly': [1, 5, 6, 7],       'neutral': [3],          'enemy': [2, 4, 8, 9]},
    5: {'friendly': [1, 2, 3, 5, 6],    'neutral': [4, 7, 8, 9], 'enemy': []},
    6: {'friendly': [1, 4, 5, 6, 7],    'neutral': [2, 8, 9],    'enemy': [3]},
    7: {'friendly': [1, 3, 4, 5, 6],    'neutral': [2, 7, 8, 9], 'enemy': []},
    8: {'friendly': [3, 5, 6, 7],       'neutral': [9],          'enemy': [1, 2, 4, 8]},
    9: {'friendly': [1, 3, 5],          'neutral': [6, 7, 8, 9], 'enemy': [4, 2]},
}

NAMANK_MB = {
    1: {'friend': [1, 2, 3, 4, 5, 7, 9],    'neutral': [],  'enemy': [6, 8]},
    2: {'friend': [1, 2, 3, 4, 7, 8],       'neutral': [9], 'enemy': [5, 6]},
    3: {'friend': [1, 2, 3, 5, 6, 8, 9],    'neutral': [],  'enemy': [4, 7]},
    4: {'friend': [1, 2, 5, 7, 9],          'neutral': [],  'enemy': [3, 4, 6, 8]},
    5: {'friend': [1, 3, 4, 5, 6, 7, 8, 9], 'neutral': [],  'enemy': [2]},
    6: {'friend': [3, 5, 8, 9],             'neutral': [7], 'enemy': [1, 2, 4, 6]},
    7: {'friend': [1, 2, 4, 5],             'neutral': [],  'enemy': [3, 6, 7, 8, 9]},
    8: {'friend': [2, 3, 5, 6],             'neutral': [],  'enemy': [1, 4, 7, 8, 9]},
    9: {'friend': [1, 2, 3, 4, 5, 6],       'neutral': [],  'enemy': [7, 8, 9]},
}

COMPOUND_AUSPICIOUS = {
    10: True,  11: False, 12: False, 13: True,  14: False,
    15: True,  16: False, 17: True,  18: False, 19: True,
    20: True,  21: True,  22: False, 23: True,  24: True,
    25: True,  26: False, 27: True,  28: False, 29: False,
    30: True,  31: True,  32: True,  33: True,  34: True,
    35: False, 36: True,  37: True,  38: False, 39: True,
    40: True,  41: True,  42: True,  43: False, 44: False,
    45: True,  46: True,  47: False, 48: True,  49: True,
    50: True,  51: True,  52: False,
}

COMPOUNDS_FOR_NAMANK = {
    1: [10, 19, 28, 37, 46, 55, 64, 73],
    2: [11, 20, 29, 38, 47, 56, 65, 74],
    3: [12, 21, 30, 39, 48, 57, 66, 75],
    4: [13, 22, 31, 40, 49, 58, 67, 76],
    5: [14, 23, 32, 41, 50, 59, 68, 77],
    6: [15, 24, 33, 42, 51, 60, 69],
    7: [16, 25, 34, 43, 52, 61, 70],
    8: [17, 26, 35, 44, 53, 62, 71],
    9: [18, 27, 36, 45, 54, 63, 72],
}

VOWELS = set("AEIOU")
VOWELS_Y = set("AEIOUY")


# --- Numerology primitives ---------------------------------------------------

def reduce_digits(n):
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def is_compound_auspicious(s):
    if s < 10:
        return True
    if s > 52:
        count = 0
        while s > 18:
            s -= 9
            count += is_compound_auspicious(s)
        if count / (s / 9) > 0.5:
            return True
    return COMPOUND_AUSPICIOUS.get(s, True)


def sanyuktank(part):
    return sum(LETTERS.get(c, 0) for c in part.upper())


# --- Scoring -----------------------------------------------------------------

def phonotactic_score(name):
    """Pronounceability heuristic. Higher = better."""
    s = name.upper()
    if not s:
        return -100
    score = 0.0

    vc = sum(1 for c in s if c in VOWELS_Y)
    score -= abs(vc / len(s) - 0.4) * 8

    run = mx = 0
    for c in s:
        run = 0 if c in VOWELS_Y else run + 1
        mx = max(mx, run)
    if mx >= 3:
        score -= (mx - 2) * 4

    run = mx = 0
    for c in s:
        run = run + 1 if c in VOWELS_Y else 0
        mx = max(mx, run)
    if mx >= 3:
        score -= (mx - 2) * 2

    for i in range(len(s) - 2):
        if s[i] == s[i+1] == s[i+2]:
            score -= 6

    if len(s) >= 2 and s[0] == s[1]:
        score -= 4
    if len(s) >= 2 and s[0] not in VOWELS_Y and s[1] not in VOWELS_Y:
        score -= 2

    return score


def sound_similarity(modified, original):
    """How close `modified` sounds to `original`. Range ~0..1."""
    m = jellyfish.metaphone(modified)
    o = jellyfish.metaphone(original)
    sim = SequenceMatcher(None, m, o).ratio()
    if jellyfish.soundex(modified)[:1] != jellyfish.soundex(original)[:1]:
        sim -= 0.15
    return sim


def name_score(modified_parts, original_parts,
               w_phono=1.0, w_sim=20.0, mod_penalty=0.5, n_mods=0):
    """Composite score across all name parts."""
    phono = sum(phonotactic_score(p) for p in modified_parts)
    sim   = sum(sound_similarity(m, o) for m, o in zip(modified_parts, original_parts))
    return w_phono * phono + w_sim * sim - mod_penalty * n_mods


# --- Modification enumeration ------------------------------------------------

def get_allowed_letters(part, relative_initials, name_letters=frozenset()):
    """Letters allowed for insertion or as replacement targets:
    vowels ∪ letters anywhere in the full name ∪ letters from
    `relative_initials`.

    `name_letters` is the union of letters across all parts of the full name;
    pass it so that, e.g., a letter present in the surname can be added to the
    first name. When omitted, only this `part`'s own letters are used."""
    s = set(VOWELS) | set(part.upper()) | set(name_letters)
    for init in relative_initials:
        s |= set(init.upper())
    return s


def single_mod_deltas(part, allowed):
    """Set of possible sanyuktank deltas from a single insertion/deletion/replacement."""
    part = part.upper()
    name_vals = {LETTERS[c] for c in part}
    allowed_vals = {LETTERS[c] for c in allowed}
    deltas = set(allowed_vals)                 # insertion
    deltas |= {-v for v in name_vals}          # deletion
    for vo in name_vals:                       # replacement
        for vn in allowed_vals:
            deltas.add(vn - vo)
    deltas.discard(0)
    return deltas


def min_mods_to_reach(part, target_delta, allowed, max_mods=3):
    """Minimum number of single mods needed to change `part`'s sanyuktank by
    `target_delta`. Returns None if not reachable within `max_mods`."""
    if target_delta == 0:
        return 0
    single = single_mod_deltas(part, allowed)
    reachable, frontier = {0}, {0}
    for k in range(1, max_mods + 1):
        nxt = set()
        for d in frontier:
            for s in single:
                if d + s not in reachable:
                    reachable.add(d + s)
                    nxt.add(d + s)
        if target_delta in reachable:
            return k
        frontier = nxt
    return None


def enumerate_modified_names(part, target_delta, num_mods, allowed, limit=None):
    """All strings reachable from `part` via exactly `num_mods` insertions /
    deletions / replacements that produce sanyuktank delta == target_delta."""
    part = part.upper()
    if num_mods == 0:
        return {part} if target_delta == 0 else set()
    allowed = sorted(allowed)
    results = set()

    def dfs(cur, left, delta):
        if left == 0:
            if delta == target_delta:
                results.add(cur)
            return
        if abs(target_delta - delta) > 8 * left:
            return
        if limit and len(results) >= limit:
            return
        for i in range(len(cur) + 1):                  # insertion
            for L in allowed:
                nd = delta + LETTERS[L]
                if abs(target_delta - nd) > 8 * (left - 1):
                    continue
                dfs(cur[:i] + L + cur[i:], left - 1, nd)
                if limit and len(results) >= limit:
                    return
        if len(cur) > 1:                                # deletion
            for i in range(len(cur)):
                nd = delta - LETTERS[cur[i]]
                if abs(target_delta - nd) > 8 * (left - 1):
                    continue
                dfs(cur[:i] + cur[i+1:], left - 1, nd)
                if limit and len(results) >= limit:
                    return
        for i in range(len(cur)):                       # replacement
            ov = LETTERS[cur[i]]
            for L in allowed:
                if L == cur[i]:
                    continue
                nd = delta - ov + LETTERS[L]
                if abs(target_delta - nd) > 8 * (left - 1):
                    continue
                dfs(cur[:i] + L + cur[i+1:], left - 1, nd)
                if limit and len(results) >= limit:
                    return

    dfs(part, num_mods, 0)
    return results


# --- Multi-part splits -------------------------------------------------------

def find_valid_splits(part_sums, target_namanks, max_mods=3,
                      max_delta_per_part=None):
    """All (new_sums, deltas) tuples satisfying the *necessary* edit-budget
    conditions for reachability in ≤ max_mods edits:

      • each new sanyuktank is an auspicious compound
      • |Δᵢ| ≤ 8 · max_mods                (single-part bound)
      • Σ |Δᵢ| ≤ 8 · max_mods              (joint-budget bound)
      • reduce_digits(Σ new sanyuktanks) ∈ target_namanks

    Reachability is verified downstream by `filter_by_reachability`.

    Setting `max_delta_per_part` overrides the default tight bound; the joint
    sum prune is always active.
    """
    if max_delta_per_part is None:
        max_delta_per_part = 8 * max_mods
    max_total_abs_delta = 8 * max_mods

    auspicious_per_part = []
    for s in part_sums:
        vals = [v for v in range(max(1, s - max_delta_per_part),
                                 s + max_delta_per_part + 1)
                if is_compound_auspicious(v)]
        auspicious_per_part.append(vals)

    results = []
    n = len(part_sums)

    def recurse(idx, current, total, abs_delta_sum):
        if idx == n:
            if reduce_digits(total) in target_namanks:
                deltas = tuple(c - s for c, s in zip(current, part_sums))
                results.append((tuple(current), deltas))
            return
        s_orig = part_sums[idx]
        for v in auspicious_per_part[idx]:
            new_abs = abs_delta_sum + abs(v - s_orig)
            if new_abs > max_total_abs_delta:
                continue
            current.append(v)
            recurse(idx + 1, current, total + v, new_abs)
            current.pop()

    recurse(0, [], 0, 0)
    results.sort(key=lambda x: sum(abs(d) for d in x[1]))
    return results


def enumerate_with_depths(part, target_delta, min_mods, max_depth,
                          allowed, limit=None):
    """For every name reachable from `part` in d edits with sanyuktank delta
    = target_delta (d ∈ [min_mods, max_depth]), return {name: smallest d at
    which the DFS encountered it}. Used to enumerate all in-budget variants
    per part, not just the cheapest."""
    result = {}
    for d in range(min_mods, max_depth + 1):
        names = enumerate_modified_names(part, target_delta, d, allowed, limit)
        for name in names:
            if name not in result:
                result[name] = d
    return result


def filter_by_reachability(splits, parts, relative_initials, max_mods=3):
    """Keep only splits where each part's delta is reachable, and the total
    mod count across parts is ≤ max_mods."""
    name_letters = set("".join(parts).upper())
    allowed_per_part = [get_allowed_letters(p, relative_initials, name_letters)
                        for p in parts]
    keep = []
    for new_sums, deltas in splits:
        mods_per = []
        for part, delta, allowed in zip(parts, deltas, allowed_per_part):
            m = min_mods_to_reach(part, delta, allowed, max_mods)
            if m is None:
                break
            mods_per.append(m)
        else:
            if sum(mods_per) <= max_mods:
                keep.append((new_sums, deltas, tuple(mods_per)))
    keep.sort(key=lambda x: (sum(x[2]), sum(abs(d) for d in x[1])))
    return keep


# --- Main analysis -----------------------------------------------------------

DEFAULT_CANDIDATE_NAMANKS = [1, 3, 5, 6, 9]


def analyze(fullname, dob, relative_initials,
            max_mods=3,
            candidate_namanks=DEFAULT_CANDIDATE_NAMANKS,
            per_part_enum_limit=None,
            top_k_heap=10000,
            top_n=2000,
            max_delta_per_part=None):
    """Run the full analysis and print ranked name suggestions.

    Parameters
    ----------
    max_mods : int
        Total edit budget across all name parts.
    candidate_namanks : list[int]
        Single-digit namanks considered intrinsically auspicious. Targets are
        the subset friendly with both moolank and bhagyank.
    per_part_enum_limit : int | None
        Cap on names enumerated per (part, depth). None = exhaustive.
    top_k_heap : int
        Number of top-scoring full-name combos kept in memory.
    top_n : int
        How many to print.
    max_delta_per_part : int | None
        Override the default tight per-part Δ range (8·max_mods). Lower it for
        speed; raising above 8·max_mods has no effect on completeness.
    """
    parts = fullname.split()
    assert all(c.isalpha() for c in fullname.replace(" ", "")), \
        "name must be alphabetic"
    assert len(parts) >= 1

    moolank  = reduce_digits(int(dob.split("/")[0]))
    bhagyank = reduce_digits(sum(int(d) for d in dob.replace("/", "")))

    part_sums = [sanyuktank(p) for p in parts]
    total = sum(part_sums)
    namank = reduce_digits(total)

    print(f"{fullname} {dob}")
    print(f"{' + '.join(str(s) for s in part_sums)} = {total} ({namank})")

    mb_harmony = moolank not in MOOLANK_BHAGYANK[bhagyank]['enemy']
    nm_harmony = namank  not in NAMANK_MB[moolank]['enemy']
    nb_harmony = namank  not in NAMANK_MB[bhagyank]['enemy']
    print(f"Moolank-Bhagyank ({moolank}-{bhagyank}) harmony: {'✓' if mb_harmony else '✗'}")
    print(f"Namank-Moolank ({namank}-{moolank}) harmony: {'✓' if nm_harmony else '✗'}")
    print(f"Namank-Bhagyank ({namank}-{bhagyank}) harmony: {'✓' if nb_harmony else '✗'}")

    for part, s in zip(parts, part_sums):
        print(f"  {part} ({s}) auspicious: {'✓' if is_compound_auspicious(s) else '✗'}")
    print(f"  Total ({total}) auspicious: {'✓' if is_compound_auspicious(total) else '✗'}")

    new_namanks = [n for n in candidate_namanks
                   if moolank not in NAMANK_MB[n]['enemy']
                   and bhagyank not in NAMANK_MB[n]['enemy']]
    print(f"\nTarget namanks: {new_namanks}")

    splits = find_valid_splits(part_sums, new_namanks, max_mods,
                               max_delta_per_part=max_delta_per_part)
    candidates = filter_by_reachability(splits, parts, relative_initials, max_mods)

    print(f"\n{len(candidates)} reachable candidates (≤{max_mods} mods):")
    headers = ([f"p{i+1}" for i in range(len(parts))]
               + [f"Δ{i+1}" for i in range(len(parts))]
               + [f"m{i+1}" for i in range(len(parts))]
               + ["sum", "nk"])
    print(" ".join(f"{h:>4}" for h in headers))
    for new_sums, deltas, mods in candidates:
        tot = sum(new_sums)
        row = (list(new_sums)
               + [f"{d:+d}" for d in deltas]
               + list(mods)
               + [tot, reduce_digits(tot)])
        print(" ".join(f"{v!s:>4}" for v in row))

    # Exhaustive in-budget enumeration: for every split, each part may use up
    # to (mᵢ + spare) edits where spare = max_mods − Σmⱼ. Cartesian-product
    # combos are kept iff the depth sum stays within budget.
    name_letters = set("".join(parts).upper())
    allowed_per_part = [get_allowed_letters(p, relative_initials, name_letters)
                        for p in parts]
    heap = []        # min-heap of (score, combo, total_depth, sum, nk)
    total_combos = 0
    truncated = False

    for new_sums, deltas, mods in candidates:
        spare = max_mods - sum(mods)
        per_part = []
        skip = False
        for p, d_target, m, allowed in zip(parts, deltas, mods, allowed_per_part):
            max_d = m + spare
            names_d = enumerate_with_depths(p, d_target, m, max_d, allowed,
                                            limit=per_part_enum_limit)
            if not names_d:
                skip = True
                break
            per_part.append(list(names_d.items()))
        if skip:
            continue

        def gen(idx, names, depth_sum):
            if idx == len(per_part):
                yield tuple(names), depth_sum
                return
            for name, dpth in per_part[idx]:
                if depth_sum + dpth > max_mods:
                    continue
                names.append(name)
                yield from gen(idx + 1, names, depth_sum + dpth)
                names.pop()

        new_total = sum(new_sums)
        new_nk = reduce_digits(new_total)
        for combo, total_depth in gen(0, [], 0):
            total_combos += 1
            score = name_score(combo, parts,
                               mod_penalty=0.5, n_mods=total_depth)
            item = (score, combo, total_depth, new_total, new_nk)
            if top_k_heap is None or len(heap) < top_k_heap:
                heapq.heappush(heap, item)
            elif score > heap[0][0]:
                heapq.heapreplace(heap, item)
                truncated = True
            else:
                truncated = True

    ranked = sorted(heap, key=lambda x: -x[0])

    cap_note = f" (top {top_k_heap} kept)" if truncated else ""
    print(f"\n{total_combos} full-name candidates{cap_note}. Top {top_n}:\n")
    name_w = max((len(' '.join(c)) for _, c, _, _, _ in ranked[:top_n]), default=20)
    print(f"{'score':>6}  {'name':<{name_w}} {'mods':>5} {'sum':>4} {'nk':>3}")
    for score, combo, m, s, nk in ranked[:top_n]:
        print(f"{score:>6.2f}  {' '.join(combo):<{name_w}} {m:>5} {s:>4} {nk:>3}")


# --- Entrypoint --------------------------------------------------------------

if __name__ == "__main__":
    fullname = "Svetlana Bondar"
    dob = "7/27/1966"  # DD/MM/YYYY
    relative_initials = []

    analyze(fullname, dob, relative_initials)
