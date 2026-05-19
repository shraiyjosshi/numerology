import Link from "next/link";
import { StudioPage, StudioPageHeader } from "@/components/StudioPage";
import { NAV_GROUPS } from "@/lib/nav";

const TOOL_DESCRIPTIONS: Record<string, string> = {
  "/name": "Reduce a name to its single-digit root.",
  "/phone": "Search numbers aligned to your roots.",
};

export default function Home() {
  const calculate = NAV_GROUPS.find((g) => g.label === "Calculate")!.items.filter((i) => !i.soon);

  return (
    <StudioPage>
      <StudioPageHeader title="Numerology" />

      <section>
        <h2 className="font-serif text-xl text-[#2A2A2A] mb-3">Calculate</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
          {calculate.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="studio-tile"
              data-soon={item.soon ? "true" : undefined}
            >
              {item.soon && <span className="studio-tile-soon">Soon</span>}
              <span className="studio-tile-title">{item.label}</span>
              <span className="studio-tile-desc">
                {TOOL_DESCRIPTIONS[item.href] ?? ""}
              </span>
            </Link>
          ))}
        </div>
      </section>

      <footer className="mt-16 pt-6 border-t border-[var(--color-rule)] text-sm text-[#6B6B6B]">
        Built with love by{" "}
        <a
          href="https://shreyjoshi.com"
          target="_blank"
          rel="noreferrer noopener"
          className="text-[#B05818] hover:text-[#8B2C2C] underline underline-offset-4"
        >
          Shrey Joshi
        </a>
        .
      </footer>
    </StudioPage>
  );
}
