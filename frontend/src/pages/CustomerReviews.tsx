import { useState } from "react";
import { toast } from "sonner";
import { motion } from "framer-motion";
import {
  Star,
  Search,
  MessageSquareReply,
  Flag,
  ThumbsUp,
  Meh,
  ThumbsDown,
  Quote,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { useReviews, useRespondReview } from "@/hooks/useApi";
import { cn, formatDate } from "@/lib/utils";
import type { CustomerReview } from "@/types";

const SENTIMENT_MAP: Record<
  CustomerReview["sentiment"],
  { variant: "success" | "secondary" | "destructive"; label: string; icon: React.ReactNode }
> = {
  positive: { variant: "success", label: "Positive", icon: <ThumbsUp className="h-3 w-3" /> },
  neutral: { variant: "secondary", label: "Neutral", icon: <Meh className="h-3 w-3" /> },
  negative: { variant: "destructive", label: "Negative", icon: <ThumbsDown className="h-3 w-3" /> },
};

const STATUS_MAP: Record<CustomerReview["status"], { variant: "default" | "warning" | "destructive"; label: string }> = {
  new: { variant: "warning", label: "New" },
  responded: { variant: "default", label: "Responded" },
  flagged: { variant: "destructive", label: "Flagged" },
};

function StarRating({ rating, size = "sm" }: { rating: number; size?: "sm" | "md" }) {
  return (
    <div className={cn("flex items-center gap-0.5", size === "md" && "gap-1")}>
      {[1, 2, 3, 4, 5].map((n) => (
        <Star
          key={n}
          className={cn(
            size === "md" ? "h-4 w-4" : "h-3 w-3",
            n <= rating
              ? "fill-[hsl(var(--chart-5))] text-[hsl(var(--chart-5))]"
              : "fill-muted text-muted-foreground/30"
          )}
        />
      ))}
    </div>
  );
}

export default function CustomerReviews() {
  const [search, setSearch] = useState("");
  const [sentiment, setSentiment] = useState("all");
  const [status, setStatus] = useState("all");

  const { data, isLoading } = useReviews({ search, sentiment, status });
  const respondMut = useRespondReview();

  const reviews = data || [];

  const stats = {
    total: reviews.length,
    avg: reviews.length ? reviews.reduce((s, r) => s + r.rating, 0) / reviews.length : 0,
    positive: reviews.filter((r) => r.sentiment === "positive").length,
    negative: reviews.filter((r) => r.sentiment === "negative").length,
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customer Reviews"
        description="Monitor and respond to reviews across all your sales channels."
      />

      {/* Stat row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Reviews", value: stats.total, icon: Star, color: "text-[hsl(var(--chart-5))]" },
          { label: "Average Rating", value: `${stats.avg.toFixed(1)} / 5`, icon: Star, color: "text-[hsl(var(--chart-5))]" },
          { label: "Positive", value: stats.positive, icon: ThumbsUp, color: "text-success" },
          { label: "Needs Attention", value: stats.negative, icon: ThumbsDown, color: "text-destructive" },
        ].map((s, i) => (
          <Card key={i}>
            <CardContent className="flex items-center gap-3 p-4">
              <div className={cn("flex h-10 w-10 items-center justify-center rounded-xl bg-muted", s.color)}>
                <s.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{s.label}</p>
                <p className="text-xl font-bold">{s.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search by title, body, author or product…"
              className="pl-9"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={sentiment} onValueChange={setSentiment}>
            <SelectTrigger className="sm:w-[160px]">
              <SelectValue placeholder="Sentiment" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All sentiments</SelectItem>
              <SelectItem value="positive">Positive</SelectItem>
              <SelectItem value="neutral">Neutral</SelectItem>
              <SelectItem value="negative">Negative</SelectItem>
            </SelectContent>
          </Select>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="sm:w-[160px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="new">New</SelectItem>
              <SelectItem value="responded">Responded</SelectItem>
              <SelectItem value="flagged">Flagged</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Reviews list */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-xl" />
          ))}
        </div>
      ) : reviews.length === 0 ? (
        <EmptyState icon={<Star className="h-6 w-6" />} title="No reviews found" description="Try adjusting your filters." />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {reviews.map((r, i) => (
            <motion.div
              key={r.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <Card className="h-full hover:shadow-elevated">
                <CardContent className="flex h-full flex-col p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-primary/15 to-[hsl(var(--chart-2)/0.15)] text-primary">
                        <Quote className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold">{r.author}</p>
                        <p className="text-xs text-muted-foreground">{r.source} · {formatDate(r.date)}</p>
                      </div>
                    </div>
                    <StarRating rating={r.rating} />
                  </div>

                  <div className="mt-3">
                    <p className="text-sm font-medium">{r.title}</p>
                    <p className="mt-1 line-clamp-3 text-sm text-muted-foreground">{r.body}</p>
                  </div>

                  <div className="mt-3 flex flex-wrap items-center gap-1.5">
                    <Badge variant="outline">{r.product}</Badge>
                    <Badge variant={SENTIMENT_MAP[r.sentiment].variant} className="gap-1">
                      {SENTIMENT_MAP[r.sentiment].icon}
                      {SENTIMENT_MAP[r.sentiment].label}
                    </Badge>
                    <Badge variant={STATUS_MAP[r.status].variant}>{STATUS_MAP[r.status].label}</Badge>
                  </div>

                  <div className="mt-auto flex items-center justify-end gap-2 border-t border-border pt-3">
                    <Button variant="ghost" size="sm" className="text-muted-foreground">
                      <Flag className="h-3.5 w-3.5" />
                      Flag
                    </Button>
                    <Button
                      variant={r.status === "responded" ? "secondary" : "gradient"}
                      size="sm"
                      disabled={r.status === "responded" || respondMut.isPending}
                      onClick={async () => {
                        await respondMut.mutateAsync(r.id);
                        toast.success("Review marked as responded", { description: r.title });
                      }}
                    >
                      <MessageSquareReply className="h-3.5 w-3.5" />
                      {r.status === "responded" ? "Responded" : "Respond"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
