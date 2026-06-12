export type NumerologySystem = "vedic" | "chaldean";

// Vedic and Chaldean charts are identical for 24 of 26 letters; they differ
// only at C (2 vs 3) and X (6 vs 5). Chaldean assigns no 9 (9 is left sacred).
export const VEDIC_LETTER_VALUES: Record<string, number> = {
  A: 1, B: 2, C: 2, D: 4, E: 5, F: 8, G: 3, H: 5, I: 1,
  J: 1, K: 2, L: 3, M: 4, N: 5, O: 7, P: 8, Q: 1, R: 2,
  S: 3, T: 4, U: 6, V: 6, W: 6, X: 6, Y: 1, Z: 7,
};

export const CHALDEAN_LETTER_VALUES: Record<string, number> = {
  A: 1, B: 2, C: 3, D: 4, E: 5, F: 8, G: 3, H: 5, I: 1,
  J: 1, K: 2, L: 3, M: 4, N: 5, O: 7, P: 8, Q: 1, R: 2,
  S: 3, T: 4, U: 6, V: 6, W: 6, X: 5, Y: 1, Z: 7,
};

export const SYSTEM_LETTER_VALUES: Record<
  NumerologySystem,
  Record<string, number>
> = {
  vedic: VEDIC_LETTER_VALUES,
  chaldean: CHALDEAN_LETTER_VALUES,
};

// Back-compat alias for callers predating the system toggle.
export const LETTER_VALUES = VEDIC_LETTER_VALUES;

export type LetterPair = { letter: string; value: number };

export function letterBreakdown(
  name: string,
  system: NumerologySystem = "vedic"
): LetterPair[] {
  const values = SYSTEM_LETTER_VALUES[system];
  return Array.from(name.toUpperCase())
    .filter((c) => c in values)
    .map((c) => ({ letter: c, value: values[c] }));
}

export function reduceToRoot(n: number): number {
  while (n > 9) {
    n = String(n).split("").reduce((s, d) => s + Number(d), 0);
  }
  return n;
}

export type NameResult = {
  total: number;
  root: number;
  pairs: LetterPair[];
};

export function nameNumber(
  name: string,
  system: NumerologySystem = "vedic"
): NameResult {
  const pairs = letterBreakdown(name, system);
  const total = pairs.reduce((s, p) => s + p.value, 0);
  return { total, root: reduceToRoot(total), pairs };
}

// Twilio AvailablePhoneNumbers resource types we query against. Most non-US
// countries do not stock Local inventory; their numbers live under Mobile or
// National. Order matters — earlier types are probed first.
export type TwilioNumberType =
  | "Local"
  | "Mobile"
  | "National"
  | "TollFree";

export type CountrySpec = {
  code: string;
  name: string;
  dialPrefix: string;
  // Acceptable domestic-number length range (digits remaining after the dial
  // prefix is stripped from E.164). domesticMin doubles as the pattern
  // generation length: substring matches against longer numbers still hit.
  domesticMin: number;
  domesticMax: number;
  numberTypes: TwilioNumberType[];
};

// numberTypes are the AvailablePhoneNumbers subresources Twilio actually
// exposes for the country. Probing a non-existent subresource returns a 20404
// (e.g. AU/National doesn't exist), wasting queries — values below were
// cross-checked against Twilio's per-country regulatory pages 2026-04. The
// route layer also short-circuits on 20404 at runtime, so a wrong entry here
// degrades cleanly instead of breaking the search.
export const COUNTRY_SPECS: Record<string, CountrySpec> = {
  US: { code: "US", name: "United States",  dialPrefix: "1",  domesticMin: 10, domesticMax: 10, numberTypes: ["Local", "TollFree"] },
  CA: { code: "CA", name: "Canada",         dialPrefix: "1",  domesticMin: 10, domesticMax: 10, numberTypes: ["Local", "TollFree"] },
  GB: { code: "GB", name: "United Kingdom", dialPrefix: "44", domesticMin: 10, domesticMax: 10, numberTypes: ["Local", "Mobile", "National", "TollFree"] },
  IN: { code: "IN", name: "India",          dialPrefix: "91", domesticMin: 10, domesticMax: 10, numberTypes: ["Mobile"] },
  AU: { code: "AU", name: "Australia",      dialPrefix: "61", domesticMin: 9,  domesticMax: 9,  numberTypes: ["Local", "Mobile"] },
  DE: { code: "DE", name: "Germany",        dialPrefix: "49", domesticMin: 10, domesticMax: 11, numberTypes: ["Local", "Mobile"] },
  FR: { code: "FR", name: "France",         dialPrefix: "33", domesticMin: 9,  domesticMax: 9,  numberTypes: ["Local", "Mobile"] },
  MX: { code: "MX", name: "Mexico",         dialPrefix: "52", domesticMin: 10, domesticMax: 10, numberTypes: ["Local", "Mobile"] },
  BR: { code: "BR", name: "Brazil",         dialPrefix: "55", domesticMin: 10, domesticMax: 11, numberTypes: ["Mobile", "Local"] },
  JP: { code: "JP", name: "Japan",          dialPrefix: "81", domesticMin: 9,  domesticMax: 10, numberTypes: ["Local"] },
};

export function getCountrySpec(code: string): CountrySpec | null {
  return COUNTRY_SPECS[code] ?? null;
}

export const COUNTRY_OPTIONS: { code: string; name: string }[] = Object.values(
  COUNTRY_SPECS
).map(({ code, name }) => ({ code, name }));

// Back-compat: a few callers still want the bare prefix map.
export const COUNTRY_DIAL_PREFIX: Record<string, string> = Object.fromEntries(
  Object.values(COUNTRY_SPECS).map((s) => [s.code, s.dialPrefix])
);

export function mulankFromDob(dob: string): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dob);
  if (!m) return null;
  return reduceToRoot(Number(m[3]));
}

export function bhagyankFromDob(dob: string): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dob);
  if (!m) return null;
  const sum = Array.from(dob.replace(/-/g, "")).reduce((s, d) => s + Number(d), 0);
  return reduceToRoot(sum);
}

export function digitalRoot(digits: string): number {
  let s = Array.from(digits)
    .filter((c) => /\d/.test(c))
    .reduce((a, c) => a + Number(c), 0);
  while (s > 9) {
    s = String(s).split("").reduce((a, d) => a + Number(d), 0);
  }
  return s;
}

export function stripCountryCode(e164: string, country: string): string {
  const spec = COUNTRY_SPECS[country];
  const bare = e164.replace(/^\+/, "");
  if (!spec) return bare;
  return bare.startsWith(spec.dialPrefix) ? bare.slice(spec.dialPrefix.length) : bare;
}

export function generateAnchors(bn: number, dn: number, length: number): string[] {
  const digits = Array.from(new Set([String(bn), String(dn)])).sort();
  const out: string[] = [];
  const total = digits.length ** length;
  for (let i = 0; i < total; i++) {
    let s = "";
    let x = i;
    for (let j = 0; j < length; j++) {
      s = digits[x % digits.length] + s;
      x = Math.floor(x / digits.length);
    }
    out.push(s);
  }
  return out;
}

export type PhoneScore = {
  bn_dn_count: number;
  bn_dn_pct: number;
  digital_root: number;
  longest_repeat_run: number;
  longest_bn_dn_run: number;
  trailing4: string;
};

export function scoreNumber(domestic: string, bn: number, dn: number): PhoneScore {
  const bnDn = new Set([String(bn), String(dn)]);
  const count = Array.from(domestic).filter((c) => bnDn.has(c)).length;

  let longestRun = 1;
  let maxRun = 1;
  for (let i = 1; i < domestic.length; i++) {
    if (domestic[i] === domestic[i - 1]) {
      maxRun++;
      longestRun = Math.max(longestRun, maxRun);
    } else {
      maxRun = 1;
    }
  }

  let longestBnDnRun = 0;
  let cur = 0;
  for (const c of domestic) {
    if (bnDn.has(c)) {
      cur++;
      longestBnDnRun = Math.max(longestBnDnRun, cur);
    } else {
      cur = 0;
    }
  }

  return {
    bn_dn_count: count,
    bn_dn_pct: Math.round((count / domestic.length) * 1000) / 1000,
    digital_root: digitalRoot(domestic),
    longest_repeat_run: longestRun,
    longest_bn_dn_run: longestBnDnRun,
    trailing4: domestic.slice(-4),
  };
}

export type TwilioNumber = {
  phone_number: string;
  friendly_name: string;
  locality: string;
  region: string;
  iso_country: string;
};

export type Match = TwilioNumber & PhoneScore & { domestic: string };

export function sortMatches(matches: Match[]): Match[] {
  return [...matches].sort((a, b) =>
    b.bn_dn_pct - a.bn_dn_pct ||
    b.longest_bn_dn_run - a.longest_bn_dn_run ||
    b.longest_repeat_run - a.longest_repeat_run ||
    a.domestic.localeCompare(b.domestic)
  );
}
