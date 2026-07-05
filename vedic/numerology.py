#!/usr/bin/env python3
"""Find Twilio phone numbers matching numerology criteria.

Given a Mulank (BN) and Bhayank (DN), search Twilio for available numbers where:
  1. >=50% of the (post-country-code) digits are BN or DN.
  2. The repeated digital root of those digits equals BN or DN.

Strategy: Twilio's Contains parameter only supports `*` as a single-digit wildcard
(no character classes), so we enumerate length-k patterns made of {BN, DN} and call
AvailablePhoneNumbers Local with Contains=<pattern> for each.

A single fixed k is too exclusive -- especially when BN==DN, where length-5 collapses
to a single pattern like "55555" and misses numbers with the BN/DN digits scattered
or in shorter runs. Instead, we search across multiple anchor lengths (default 2,3,4,5),
union the results, dedupe by phone number, and let the post-filter enforce the >=50%
and digital-root rules. Twilio caps each Contains query at PageSize results regardless
of true inventory match count, and empirically different anchor lengths return disjoint
slices of inventory -- so more anchors strictly yield more candidates. Larger k (e.g. 5)
actually surfaces the most numbers per BN/DN pair because each of its 32 patterns samples
a different inventory slice; smaller k (e.g. 2) supplements with a few dozen extra hits.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from itertools import product
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth


COUNTRY_DIAL_PREFIX = {
    "US": "1", "CA": "1", "GB": "44", "IN": "91", "AU": "61",
    "DE": "49", "FR": "33", "MX": "52", "BR": "55", "JP": "81",
}


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def digital_root(digits: str) -> int:
    s = sum(int(c) for c in digits if c.isdigit())
    while s > 9:
        s = sum(int(c) for c in str(s))
    return s


def strip_country_code(e164: str, country: str) -> str:
    prefix = COUNTRY_DIAL_PREFIX.get(country, "1")
    bare = e164.lstrip("+")
    return bare[len(prefix):] if bare.startswith(prefix) else bare


def generate_anchors(bn: int, dn: int, length: int) -> list[str]:
    digits = sorted({str(bn), str(dn)})
    return ["".join(p) for p in product(digits, repeat=length)]


def search_twilio(
    auth: HTTPBasicAuth,
    account_sid: str,
    country: str,
    contains: str,
    area_code: str | None,
    page_size: int,
) -> list[dict]:
    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"
        f"/AvailablePhoneNumbers/{country}/Local.json"
    )
    params: dict[str, str | int] = {"Contains": contains, "PageSize": page_size}
    if area_code:
        params["AreaCode"] = area_code
    resp = requests.get(url, auth=auth, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("available_phone_numbers", [])


def score_number(domestic: str, bn: int, dn: int) -> dict:
    bn_dn = {str(bn), str(dn)}
    count = sum(1 for c in domestic if c in bn_dn)
    longest_run = max_run = 1
    for i in range(1, len(domestic)):
        if domestic[i] == domestic[i - 1]:
            max_run += 1
            longest_run = max(longest_run, max_run)
        else:
            max_run = 1
    longest_bn_dn_run = cur = 0
    for c in domestic:
        if c in bn_dn:
            cur += 1
            longest_bn_dn_run = max(longest_bn_dn_run, cur)
        else:
            cur = 0
    return {
        "bn_dn_count": count,
        "bn_dn_pct": round(count / len(domestic), 3),
        "digital_root": digital_root(domestic),
        "longest_repeat_run": longest_run,
        "longest_bn_dn_run": longest_bn_dn_run,
        "trailing4": domestic[-4:],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bn", type=int, required=True, help="Mulank / Birth Number (1-9)")
    p.add_argument("--dn", type=int, required=True, help="Bhayank / Destiny Number (1-9)")
    p.add_argument("--country", default="US", help="ISO country code (default: US)")
    p.add_argument("--area-code", default=None, help="Optional area code filter")
    p.add_argument("--anchor-lengths", "-k", default="2,3,4,5",
                   help="Comma-separated anchor pattern lengths to search (default: 2,3,4,5). "
                        "Results across all lengths are unioned and deduped before post-filter. "
                        "Twilio caps each Contains query at PageSize results regardless of how many "
                        "actually match in inventory, and different anchor lengths sample disjoint "
                        "slices of the inventory -- so more anchors yield strictly more candidates.")
    p.add_argument("--page-size", type=int, default=50,
                   help="Twilio results per anchor (max ~50 for Local)")
    p.add_argument("--out", default="ranked_phone_numbers.csv")
    p.add_argument("--env", default=".env")
    p.add_argument("--sleep", type=float, default=0.0,
                   help="Seconds to sleep between API calls (rate limit cushion)")
    args = p.parse_args()

    if not (1 <= args.bn <= 9 and 1 <= args.dn <= 9):
        print("BN and DN must each be 1-9", file=sys.stderr)
        return 2

    try:
        lengths = sorted({int(x) for x in args.anchor_lengths.split(",") if x.strip()}, reverse=True)
    except ValueError:
        print(f"--anchor-lengths must be comma-separated ints, got: {args.anchor_lengths!r}", file=sys.stderr)
        return 2
    if not lengths or any(L < 1 or L > 10 for L in lengths):
        print("--anchor-lengths values must be in 1..10", file=sys.stderr)
        return 2
    if args.bn == args.dn:
        print(f"Note: BN==DN=={args.bn}; each length contributes a single pattern.", file=sys.stderr)

    env = load_env(Path(args.env))
    sid = env.get("TWILIO_ACCOUNT_SID") or os.environ.get("TWILIO_ACCOUNT_SID")
    key_sid = env.get("TWILIO_API_KEY_SID") or os.environ.get("TWILIO_API_KEY_SID")
    key_secret = env.get("TWILIO_API_KEY_SECRET") or os.environ.get("TWILIO_API_KEY_SECRET")
    token = env.get("TWILIO_AUTH_TOKEN") or os.environ.get("TWILIO_AUTH_TOKEN")
    if not sid:
        print("TWILIO_ACCOUNT_SID missing from .env", file=sys.stderr)
        return 2
    if key_sid and key_secret:
        auth = HTTPBasicAuth(key_sid, key_secret)
    elif token:
        auth = HTTPBasicAuth(sid, token)
    else:
        print("Need TWILIO_API_KEY_SID+SECRET or TWILIO_AUTH_TOKEN", file=sys.stderr)
        return 2

    anchors_by_len = {L: generate_anchors(args.bn, args.dn, L) for L in lengths}
    total_anchors = sum(len(a) for a in anchors_by_len.values())
    summary = ", ".join(f"k={L}:{len(anchors_by_len[L])}" for L in lengths)
    print(f"BN={args.bn} DN={args.dn}  anchors={total_anchors} ({summary})  "
          f"country={args.country}  area_code={args.area_code or '-'}", file=sys.stderr)

    seen: dict[str, dict] = {}
    i = 0
    for L in lengths:
        anchors = anchors_by_len[L]
        for anchor in anchors:
            i += 1
            try:
                results = search_twilio(auth, sid, args.country, anchor, args.area_code, args.page_size)
            except requests.HTTPError as e:
                body = e.response.text[:200] if e.response is not None else ""
                print(f"  [{i}/{total_anchors}] k={L} {anchor}: HTTP error {e}  {body}", file=sys.stderr)
                continue
            new = 0
            for r in results:
                num = r.get("phone_number")
                if not num or num in seen:
                    continue
                seen[num] = r
                new += 1
            print(f"  [{i}/{total_anchors}] k={L} Contains={anchor}: {len(results)} hits "
                  f"(+{new} new, {len(seen)} unique total)", file=sys.stderr)
            if args.sleep:
                time.sleep(args.sleep)

    matches: list[dict] = []
    for num, r in seen.items():
        domestic = strip_country_code(num, args.country)
        if not domestic.isdigit():
            continue
        s = score_number(domestic, args.bn, args.dn)
        if s["bn_dn_pct"] < 0.5:
            continue
        if s["digital_root"] not in (args.bn, args.dn):
            continue
        matches.append({
            "phone_number": num,
            "domestic": domestic,
            "friendly_name": r.get("friendly_name", ""),
            "locality": r.get("locality", ""),
            "region": r.get("region", ""),
            "iso_country": r.get("iso_country", ""),
            **s,
        })

    matches.sort(key=lambda m: (
        -m["bn_dn_pct"],
        -m["longest_bn_dn_run"],
        -m["longest_repeat_run"],
        m["domestic"],
    ))

    if matches:
        out_path = Path(args.out)
        with out_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(matches[0].keys()))
            w.writeheader()
            w.writerows(matches)
        print(f"\n{len(matches)} matches written -> {out_path}", file=sys.stderr)
        for m in matches[:10]:
            print(f"  {m['phone_number']}  {m['bn_dn_count']}/10 BN-DN  "
                  f"root={m['digital_root']}  run={m['longest_bn_dn_run']}  "
                  f"{m['locality']},{m['region']}", file=sys.stderr)
    else:
        print("\nNo matches passed both filters.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
