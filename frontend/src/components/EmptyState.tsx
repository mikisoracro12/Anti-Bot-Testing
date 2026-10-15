import { Inbox } from "lucide-react";
import type { ReactNode } from "react";

interface Props {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: Props) {
  return (
    <div className="flex min-h-[160px] flex-col items-center justify-center gap-2 p-8 text-center">
      <Inbox className="mb-1 h-8 w-8 text-slate-600" aria-hidden />
      <h3 className="text-sm font-medium text-slate-200">{title}</h3>
      {description && <p className="max-w-sm text-sm text-slate-500">{description}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
