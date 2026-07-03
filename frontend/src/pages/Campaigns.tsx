import { motion } from "framer-motion";
import { Plus, Megaphone, Mail, Search, Share2, Monitor, Link2, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Cell } from "recharts";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { StatusBadge } from "@/components/common/StatusBadge";
import { useCampaigns } from "@/hooks/useApi";
import { cn, formatCurrency, formatNumber, formatCompact } from "@/lib/utils";
import type { Campaign } from "@/types";

const CHANNEL_ICON: Record<Campaign["channel"], React.ReactNode> = {
  Email: <Mail className="h-4 w-4" />,
  Social: <Share2 className="h-4 w-4" />,
  Search: <Search className="h-4 w-4" />,
  Display: <Monitor className="h-4 w-4" />,
  Affiliate: <Link2 className="h-4 w-4" />,
};

export default function Campaigns() {
  const { data, isLoading } = useCampaigns();
  const campaigns = data || [];

  const totals = campaigns.reduce(
    (acc, c) => {
      acc.budget += c.budget;
      acc.spent += c.spent;
      acc.impressions += c.impressions;
      acc.clicks += c.clicks;
      acc.conversions += c.conversions;
      return acc;
    },
    { budget: 0, spent: 0, impressions: 0, clicks: 0, conversions: 0 }
  );

  const chartData = campaigns
    .filter((c) => c.status === "active")
    .map((c) => ({ name: c.name.length > 14 ? c.name.slice(0, 14) + "…" : c.name, conversions: c.conversions, color: "hsl(var(--chart-1))" }));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Campaigns"
        description="Plan, launch and monitor your marketing campaigns across channels."
        actions={
          <Button variant="gradient" size="sm">
            <Plus className="h-4 w-4" />
            New Campaign
          </Button>
        }
      />

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Budget", value: formatCurrency(totals.budget), delta: "+8.2%", positive: true },
          { label: "Spent", value: formatCurrency(totals.spent), delta: "+12.4%", positive: false },
          { label: "Impressions", value: formatCompact(totals.impressions), delta: "+18.9%", positive: true },
          { label: "Conversions", value: formatNumber(totals.conversions), delta: "+5.7%", positive: true },
        ].map((s, i) => (
          <Card key={i}>
            <CardContent className="p-5">
              <p className="text-sm text-muted-foreground">{s.label}</p>
              <p className="mt-1 text-2xl font-bold">{s.value}</p>
              <p className={cn("mt-2 inline-flex items-center gap-0.5 text-xs font-semibold", s.positive ? "text-success" : "text-destructive")}>
                {s.positive ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                {s.delta}
                <span className="font-normal text-muted-foreground"> vs last month</span>
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Active Campaign Conversions</CardTitle>
          <CardDescription>Conversion volume by active campaign</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 60, right: 16, top: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
                <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => formatCompact(v as number)} />
                <YAxis dataKey="name" type="category" stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} width={140} />
                <RechartsTooltip
                  cursor={{ fill: "hsl(var(--muted))", opacity: 0.4 }}
                  contentStyle={{ borderRadius: 10, border: "1px solid hsl(var(--border))", background: "hsl(var(--popover))", color: "hsl(var(--popover-foreground))", fontSize: 12 }}
                />
                <Bar dataKey="conversions" radius={[0, 6, 6, 0]} barSize={18}>
                  {chartData.map((_, i) => (
                    <Cell key={i} fill="hsl(var(--chart-1))" />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Campaign cards grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-48 rounded-xl" />)
          : campaigns.length === 0
            ? <EmptyState className="col-span-full" icon={<Megaphone className="h-6 w-6" />} title="No campaigns yet" description="Create your first campaign to start tracking performance." />
            : campaigns.map((c, i) => {
              const util = c.budget ? Math.round((c.spent / c.budget) * 100) : 0;
              const ctr = c.impressions ? (c.clicks / c.impressions) * 100 : 0;
              const cr = c.clicks ? (c.conversions / c.clicks) * 100 : 0;
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
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                          {CHANNEL_ICON[c.channel]}
                        </div>
                        <StatusBadge status={c.status} />
                      </div>
                      <div className="mt-3">
                        <p className="text-sm font-semibold">{c.name}</p>
                        <p className="text-xs text-muted-foreground">{c.channel} channel</p>
                      </div>

                      <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
                        <div>
                          <p className="text-muted-foreground">Impr.</p>
                          <p className="font-semibold">{formatCompact(c.impressions)}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Clicks</p>
                          <p className="font-semibold">{formatCompact(c.clicks)}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Conv.</p>
                          <p className="font-semibold">{formatCompact(c.conversions)}</p>
                        </div>
                      </div>

                      <div className="mt-4 space-y-1.5">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">Budget utilisation</span>
                          <span className="font-medium">{util}%</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                          <div
                            className={cn(
                              "h-full rounded-full",
                              util > 90
                                ? "bg-gradient-to-r from-[hsl(var(--warning))] to-[hsl(var(--destructive))]"
                                : "bg-brand-gradient"
                            )}
                            style={{ width: `${util}%` }}
                          />
                        </div>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>{formatCurrency(c.spent)} spent</span>
                          <span>of {formatCurrency(c.budget)}</span>
                        </div>
                      </div>

                      <div className="mt-4 flex items-center gap-3 border-t border-border pt-3 text-xs">
                        <Badge variant="secondary">CTR {ctr.toFixed(2)}%</Badge>
                        <Badge variant="secondary">CR {cr.toFixed(2)}%</Badge>
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
