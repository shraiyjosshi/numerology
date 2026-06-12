import NameCalculator from "@/components/NameCalculator";
import { StudioPage, StudioPageHeader } from "@/components/StudioPage";

export const metadata = {
  title: "Name — Numerology",
  description: "Compute the Vedic or Chaldean numerological value of a name, with the per-letter breakdown.",
};

export default function NamePage() {
  return (
    <StudioPage>
      <StudioPageHeader eyebrow="Calculate" title="Name" />
      <div className="bg-white border border-[var(--color-rule)] rounded-2xl p-4 sm:p-6 lg:p-7 max-w-3xl">
        <NameCalculator />
      </div>
    </StudioPage>
  );
}
