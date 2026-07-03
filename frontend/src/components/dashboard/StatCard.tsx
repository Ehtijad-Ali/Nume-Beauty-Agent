import * as React from "react";
import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: React.ReactNode;
  delta?: number;
  deltaLabel?: string;
  icon: LucideIcon;
  accent?: "primary" | "blue" | "green" | "amber" | "rose";
  subtitle?: string;
}

// accents map to theme-aware chart tokens, so no dark: overrides are needed
const ACCENT_CLASS: Record<NonNullable<StatCardProps["accent"]>, string> = {
  primary: "from-[hsl(var(--chart-1)/0.16)] to-[hsl(var(--chart-1)/0.05)] text-[hsl(var(--chart-1))]",
  blue: "from-[hsl(var(--chart-4)/0.16)] to-[hsl(var(--chart-4)/0.05)] text-[hsl(var(--chart-4))]",
  green: "from-[hsl(var(--success)/0.16)] to-[hsl(var(--success)/0.05)] text-success",
  amber: "from-[hsl(var(--chart-5)/0.16)] to-[hsl(var(--chart-5)/0.05)] text-[hsl(var(--chart-5))]",
  rose: "from-[hsl(var(--chart-2)/0.16)] to-[hsl(var(--chart-2)/0.05)] text-[hsl(var(--chart-2))]",
};

export function StatCard({
  title,
  value,
  delta,
  deltaLabel,
  icon: Icon,
  accent = "primary",
  subtitle,
}: StatCardProps) {
  const positive = (delta ?? 0) >= 0;
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
    >
      <Card className="overflow-hidden hover:shadow-elevated">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">{title}</p>
              <p className="text-2xl font-bold tracking-tight">{value}</p>
              {subtitle && (
                <p className="text-xs text-muted-foreground">{subtitle}</p>
              )}
            </div>
            <div
              className={cn(
                "flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br",
                ACCENT_CLASS[accent]
              )}
            >
              <Icon className="h-5 w-5" />
            </div>
          </div>
          {typeof delta === "number" && (
            <div className="mt-4 flex items-center gap-1.5 text-xs">
              <span
                className={cn(
                  "inline-flex items-center gap-0.5 font-semibold",
                  positive ? "text-success" : "text-destructive"
                )}
              >
                {positive ? (
                  <ArrowUpRight className="h-3.5 w-3.5" />
                ) : (
                  <ArrowDownRight className="h-3.5 w-3.5" />
                )}
                {Math.abs(delta)}%
              </span>
              <span className="text-muted-foreground">
                {deltaLabel ?? "vs last month"}
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
