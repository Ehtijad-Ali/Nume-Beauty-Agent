import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import {
  Sparkles,
  Send,
  Plus,
  Trash2,
  Loader2,
  MessageSquare,
  Bug,
  FileText,
  Timer,
  Coins,
  Bot,
  BookOpen,
  Layers,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/components/common/EmptyState";
import {
  useRagConfig,
  useRagConversations,
  useRagMessages,
  useRagMessageDebug,
  useRagQuery,
  useRagStats,
  useDeleteRagConversation,
} from "@/hooks/useApi";
import { normalizeError } from "@/api";
import { formatDate } from "@/lib/utils";
import type { RagChatMessage, RagSource } from "@/types";

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function formatMs(ms?: number | null): string {
  if (ms == null) return "—";
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`;
}

// --------------------------------------------------------------------------- //
// Stat chips (admin: token usage + response time)
// --------------------------------------------------------------------------- //
function StatChips() {
  const { data: stats } = useRagStats();
  const { data: config } = useRagConfig();
  const chips = [
    { icon: <MessageSquare className="h-3.5 w-3.5" />, label: "Queries", value: stats ? String(stats.queryCount) : "—" },
    { icon: <Coins className="h-3.5 w-3.5" />, label: "Tokens", value: stats ? formatTokens(stats.totalTokens) : "—" },
    { icon: <Timer className="h-3.5 w-3.5" />, label: "Avg response", value: stats ? formatMs(stats.avgTotalMs) : "—" },
    {
      icon: <Bot className="h-3.5 w-3.5" />,
      label: "Model",
      value: config ? `${config.llmProvider} · ${config.llmModel}` : "—",
    },
  ];
  return (
    <div className="flex flex-wrap gap-2">
      {chips.map((c) => (
        <Badge key={c.label} variant="outline" className="gap-1.5 px-2.5 py-1 font-normal">
          {c.icon}
          <span className="text-muted-foreground">{c.label}:</span> {c.value}
        </Badge>
      ))}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Debug dialog (admin: retrieved chunks, sources, prompt debugger, usage)
// --------------------------------------------------------------------------- //
function DebugDialog({ messageId, onClose }: { messageId: string | null; onClose: () => void }) {
  const { data: debug, isLoading } = useRagMessageDebug(messageId);
  return (
    <Dialog open={!!messageId} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bug className="h-4 w-4" /> Response inspector
          </DialogTitle>
          <DialogDescription>
            Exactly what the RAG engine retrieved and sent to the model for this answer.
          </DialogDescription>
        </DialogHeader>
        {isLoading || !debug ? (
          <div className="space-y-2">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : (
          <Tabs defaultValue="chunks">
            <TabsList>
              <TabsTrigger value="chunks">Retrieved chunks ({debug.retrievedChunks.length})</TabsTrigger>
              <TabsTrigger value="sources">Sources ({debug.sources.length})</TabsTrigger>
              <TabsTrigger value="prompt">Final prompt</TabsTrigger>
              <TabsTrigger value="usage">Usage</TabsTrigger>
            </TabsList>

            <TabsContent value="chunks" className="max-h-[55vh] space-y-3 overflow-y-auto pr-1">
              {debug.retrievedChunks.length === 0 && (
                <p className="text-sm text-muted-foreground">No chunks were retrieved for this turn.</p>
              )}
              {debug.retrievedChunks.map((c) => (
                <div key={c.chunkId} className="rounded-lg border p-3">
                  <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
                    {c.citation && <Badge variant="secondary">[{c.citation}]</Badge>}
                    <span className="font-medium">{c.title ?? "Untitled"}</span>
                    {c.page && <span className="text-muted-foreground">p.{c.page}</span>}
                    {c.categoryName && <Badge variant="outline">{c.categoryName}</Badge>}
                    {c.priority && (
                      <Badge variant="success" className="gap-1">
                        <Sparkles className="h-3 w-3" /> priority
                      </Badge>
                    )}
                    <span className="ml-auto text-muted-foreground">
                      score {c.score.toFixed(3)}
                      {c.rankScore != null && c.rankScore !== c.score && ` → rank ${c.rankScore.toFixed(3)}`}
                    </span>
                  </div>
                  <p className="line-clamp-4 whitespace-pre-wrap text-xs text-muted-foreground">{c.content}</p>
                </div>
              ))}
            </TabsContent>

            <TabsContent value="sources" className="max-h-[55vh] space-y-2 overflow-y-auto pr-1">
              {debug.sources.length === 0 && (
                <p className="text-sm text-muted-foreground">No sources were cited for this turn.</p>
              )}
              {debug.sources.map((s) => (
                <div key={s.documentId} className="flex items-center gap-3 rounded-lg border p-3 text-sm">
                  <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{s.title ?? "Untitled document"}</p>
                    <p className="text-xs text-muted-foreground">
                      {s.categoryName ?? "Uncategorised"} · {s.chunksUsed} chunk{s.chunksUsed === 1 ? "" : "s"} · best score{" "}
                      {s.bestScore.toFixed(3)}
                    </p>
                  </div>
                  <div className="flex gap-1">
                    {s.citations.map((n) => (
                      <Badge key={n} variant="secondary">[{n}]</Badge>
                    ))}
                  </div>
                </div>
              ))}
            </TabsContent>

            <TabsContent value="prompt" className="max-h-[55vh] space-y-3 overflow-y-auto pr-1">
              <div>
                <p className="mb-1 text-xs font-semibold uppercase text-muted-foreground">System prompt</p>
                <pre className="whitespace-pre-wrap rounded-lg bg-muted p-3 text-xs">{debug.finalPrompt.system}</pre>
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold uppercase text-muted-foreground">Messages</p>
                <div className="space-y-2">
                  {debug.finalPrompt.messages.map((m, i) => (
                    <div key={i} className="rounded-lg border p-2 text-xs">
                      <Badge variant={m.role === "user" ? "secondary" : "outline"} className="mb-1">
                        {m.role}
                      </Badge>
                      <p className="whitespace-pre-wrap">{m.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="usage">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {[
                  { label: "Provider / model", value: `${debug.provider}${debug.model ? ` · ${debug.model}` : ""}` },
                  { label: "Input tokens", value: formatTokens(debug.usage.inputTokens) },
                  { label: "Output tokens", value: formatTokens(debug.usage.outputTokens) },
                  { label: "Retrieval time", value: formatMs(debug.timings.retrievalMs) },
                  { label: "LLM time", value: formatMs(debug.timings.llmMs) },
                  { label: "Total time", value: formatMs(debug.timings.totalMs) },
                ].map((item) => (
                  <div key={item.label} className="rounded-lg border p-3">
                    <p className="text-xs text-muted-foreground">{item.label}</p>
                    <p className="mt-1 text-sm font-semibold">{item.value}</p>
                  </div>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}

// --------------------------------------------------------------------------- //
// Chat message bubble
// --------------------------------------------------------------------------- //
function SourceBadges({ sources }: { sources?: RagSource[] | null }) {
  if (!sources?.length) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {sources.map((s) => (
        <Badge key={s.documentId} variant="outline" className="gap-1 font-normal">
          <BookOpen className="h-3 w-3" />
          {s.title ?? "Untitled"} {s.citations.map((n) => `[${n}]`).join("")}
        </Badge>
      ))}
    </div>
  );
}

function MessageBubble({ message, onInspect }: { message: RagChatMessage; onInspect: (id: string) => void }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
          isUser ? "bg-primary text-primary-foreground" : "bg-muted"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {!isUser && (
          <>
            <SourceBadges sources={message.sources} />
            <div className="mt-2 flex items-center gap-3 text-[11px] text-muted-foreground">
              {message.model && <span>{message.model}</span>}
              {message.totalMs != null && <span>{formatMs(message.totalMs)}</span>}
              {(message.inputTokens > 0 || message.outputTokens > 0) && (
                <span>{formatTokens(message.inputTokens + message.outputTokens)} tokens</span>
              )}
              <button
                className="inline-flex items-center gap-1 underline-offset-2 hover:underline"
                onClick={() => onInspect(message.id)}
              >
                <Bug className="h-3 w-3" /> Inspect
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Page
// --------------------------------------------------------------------------- //
export default function Assistant() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [allowGeneral, setAllowGeneral] = useState(false);
  const [inspectId, setInspectId] = useState<string | null>(null);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: conversations, isLoading: loadingConversations } = useRagConversations();
  const { data: messages, isLoading: loadingMessages } = useRagMessages(conversationId);
  const queryMut = useRagQuery();
  const deleteMut = useDeleteRagConversation();

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pendingQuestion]);

  const send = () => {
    const message = draft.trim();
    if (!message || queryMut.isPending) return;
    setDraft("");
    setPendingQuestion(message);
    queryMut.mutate(
      {
        message,
        conversationId: conversationId ?? undefined,
        allowGeneralKnowledge: allowGeneral || undefined,
      },
      {
        onSuccess: (data) => {
          setConversationId(data.conversationId);
          setPendingQuestion(null);
        },
        onError: (err) => {
          setPendingQuestion(null);
          setDraft(message);
          toast.error(normalizeError(err).message);
        },
      }
    );
  };

  const removeConversation = (id: string) => {
    deleteMut.mutate(id, {
      onSuccess: () => {
        if (conversationId === id) setConversationId(null);
        toast.success("Conversation deleted");
      },
      onError: (err) => toast.error(normalizeError(err).message),
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Assistant"
        description="Ask questions grounded in your knowledge base — every answer cites its sources."
      />
      <StatChips />

      <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
        {/* Conversations */}
        <Card className="h-[calc(100vh-16rem)] overflow-hidden">
          <CardContent className="flex h-full flex-col gap-2 p-3">
            <Button variant="outline" size="sm" className="justify-start gap-2" onClick={() => setConversationId(null)}>
              <Plus className="h-4 w-4" /> New chat
            </Button>
            <div className="flex-1 space-y-1 overflow-y-auto">
              {loadingConversations && (
                <div className="space-y-2 p-1">
                  <Skeleton className="h-9 w-full" />
                  <Skeleton className="h-9 w-full" />
                </div>
              )}
              {conversations?.map((c) => (
                <div
                  key={c.id}
                  className={`group flex cursor-pointer items-center gap-2 rounded-lg px-2.5 py-2 text-sm transition-colors hover:bg-muted ${
                    c.id === conversationId ? "bg-muted font-medium" : ""
                  }`}
                  onClick={() => setConversationId(c.id)}
                >
                  <MessageSquare className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                  <span className="min-w-0 flex-1 truncate" title={c.title}>
                    {c.title}
                  </span>
                  <button
                    className="hidden shrink-0 text-muted-foreground hover:text-destructive group-hover:block"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeConversation(c.id);
                    }}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
              {conversations && conversations.length === 0 && !loadingConversations && (
                <p className="p-2 text-xs text-muted-foreground">No conversations yet.</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Chat */}
        <Card className="flex h-[calc(100vh-16rem)] flex-col overflow-hidden">
          <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
            {conversationId && loadingMessages && (
              <div className="space-y-3">
                <Skeleton className="h-16 w-2/3" />
                <Skeleton className="ml-auto h-10 w-1/2" />
              </div>
            )}
            {!conversationId && !pendingQuestion && (
              <EmptyState
                icon={<Sparkles className="h-8 w-8" />}
                title="Ask the knowledge base"
                description="Answers are retrieved from your uploaded documents — brand guidelines, product catalogue and personas take priority."
              />
            )}
            {messages?.map((m) => (
              <MessageBubble key={m.id} message={m} onInspect={setInspectId} />
            ))}
            {pendingQuestion && (
              <>
                <div className="flex justify-end">
                  <div className="max-w-[85%] rounded-2xl bg-primary px-4 py-3 text-sm text-primary-foreground">
                    <p className="whitespace-pre-wrap">{pendingQuestion}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Retrieving context and generating…
                </div>
              </>
            )}
          </div>

          {/* Composer */}
          <div className="border-t p-3">
            <div className="flex items-end gap-2">
              <Textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                placeholder="Ask about your brand, products, personas…"
                rows={2}
                className="min-h-[44px] resize-none"
              />
              <Button onClick={send} disabled={!draft.trim() || queryMut.isPending} className="shrink-0">
                {queryMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>
            <div className="mt-2 flex items-center gap-2">
              <Switch id="allow-general" checked={allowGeneral} onCheckedChange={setAllowGeneral} />
              <Label htmlFor="allow-general" className="text-xs font-normal text-muted-foreground">
                Allow general knowledge when nothing relevant is found
              </Label>
              <span className="ml-auto flex items-center gap-1 text-[11px] text-muted-foreground">
                <Layers className="h-3 w-3" /> Grounded on the knowledge base
              </span>
            </div>
          </div>
        </Card>
      </div>

      <DebugDialog messageId={inspectId} onClose={() => setInspectId(null)} />
    </div>
  );
}
