import { motion } from "framer-motion";
import { Plus, Globe, TrendingUp, TrendingDown, Swords, ExternalLink } from "lucide-react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip as RechartsTooltip, LineChart, Line } from "recharts";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { useCompetitors } from "@/hooks/useApi";
import { cn, formatCompact, formatNumber } from "@/lib/utils";

const COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
  "hsl(var(--chart-6))",
];

function Sparkline({ data, color }: { data: number[]; color: string }) {
  const d = data.map((v, i) => ({ x: i, y: v }));
  return (
    <ResponsiveContainer width="100%" height={36}>
      <LineChart data={d} margin={{ top: 2, bottom: 2, left: 0, right: 0 }}>
        <Line
          type="monotone"
          dataKey="y"
          stroke={color}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default function Competitors() {
  const { data, isLoading } = useCompetitors();
  const competitors = data || [];

  const pieData = competitors.map((c) => ({ name: c.name, value: c.shareOfVoice }));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Competitors"
        description="Track share-of-voice, traffic and advertising activity across your competitive set."
        actions={
          <Button variant="gradient" size="sm">
            <Plus className="h-4 w-4" />
            Add Competitor
          </Button>
        }
      />

      {/* SoV + summary */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Share of Voice</CardTitle>
            <CardDescription>Distribution across tracked competitors</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[220px] w-full" />
            ) : (
              <div className="relative h-[220px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={2}
                      stroke="hsl(var(--card))"
                      strokeWidth={3}
                    >
                      {pieData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip
                      contentStyle={{
                        borderRadius: 10,
                        border: "1px solid hsl(var(--border))",
                        background: "hsl(var(--popover))",
                        color: "hsl(var(--popover-foreground))",
                        fontSize: 12,
                      }}
                      formatter={(v: number) => [`${v}%`, "Share"]}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                  <p className="text-2xl font-bold">{competitors.length}</p>
                  <p className="text-xs text-muted-foreground">tracked</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Top Movers</CardTitle>
            <CardDescription>Week-over-week share of voice change</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : (
              <ul className="space-y-1">
                {[...competitors]
                  .sort((a, b) => Math.abs(b.change) - Math.abs(a.change))
                  .slice(0, 5)
                  .map((c, i) => {
                    const positive = c.change >= 0;
                    return (
                      <li
                        key={c.id}
                        className="flex items-center justify-between rounded-lg px-3 py-2.5 transition-colors hover:bg-muted/40"
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className="h-2.5 w-2.5 rounded-full"
                            style={{ background: COLORS[i % COLORS.length] }}
                          />
                          <div>
                            <p className="text-sm font-medium">{c.name}</p>
                            <p className="text-xs text-muted-foreground">{c.domain}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <p className="text-sm font-semibold">{c.shareOfVoice}%</p>
                            <p className="text-[10px] text-muted-foreground">SoV</p>
                          </div>
                          <div
                            className={cn(
                              "inline-flex items-center gap-0.5 rounded-md px-2 py-0.5 text-xs font-semibold",
                              positive ? "bg-success/15 text-success" : "bg-destructive/15 text-destructive"
                            )}
                          >
                            {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                            {Math.abs(c.change)}%
                          </div>
                        </div>
                      </li>
                    );
                  })}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Competitor cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-56 rounded-xl" />)
          : competitors.length === 0
            ? <EmptyState className="col-span-full" icon={<Swords className="h-6 w-6" />} title="No competitors tracked" description="Add competitors to start monitoring their share of voice." />
            : competitors.map((c, i) => {
              const positive = c.change >= 0;
              const color = COLORS[i % COLORS.length];
              return (
                <motion.div
                  key={c.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="group h-full hover:shadow-elevated hover:border-primary/40">
                    <CardContent className="flex h-full flex-col p-5">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div
                            className="flex h-10 w-10 items-center justify-center rounded-xl text-white"
                            style={{ background: color }}
                          >
                            <Globe className="h-5 w-5" />
                          </div>
                          <div>
                            <p className="text-sm font-semibold">{c.name}</p>
                            <a
                              href={`https://${c.domain}`}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-0.5 text-xs text-muted-foreground hover:text-primary"
                            >
                              {c.domain}
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          </div>
                        </div>
                        <div
                          className={cn(
                            "inline-flex items-center gap-0.5 rounded-md px-2 py-0.5 text-xs font-semibold",
                            positive ? "bg-success/15 text-success" : "bg-destructive/15 text-destructive"
                          )}
                        >
                          {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                          {Math.abs(c.change)}%
                        </div>
                      </div>

                      <div className="mt-4 h-9">
                        <Sparkline data={c.trend} color={color} />
                      </div>

                      <div className="mt-4 grid grid-cols-3 gap-3 border-t border-border pt-4">
                        <div>
                          <p className="text-xs text-muted-foreground">Traffic</p>
                          <p className="text-sm font-semibold">{formatCompact(c.traffic)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Keywords</p>
                          <p className="text-sm font-semibold">{formatNumber(c.keywords)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Ads</p>
                          <p className="text-sm font-semibold">{formatNumber(c.ads)}</p>
                        </div>
                      </div>

                      <div className="mt-4">
                        <div className="mb-1 flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">Share of Voice</span>
                          <span className="font-semibold">{c.shareOfVoice}%</span>
                        </div>
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${c.shareOfVoice}%`, background: color }}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
      </div>
    </div>
  );
}
