const styles: Record<string, string> = {
  allowed: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  normal: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  blocked: "bg-red-500/15 text-red-300 border-red-500/30",
  rate_limited: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  captcha_failed: "bg-red-500/15 text-red-300 border-red-500/30",
  captcha_required: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  suspicious: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  high_risk: "bg-red-500/15 text-red-300 border-red-500/30",
  passed: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  failed: "bg-red-500/15 text-red-300 border-red-500/30",
  missing: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  not_required: "bg-slate-500/15 text-slate-300 border-slate-500/30",
  error: "bg-red-500/15 text-red-300 border-red-500/30",
};

interface Props {
  value: string | null | undefined;
}

export function StatusBadge({ value }: Props) {
  if (!value) return <span className="text-slate-500">—</span>;
  const cls = styles[value] ?? "bg-slate-500/15 text-slate-300 border-slate-500/30";
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 font-mono text-xs ${cls}`}
    >
      {value.replace(/_/g, " ")}
    </span>
  );
}
