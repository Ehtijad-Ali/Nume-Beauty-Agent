import { Badge } from "@/components/ui/badge";
import type { Status } from "@/types";
import { cn } from "@/lib/utils";

const STATUS_MAP: Record<Status, { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive"; dot: string }> = {
  active: { label: "Active", variant: "success", dot: "bg-success" },
  draft: { label: "Draft", variant: "secondary", dot: "bg-muted-foreground" },
  paused: { label: "Paused", variant: "warning", dot: "bg-warning" },
  archived: { label: "Archived", variant: "secondary", dot: "bg-muted-foreground" },
};

export function StatusBadge({ status, className }: { status: Status; className?: string }) {
  const cfg = STATUS_MAP[status] || STATUS_MAP.draft;
  return (
    <Badge variant={cfg.variant} className={cn("gap-1.5", className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dot)} />
      {cfg.label}
    </Badge>
  );
}
