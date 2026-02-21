import type { AppStep } from "../types";

const STEPS = [
  { label: "1. Load", icon: "edit_document" },
  { label: "2. KR Review", icon: "chat_bubble" },
  { label: "3. Translating", icon: "g_translate" },
  { label: "4. Multi-Review", icon: "rate_review" },
  { label: "5. Complete", icon: "check_circle" },
] as const;

const STEP_ORDER: AppStep[] = [
  "idle",
  "loading",
  "ko_review",
  "translating",
  "final_review",
  "done",
];

/** Map AppStep → STEPS visual index (0–4). "loading" shares index 0 with "idle". */
function stepIndex(step: AppStep): number {
  if (step === "loading") return 0;
  const idx = STEP_ORDER.indexOf(step);
  // skip "loading" in count → subtract 1 for steps after it
  return idx <= 0 ? 0 : idx - 1;
}

export default function StepIndicator({
  currentStep,
}: {
  currentStep: AppStep;
}) {
  const activeIdx = stepIndex(currentStep);

  return (
    <nav aria-label="Progress" className="flex-1 max-w-3xl mx-auto">
      <ol className="flex items-center justify-between w-full" role="list">
        {STEPS.map((step, i) => {
          const isCompleted = i < activeIdx;
          const isCurrent = i === activeIdx;
          const isLast = i === STEPS.length - 1;

          return (
            <li
              key={step.label}
              className="relative flex flex-col items-center group flex-1"
            >
              <div className="flex items-center w-full">
                {/* Left connector line */}
                {i > 0 && (
                  <div
                    className={`hidden sm:block absolute left-[-50%] right-[50%] top-4 h-[2px] -z-0 ${
                      isCompleted || isCurrent ? "bg-primary" : "bg-slate-200"
                    }`}
                  />
                )}

                {/* Step circle */}
                {isCompleted ? (
                  <span className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-white z-10 mx-auto">
                    <span className="material-symbols-outlined text-lg">
                      check
                    </span>
                  </span>
                ) : isCurrent ? (
                  <span className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white border-2 border-primary text-primary z-10 mx-auto shadow-sm shadow-primary/20">
                    <span className="material-symbols-outlined text-lg">
                      {step.icon}
                    </span>
                  </span>
                ) : (
                  <span className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white border border-slate-300 text-slate-400 z-10 mx-auto">
                    <span className="material-symbols-outlined text-lg">
                      {step.icon}
                    </span>
                  </span>
                )}

                {/* Right connector line */}
                {!isLast && (
                  <div
                    className={`hidden sm:block absolute left-[50%] right-[-50%] top-4 h-[2px] -z-0 ${
                      isCompleted ? "bg-primary" : "bg-slate-200"
                    }`}
                  />
                )}
              </div>

              {/* Label */}
              <span
                className={`mt-2 w-full text-center text-xs ${
                  isCompleted
                    ? "font-semibold text-primary"
                    : isCurrent
                      ? "font-bold text-primary"
                      : "font-medium text-text-muted"
                }`}
              >
                {step.label}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
