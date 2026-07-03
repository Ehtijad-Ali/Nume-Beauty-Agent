import { motion } from "framer-motion";
import {
  Package,
  Megaphone,
  BookOpen,
  UploadCloud,
  HardDrive,
  Activity,
  ArrowUpRight,
  Server,
} from "lucide-react";
import { Link } from "react-router-dom";
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/dashboard/StatCard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useDashboardStats,
  useActivity,
  useSystemStatus,
} from "@/hooks/useApi";
import {
  cn,
  formatCompact,
  formatCurrency,
  formatNumber,
  timeAgo,
} from "@/lib/utils";

const trafficData = [
  { name: "Mon", value: 4200 },
  { name: "Tue", value: 5400 },
  { name: "Wed", value: 4800 },
  { name: "Thu", value: 6200 },
  { name: "Fri", value: 7400 },
  { name: "Sat", value: 6800 },
  { name: "Sun", value: 8200 },
];

const channelData = [
  { name: "Email", value: 3120, color: "hsl(262 83% 58%)" },
  { name: "Social", value: 8910, color: "hsl(199 89% 48%)" },
  { name: "Search", value: 7340, color: "hsl(142 71% 45%)" },
  { name: "Display", value: 1980, color: "hsl(38 92% 50%)" },
  { name: "Affiliate", value: 980, color: "hsl(0 72% 51%)" },
];

const activityIcons: Record<string, React.ReactNode> = {
  upload: <UploadCloud className="h-4 w-4" />,
  campaign: <Megaphone className="h-4 w-4" />,
  product: <Package className="h-4 w-4" />,
  user: <Activity className="h-4 w-4" />,
  review: <Activity className="h-4 w-4" />,
  knowledge: <BookOpen className="h-4 w-4" />,
  system: <Server className="h-4 w-4" />,
};

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: activity, isLoading: activityLoading } = useActivity();
  const { data: system, isLoading: systemLoading } = useSystemStatus();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Your marketing workspace at a glance — products, campaigns, knowledge and system health."
        actions={
          <>
            <Button variant="outline" size="sm">
              Export
            </Button>
            <Button variant="gradient" size="sm">
              <ArrowUpRight className="h-4 w-4" />
              New Campaign
            </Button>
          </>
        }
      />

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statsLoading || !stats ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[136px] rounded-xl" />
          ))
        ) : (
          <>
            <StatCard
              title="Products"
              value={formatNumber(stats.products.total)}
              subtitle={`${stats.products.active} active · ${formatCurrency(stats.products.revenue)} revenue`}
              delta={12.4}
              icon={Package}
              accent="primary"
            />
            <StatCard
              title="Campaigns"
              value={formatNumber(stats.campaigns.total)}
              subtitle={`${stats.campaigns.active} running · ${formatCurrency(stats.campaigns.spent)} spent`}
              delta={8.1}
              icon={Megaphone}
              accent="blue"
            />
            <StatCard
              title="Knowledge Documents"
              value={formatNumber(stats.knowledge.total)}
              subtitle={`${stats.knowledge.ready} ready · ${formatCompact(stats.knowledge.sizeBytes)}B indexed`}
              delta={-2.4}
              icon={BookOpen}
              accent="green"
            />
            <StatCard
              title="Uploads"
              value={formatNumber(stats.uploads.total)}
              subtitle={`${stats.uploads.completed} completed · ${formatCompact(stats.uploads.sizeBytes)}B`}
              delta={18.2}
              icon={UploadCloud}
              accent="amber"
            />
          </>
        )}
      </div>

      {/* Charts row */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-start justify-between space-y-0">
            <div>
              <CardTitle>Traffic Overview</CardTitle>
              <CardDescription>Sessions across all channels this week</CardDescription>
            </div>
            <Badge variant="success" className="gap-1">
              <ArrowUpRight className="h-3 w-3" /> +14.2%
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="h-[260px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trafficData} margin={{ left: -20, right: 8, top: 8, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gradTraffic" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(262 83% 58%)" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="hsl(262 83% 58%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="name"
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v) => formatCompact(v as number)}
                  />
                  <RechartsTooltip
                    contentStyle={{
                      borderRadius: 10,
                      border: "1px solid hsl(var(--border))",
                      background: "hsl(var(--popover))",
                      color: "hsl(var(--popover-foreground))",
                      fontSize: 12,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="hsl(262 83% 58%)"
                    strokeWidth={2.5}
                    fill="url(#gradTraffic)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Conversions by Channel</CardTitle>
            <CardDescription>Last 7 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[260px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={channelData} margin={{ left: -20, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="name"
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v) => formatCompact(v as number)}
                  />
                  <RechartsTooltip
                    cursor={{ fill: "hsl(var(--muted))", opacity: 0.4 }}
                    contentStyle={{
                      borderRadius: 10,
                      border: "1px solid hsl(var(--border))",
                      background: "hsl(var(--popover))",
                      color: "hsl(var(--popover-foreground))",
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                    {channelData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity + System */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Recent Activity */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>What's been happening in your workspace</CardDescription>
            </div>
            <Button variant="ghost" size="sm">
              View all
            </Button>
          </CardHeader>
          <CardContent>
            {activityLoading || !activity ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : (
              <ol className="relative space-y-1">
                {activity.slice(0, 6).map((ev, i) => (
                  <motion.li
                    key={ev.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-start gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-muted/40"
                  >
                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      {activityIcons[ev.type]}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">{ev.title}</p>
                      <p className="truncate text-xs text-muted-foreground">{ev.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] text-muted-foreground">{timeAgo(ev.timestamp)}</p>
                      <p className="text-[10px] font-medium text-muted-foreground">{ev.actor}</p>
                    </div>
                  </motion.li>
                ))}
              </ol>
            )}
          </CardContent>
        </Card>

        {/* System Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>System Status</CardTitle>
              <CardDescription>Live service health</CardDescription>
            </div>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {systemLoading || !system ? (
              <div className="space-y-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : (
              <ul className="space-y-1">
                {system.map((s) => {
                  const ok = s.status === "operational";
                  const warn = s.status === "degraded";
                  return (
                    <li
                      key={s.name}
                      className="flex items-center justify-between rounded-lg px-2 py-2 transition-colors hover:bg-muted/40"
                    >
                      <div className="flex items-center gap-2.5">
                        <span
                          className={cn(
                            "h-2 w-2 rounded-full",
                            ok && "bg-success",
                            warn && "bg-warning",
                            !ok && !warn && "bg-destructive"
                          )}
                        />
                        <span className="text-sm font-medium">{s.name}</span>
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-medium">{s.latency}ms</p>
                        <p className="text-[10px] text-muted-foreground">{s.uptime}% uptime</p>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick links */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { to: "/products", label: "Manage Products", desc: "Catalog & inventory", icon: Package },
          { to: "/campaigns", label: "View Campaigns", desc: "Active & scheduled", icon: Megaphone },
          { to: "/knowledge", label: "Knowledge Base", desc: "Indexed documents", icon: BookOpen },
          { to: "/uploads", label: "Upload Assets", desc: "Drag & drop files", icon: UploadCloud },
        ].map((q) => (
          <Link key={q.to} to={q.to}>
            <Card className="group h-full hover:shadow-elevated hover:border-primary/40">
              <CardContent className="flex items-center gap-3 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                  <q.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold">{q.label}</p>
                  <p className="text-xs text-muted-foreground">{q.desc}</p>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
