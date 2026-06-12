// Self-test for lib/numerology.ts. Runnable via:
//   npx --yes tsx@latest lib/numerology.test.ts

import { nameNumber, letterBreakdown } from "./numerology";

let failures = 0;
function assertEq<T>(actual: T, expected: T, msg: string): void {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (!ok) {
    failures++;
    console.error(
      `FAIL: ${msg}\n  expected: ${JSON.stringify(expected)}\n  actual:   ${JSON.stringify(actual)}`
    );
  } else {
    console.log("ok   ", msg);
  }
}

// C differs: Vedic 2, Chaldean 3. "ABC" = 1 + 2 + {2|3}.
assertEq(nameNumber("ABC", "vedic").total, 5, "ABC vedic total");
assertEq(nameNumber("ABC", "chaldean").total, 6, "ABC chaldean total");

// X differs: Vedic 6, Chaldean 5.
assertEq(letterBreakdown("X", "vedic")[0].value, 6, "X vedic value");
assertEq(letterBreakdown("X", "chaldean")[0].value, 5, "X chaldean value");

// A name with neither C nor X is identical across systems.
assertEq(
  nameNumber("SHREY", "vedic").total,
  nameNumber("SHREY", "chaldean").total,
  "SHREY identical across systems"
);

// Default system is vedic (back-compat).
assertEq(nameNumber("ABC").total, 5, "ABC default == vedic");

// Root reduction still applies.
assertEq(nameNumber("ABC", "chaldean").root, 6, "ABC chaldean root");

if (failures > 0) {
  console.error(`\n${failures} test(s) failed.`);
  process.exit(1);
}
console.log("\nAll numerology tests passed.");
