# Vedic / Chaldean system toggle — design

## Goal

Let the name calculator compute name numbers under either the **Vedic** or the
**Chaldean** letter chart, switchable via a toggle bar on the name page.

## Letter charts

The two charts are identical for 24 of 26 letters. They differ only at:

| Letter | Vedic | Chaldean |
|--------|-------|----------|
| C      | 2     | 3        |
| X      | 6     | 5        |

Full Chaldean chart (per Jyotiṣ Vāstu Academy reference image / `chaldean.py`):

```
A1 B2 C3 D4 E5 F8 G3 H5 I1 J1 K2 L3 M4
N5 O7 P8 Q1 R2 S3 T4 U6 V6 W6 X5 Y1 Z7
```

Note: Chaldean has no value 9 (9 is considered sacred/unassigned). Neither chart
emits a 9 from a single letter, so no special handling is required.

## Decisions

- **Default system:** Chaldean.
- **State:** session-only React component state (no localStorage / URL persistence).
- **Scope:** name page only. The phone page derives mulank/bhagyank from DOB
  digits and is independent of the letter chart, so it is untouched.

## Changes

### `web/lib/numerology.ts`
- Add `export type NumerologySystem = "vedic" | "chaldean"`.
- Keep the existing table as `VEDIC_LETTER_VALUES`; add `CHALDEAN_LETTER_VALUES`
  (identical except C=3, X=5).
- Add `SYSTEM_LETTER_VALUES: Record<NumerologySystem, Record<string, number>>`.
- `letterBreakdown(name, system = "vedic")` and `nameNumber(name, system = "vedic")`
  gain a `system` parameter (defaulted to keep the signature backward-compatible;
  `NameCalculator` is the only caller today).
- Keep `LETTER_VALUES` as an alias of `VEDIC_LETTER_VALUES` for back-compat.

### `web/components/NameCalculator.tsx`
- `useState<NumerologySystem>("chaldean")`.
- Segmented toggle bar at the top of the card (two pills: *Vedic* / *Chaldean*),
  styled in the existing warm palette (`#FDF8F1` surface, `#B05818` active).
- `useMemo` recompute keyed on `system` so totals, root, per-word, and per-letter
  values update live on toggle.

### `web/app/name/page.tsx`
- Make the metadata `description` system-neutral (drop the hardcoded "Vedic").

## Testing

- Extend `web/lib/numerology` with a small self-test (tsx, matching
  `patterns.test.ts` style) asserting:
  - "ABC" → Vedic total 5 (1+2+2), Chaldean total 6 (1+2+3).
  - A name with X differs by system; a name with neither C nor X is identical.

## Out of scope

- Persistence of the selected system across reloads.
- Any change to phone search or the Python tools.
