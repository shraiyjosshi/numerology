#!/usr/bin/env python3
"""Compare Twilio AvailablePhoneNumbers responses across anchor lengths.

For a given BN/DN, queries each anchor pattern at k=2 and k=5, reports:
  - raw hit count per anchor (capped by Twilio at PageSize)
  - unique numbers per length (after dedupe within length)
  - union/overlap across lengths
  - how many survive the >=50% BN/DN + digital-root post-filter
"""
from __future__ import annotations

import sys
from itertools import product
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

sys.path.insert(0, str(Path(__file__).parent))
from numerology import (
    COUNTRY_DIAL_PREFIX, load_env, digital_root, strip_country_code,
    generate_anchors, search_twilio, score_number,
)

BN, DN = 3, 8
COUNTRY = "US"
PAGE_SIZE = 50
LENGTHS = [2, 5]


def main() -> int:
    env = load_env(Path(".env"))
    sid = env["TWILIO_ACCOUNT_SID"]
    key_sid = env.get("TWILIO_API_KEY_SID")
    key_secret = env.get("TWILIO_API_KEY_SECRET")
    token = env.get("TWILIO_AUTH_TOKEN")
    auth = HTTPBasicAuth(key_sid, key_secret) if key_sid and key_secret else HTTPBasicAuth(sid, token)

    by_length: dict[int, dict[str, dict]] = {L: {} for L in LENGTHS}
    per_anchor: dict[int, list[tuple[str, int]]] = {L: [] for L in LENGTHS}

    for L in LENGTHS:
        anchors = generate_anchors(BN, DN, L)
        print(f"\n=== k={L}: {len(anchors)} patterns ===")
        for a in anchors:
            results = search_twilio(auth, sid, COUNTRY, a, None, PAGE_SIZE)
            per_anchor[L].append((a, len(results)))
            for r in results:
                num = r.get("phone_number")
                if num:
                    by_length[L][num] = r
            print(f"  Contains={a:<6} raw_hits={len(results):>3}  "
                  f"unique_so_far={len(by_length[L]):>4}")

    # Post-filter
    def post_filter(pool: dict[str, dict]) -> int:
        kept = 0
        for num in pool:
            d = strip_country_code(num, COUNTRY)
            if not d.isdigit():
                continue
            s = score_number(d, BN, DN)
            if s["bn_dn_pct"] >= 0.5 and s["digital_root"] in (BN, DN):
                kept += 1
        return kept

    print("\n=== Summary ===")
    for L in LENGTHS:
        total_raw = sum(n for _, n in per_anchor[L])
        unique = len(by_length[L])
        kept = post_filter(by_length[L])
        print(f"  k={L}: anchors={len(per_anchor[L])}  raw_hits={total_raw}  "
              f"unique={unique}  passed_filter={kept}")

    set2 = set(by_length[2])
    set5 = set(by_length[5])
    print(f"\n=== Overlap k=2 vs k=5 (unique numbers) ===")
    print(f"  k=2 only: {len(set2 - set5)}")
    print(f"  k=5 only: {len(set5 - set2)}")
    print(f"  both:     {len(set2 & set5)}")
    print(f"  union:    {len(set2 | set5)}")

    union_pool = {**by_length[2], **by_length[5]}
    print(f"  union passed_filter: {post_filter(union_pool)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
