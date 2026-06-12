"use client";

import { useMemo, useState } from "react";
import { nameNumber, type NumerologySystem } from "@/lib/numerology";

const SYSTEMS: { value: NumerologySystem; label: string }[] = [
  { value: "vedic", label: "Vedic" },
  { value: "chaldean", label: "Chaldean" },
];

export default function NameCalculator() {
  const [name, setName] = useState("");
  const [system, setSystem] = useState<NumerologySystem>("chaldean");

  const result = useMemo(() => {
    const trimmed = name.trim();
    if (!trimmed) return null;
    const words = trimmed.split(/\s+/);
    const full = words.join(" ");
    return {
      full,
      total: nameNumber(full, system),
      perWord: words.map((w) => ({ word: w, ...nameNumber(w, system) })),
    };
  }, [name, system]);

  return (
    <div className="space-y-5 sm:space-y-6">
      <div>
        <span className="eyebrow block mb-2">System</span>
        <div
          role="radiogroup"
          aria-label="Numerology system"
          className="inline-flex w-full sm:w-auto rounded-xl border border-[#EADFCB] bg-[#FDF8F1] p-1"
        >
          {SYSTEMS.map((s) => {
            const active = system === s.value;
            return (
              <button
                key={s.value}
                type="button"
                role="radio"
                aria-checked={active}
                onClick={() => setSystem(s.value)}
                className={
                  "flex-1 sm:flex-none px-4 sm:px-6 py-1.5 rounded-lg text-sm font-medium transition-colors " +
                  (active
                    ? "bg-[#B05818] text-white shadow-sm"
                    : "text-[#6B6B6B] hover:text-[#2A2A2A]")
                }
              >
                {s.label}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <label className="eyebrow block mb-2" htmlFor="name-input">
          Your Name
        </label>
        <input
          id="name-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter a name to compute its number."
          autoComplete="name"
          autoCapitalize="words"
          autoCorrect="off"
          spellCheck={false}
          className="input-aol"
        />
      </div>

      {result ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2.5 sm:gap-3">
            <div className="bg-[#FDF8F1] border border-[#EADFCB] rounded-xl px-3 sm:px-4 py-3 flex items-baseline justify-between gap-2">
              <div className="eyebrow flex items-center">
                Total
              </div>
              <div className="font-serif text-xl sm:text-2xl text-[#2A2A2A] tabular-nums leading-none">
                {result.total.total}
              </div>
            </div>
            <div className="bg-[#FDF8F1] border border-[#EADFCB] rounded-xl px-3 sm:px-4 py-3 flex items-baseline justify-between gap-2">
              <div className="eyebrow flex items-center">
                Root
              </div>
              <div className="font-serif text-xl sm:text-2xl text-[#B05818] tabular-nums leading-none">
                {result.total.root}
              </div>
            </div>
          </div>

          <div className="space-y-3">
            {result.perWord.map((w, i) => {
              return (
                <div
                  key={i}
                  className="bg-[#FDF8F1] border border-[#EADFCB] rounded-2xl p-4 sm:p-5 card-lift"
                >
                  <div className="flex items-baseline justify-between gap-3 mb-3 flex-wrap">
                    <div className="flex items-center gap-2 flex-wrap min-w-0">
                      <div className="font-serif text-lg sm:text-xl text-[#2A2A2A] break-words">
                        {w.word}
                      </div>
                    </div>
                    <div className="flex items-baseline gap-2.5 sm:gap-3 whitespace-nowrap shrink-0">
                      {/* Chaldean reads the compound number as primary; Vedic
                          the reduced root. Swap which one is the large figure. */}
                      <div className="text-xs text-[#6B6B6B] tabular-nums">
                        {system === "chaldean" ? "root" : "sum"}{" "}
                        <span className="text-[#2A2A2A] font-medium">
                          {system === "chaldean" ? w.root : w.total}
                        </span>
                      </div>
                      <div className="font-serif text-2xl sm:text-3xl text-[#B05818] tabular-nums leading-none">
                        {system === "chaldean" ? w.total : w.root}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {w.pairs.map((p, j) => (
                      <div
                        key={j}
                        className="px-2 sm:px-2.5 py-1 bg-white border border-[#EADFCB] rounded-lg text-[0.8rem] sm:text-sm"
                      >
                        <span className="font-mono text-[#2A2A2A]">{p.letter}</span>
                        <span className="text-[#B5A790] mx-1 sm:mx-1.5">·</span>
                        <span className="text-[#B05818] font-semibold tabular-nums">
                          {p.value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}
