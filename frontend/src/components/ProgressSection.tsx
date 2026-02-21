interface ProgressSectionProps {
  title: string;
  total: number;
  percent: number;
  done: number;
  pending: number;
  errors: number;
}

export default function ProgressSection({
  title,
  total,
  percent,
  done,
  pending,
  errors,
}: ProgressSectionProps) {
  return (
    <section className="rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-soft">
      <div className="flex items-center justify-between w-full">
        {/* Left: Progress bar */}
        <div className="flex-grow pr-12">
          <div className="flex items-baseline justify-between mb-2">
            <div className="flex items-baseline gap-3">
              <h3 className="text-lg font-bold text-text-main">{title}</h3>
              <span className="text-sm font-medium text-text-muted">
                {total.toLocaleString()} strings total
              </span>
            </div>
            <span className="text-3xl font-bold text-primary">{percent}%</span>
          </div>
          <div className="relative w-full overflow-hidden rounded-full bg-slate-100 h-4">
            <div
              className="absolute top-0 left-0 h-full bg-primary rounded-full transition-all duration-500"
              style={{ width: `${percent}%` }}
            />
          </div>
        </div>

        {/* Divider */}
        <div className="h-16 w-px bg-border-subtle" />

        {/* Right: Stats */}
        <div className="flex items-center gap-12 pl-12 shrink-0">
          <div className="flex flex-col items-start">
            <span className="text-2xl font-bold text-text-main">
              {done.toLocaleString()}
            </span>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Done
              </span>
            </div>
          </div>
          <div className="flex flex-col items-start">
            <span className="text-2xl font-bold text-amber-500">
              {pending.toLocaleString()}
            </span>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Pending
              </span>
            </div>
          </div>
          <div className="flex flex-col items-start">
            <span className="text-2xl font-bold text-rose-500">
              {errors.toLocaleString()}
            </span>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Errors
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
