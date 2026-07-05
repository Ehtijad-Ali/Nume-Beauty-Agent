import { useRef, useState } from "react";
import { toast } from "sonner";
import { motion } from "framer-motion";
import {
  Upload,
  Search,
  FileText,
  FileSpreadsheet,
  FileCode,
  File,
  Globe,
  Image as ImageIcon,
  Trash2,
  Eye,
  Download,
  FileBox,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
  RefreshCw,
  RotateCw,
  History,
  Layers,
  Plus,
  Sparkles,
  Database,
  Zap,
  FileSearch,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import {
  useKnowledge,
  useDeleteKnowledge,
  useUploadKnowledge,
  useReplaceKnowledge,
  useReindexKnowledge,
  useKnowledgeChunks,
  useKnowledgeVersions,
  useKnowledgeCategories,
  useCreateKnowledgeCategory,
  useIndexStats,
  useSemanticSearch,
  useDeleteIndex,
} from "@/hooks/useApi";
import { formatDate } from "@/lib/utils";
import { knowledgeService, normalizeError } from "@/api";
import type { KnowledgeDocument, SemanticSearchResult } from "@/types";

const TYPE_ICON: Record<KnowledgeDocument["type"], React.ReactNode> = {
  pdf: <FileText className="h-4 w-4" />,
  docx: <FileText className="h-4 w-4" />,
  xlsx: <FileSpreadsheet className="h-4 w-4" />,
  csv: <FileSpreadsheet className="h-4 w-4" />,
  txt: <File className="h-4 w-4" />,
  md: <FileCode className="h-4 w-4" />,
  url: <Globe className="h-4 w-4" />,
  image: <ImageIcon className="h-4 w-4" />,
};

const STATUS_BADGE: Record<KnowledgeDocument["status"], { variant: "success" | "warning" | "destructive" | "secondary"; label: string; icon: React.ReactNode }> = {
  ready: { variant: "success", label: "Ready", icon: <CheckCircle2 className="h-3 w-3" /> },
  processing: { variant: "warning", label: "Processing", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
  queued: { variant: "secondary", label: "Queued", icon: <Clock className="h-3 w-3" /> },
  failed: { variant: "destructive", label: "Failed", icon: <AlertCircle className="h-3 w-3" /> },
};

const EMBED_BADGE: Record<KnowledgeDocument["embeddingStatus"], { variant: "success" | "warning" | "destructive" | "secondary" | "outline"; label: string; icon: React.ReactNode }> = {
  completed: { variant: "success", label: "Embedded", icon: <CheckCircle2 className="h-3 w-3" /> },
  processing: { variant: "warning", label: "Embedding…", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
  pending: { variant: "secondary", label: "Queued", icon: <Clock className="h-3 w-3" /> },
  failed: { variant: "destructive", label: "Failed", icon: <AlertCircle className="h-3 w-3" /> },
  none: { variant: "outline", label: "Not indexed", icon: <Database className="h-3 w-3" /> },
};

const ACCEPTED = ".pdf,.docx,.txt,.md,.csv,.png,.jpg,.jpeg,.webp,.tiff";

function formatBytes(b: number): string {
  if (!b) return "—";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
}

function CategoryBadge({ doc }: { doc: KnowledgeDocument }) {
  if (!doc.category) return <span className="text-xs text-muted-foreground">—</span>;
  return (
    <Badge variant="outline" className="gap-1.5 font-normal">
      <span
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: doc.category.color || "#6B7280" }}
      />
      {doc.category.name}
    </Badge>
  );
}

// --------------------------------------------------------------------------- //
// Upload dialog
// --------------------------------------------------------------------------- //
function UploadDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [categoryId, setCategoryId] = useState("auto");
  const [brand, setBrand] = useState("");
  const [tags, setTags] = useState("");
  const [progress, setProgress] = useState<number | null>(null);
  const [newCategory, setNewCategory] = useState("");
  const [addingCategory, setAddingCategory] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const { data: categories } = useKnowledgeCategories();
  const uploadMut = useUploadKnowledge();
  const createCategoryMut = useCreateKnowledgeCategory();

  const reset = () => {
    setFile(null);
    setTitle("");
    setCategoryId("auto");
    setBrand("");
    setTags("");
    setProgress(null);
    setNewCategory("");
    setAddingCategory(false);
  };

  const pickFile = (f: File | null) => {
    setFile(f);
    if (f && !title) setTitle(f.name.replace(/\.[^.]+$/, ""));
  };

  const handleCreateCategory = async () => {
    if (!newCategory.trim()) return;
    try {
      const created = await createCategoryMut.mutateAsync({ name: newCategory.trim() });
      setCategoryId(created.id);
      setAddingCategory(false);
      setNewCategory("");
      toast.success("Category created", { description: created.name });
    } catch (err) {
      toast.error("Could not create category", { description: normalizeError(err).message });
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    try {
      setProgress(0);
      const doc = await uploadMut.mutateAsync({
        file,
        title: title.trim() || undefined,
        categoryId: categoryId !== "auto" ? categoryId : undefined,
        brand: brand.trim() || undefined,
        tags: tags.trim() || undefined,
        onProgress: (e) => setProgress(e.percent),
      });
      if (doc.status === "ready") {
        toast.success("Document indexed", {
          description: `${doc.title} — ${doc.chunkCount} chunks extracted`,
        });
      } else {
        toast.warning("Uploaded, but indexing failed", { description: doc.errorMessage || undefined });
      }
      reset();
      onClose();
    } catch (err) {
      setProgress(null);
      toast.error("Upload failed", { description: normalizeError(err).message });
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) { reset(); onClose(); } }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Upload document</DialogTitle>
          <DialogDescription>
            PDF, DOCX, TXT, MD, CSV or images. The file is parsed, cleaned and chunked automatically.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Dropzone */}
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              pickFile(e.dataTransfer.files?.[0] ?? null);
            }}
            className="flex w-full flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border bg-muted/30 p-6 text-center transition-colors hover:border-primary/50 hover:bg-primary/5"
          >
            <Upload className="h-6 w-6 text-muted-foreground" />
            {file ? (
              <div>
                <p className="text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">{formatBytes(file.size)}</p>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Drag & drop a file here, or <span className="text-primary">browse</span>
              </p>
            )}
          </button>
          <input
            ref={fileInput}
            type="file"
            accept={ACCEPTED}
            className="hidden"
            onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
          />

          <div className="space-y-2">
            <Label htmlFor="kb-title">Title</Label>
            <Input id="kb-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Document title" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Category</Label>
              {addingCategory ? (
                <div className="flex gap-2">
                  <Input
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    placeholder="New category"
                    onKeyDown={(e) => e.key === "Enter" && handleCreateCategory()}
                  />
                  <Button size="sm" variant="outline" onClick={handleCreateCategory} disabled={createCategoryMut.isPending}>
                    Add
                  </Button>
                </div>
              ) : (
                <Select
                  value={categoryId}
                  onValueChange={(v) => (v === "__new__" ? setAddingCategory(true) : setCategoryId(v))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Auto-detect</SelectItem>
                    {(categories || []).map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                    ))}
                    <SelectItem value="__new__">
                      <span className="flex items-center gap-1"><Plus className="h-3 w-3" /> New category…</span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="kb-brand">Brand</Label>
              <Input id="kb-brand" value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="e.g. NUMÉ" />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="kb-tags">Tags</Label>
            <Input id="kb-tags" value={tags} onChange={(e) => setTags(e.target.value)} placeholder="comma,separated,tags" />
          </div>

          {progress !== null && (
            <div className="space-y-1">
              <Progress value={progress} />
              <p className="text-xs text-muted-foreground">
                {progress < 100 ? `Uploading… ${progress}%` : "Processing document…"}
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => { reset(); onClose(); }}>Cancel</Button>
          <Button variant="gradient" onClick={handleUpload} disabled={!file || uploadMut.isPending}>
            {uploadMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            Upload & index
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// --------------------------------------------------------------------------- //
// Replace dialog
// --------------------------------------------------------------------------- //
function ReplaceDialog({ doc, onClose }: { doc: KnowledgeDocument | null; onClose: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [changeNote, setChangeNote] = useState("");
  const [progress, setProgress] = useState<number | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const replaceMut = useReplaceKnowledge();

  const reset = () => { setFile(null); setChangeNote(""); setProgress(null); };

  const handleReplace = async () => {
    if (!doc || !file) return;
    try {
      setProgress(0);
      const updated = await replaceMut.mutateAsync({
        id: doc.id,
        file,
        changeNote: changeNote.trim() || undefined,
        onProgress: (e) => setProgress(e.percent),
      });
      if (updated.status === "ready") {
        toast.success(`New version v${updated.version} indexed`, { description: updated.title });
      } else {
        toast.warning("Replaced, but indexing failed", { description: updated.errorMessage || undefined });
      }
      reset();
      onClose();
    } catch (err) {
      setProgress(null);
      toast.error("Replace failed", { description: normalizeError(err).message });
    }
  };

  return (
    <Dialog open={!!doc} onOpenChange={(o) => { if (!o) { reset(); onClose(); } }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Replace document</DialogTitle>
          <DialogDescription>
            Upload a new file for <span className="font-semibold text-foreground">{doc?.title}</span>.
            The current version (v{doc?.version}) is kept in history.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); setFile(e.dataTransfer.files?.[0] ?? null); }}
            className="flex w-full flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border bg-muted/30 p-5 text-center transition-colors hover:border-primary/50 hover:bg-primary/5"
          >
            <RefreshCw className="h-5 w-5 text-muted-foreground" />
            {file ? (
              <div>
                <p className="text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">{formatBytes(file.size)}</p>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Choose the replacement file</p>
            )}
          </button>
          <input
            ref={fileInput}
            type="file"
            accept={ACCEPTED}
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <div className="space-y-2">
            <Label htmlFor="kb-note">Change note</Label>
            <Input id="kb-note" value={changeNote} onChange={(e) => setChangeNote(e.target.value)} placeholder="What changed?" />
          </div>
          {progress !== null && <Progress value={progress} />}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => { reset(); onClose(); }}>Cancel</Button>
          <Button variant="gradient" onClick={handleReplace} disabled={!file || replaceMut.isPending}>
            {replaceMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Replace & re-index
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// --------------------------------------------------------------------------- //
// Preview dialog (metadata / chunks / versions)
// --------------------------------------------------------------------------- //
function MetaItem({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <div className="mt-0.5 text-sm font-medium">{value ?? "—"}</div>
    </div>
  );
}

function PreviewDialog({ doc, onClose }: { doc: KnowledgeDocument | null; onClose: () => void }) {
  const { data: chunks, isLoading: chunksLoading } = useKnowledgeChunks(doc?.id ?? null);
  const { data: versions, isLoading: versionsLoading } = useKnowledgeVersions(doc?.id ?? null);

  if (!doc) return null;
  const badge = STATUS_BADGE[doc.status];

  return (
    <Dialog open={!!doc} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-h-[85vh] max-w-3xl overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
              {TYPE_ICON[doc.type] ?? <File className="h-4 w-4" />}
            </div>
            <div className="min-w-0 flex-1">
              <DialogTitle className="break-words">{doc.title}</DialogTitle>
              <DialogDescription>
                {doc.type.toUpperCase()} · v{doc.version} · {formatBytes(doc.size)} · uploaded by {doc.uploadedBy} on {formatDate(doc.uploadedAt)}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <Tabs defaultValue="overview">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="chunks" className="gap-1">
              <Layers className="h-3.5 w-3.5" /> Chunks ({doc.chunkCount})
            </TabsTrigger>
            <TabsTrigger value="versions" className="gap-1">
              <History className="h-3.5 w-3.5" /> Versions
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4 pt-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={badge.variant} className="gap-1">{badge.icon}{badge.label}</Badge>
              <CategoryBadge doc={doc} />
              {doc.brand && <Badge variant="outline">{doc.brand}</Badge>}
              {doc.tags.map((t) => (
                <Badge key={t} variant="secondary">#{t}</Badge>
              ))}
            </div>

            {doc.status === "failed" && doc.errorMessage && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                {doc.errorMessage}
              </div>
            )}

            <div className="rounded-lg border border-border bg-muted/30 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Excerpt</p>
              <p className="mt-2 text-sm leading-relaxed">
                {doc.excerpt || "No preview available for this document."}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <MetaItem label="File" value={doc.originalFilename} />
              <MetaItem label="Version" value={`v${doc.version}`} />
              <MetaItem label="Size" value={formatBytes(doc.size)} />
              <MetaItem label="Pages" value={doc.pageCount ?? "—"} />
              <MetaItem label="Words" value={doc.wordCount?.toLocaleString() ?? "—"} />
              <MetaItem label="Chunks" value={doc.chunkCount} />
              <MetaItem label="Uploaded by" value={doc.uploadedBy} />
              <MetaItem label="Uploaded" value={formatDate(doc.uploadedAt)} />
              <MetaItem
                label="Last indexed"
                value={doc.lastIndexedAt ? formatDate(doc.lastIndexedAt, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) : "Never"}
              />
              <MetaItem
                label="Vectors"
                value={
                  <span className="flex items-center gap-1.5">
                    {EMBED_BADGE[doc.embeddingStatus].icon}
                    {doc.embeddingStatus === "completed" ? doc.vectorCount : EMBED_BADGE[doc.embeddingStatus].label}
                  </span>
                }
              />
              <MetaItem
                label="Embedded"
                value={doc.embeddedAt ? formatDate(doc.embeddedAt, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) : "Never"}
              />
              <MetaItem label="Embedding model" value={doc.embeddingModel ?? "—"} />
            </div>

            {doc.embeddingStatus === "failed" && doc.embeddingError && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                Embedding failed: {doc.embeddingError}
              </div>
            )}

            {doc.metadata && Object.keys(doc.metadata).length > 0 && (
              <div className="rounded-lg border border-border p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Extracted metadata
                </p>
                <dl className="mt-2 space-y-1 text-sm">
                  {Object.entries(doc.metadata).map(([k, v]) => (
                    <div key={k} className="flex gap-2">
                      <dt className="shrink-0 font-medium capitalize text-muted-foreground">{k.replace(/_/g, " ")}:</dt>
                      <dd className="break-all">{Array.isArray(v) ? v.join(", ") : String(v)}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}
          </TabsContent>

          <TabsContent value="chunks" className="pt-4">
            {chunksLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-20 w-full" />)}
              </div>
            ) : !chunks || chunks.items.length === 0 ? (
              <EmptyState
                icon={<Layers className="h-6 w-6" />}
                title="No chunks"
                description="This document has not been indexed yet, or indexing failed."
              />
            ) : (
              <div className="max-h-[45vh] space-y-2 overflow-y-auto pr-1">
                {chunks.items.map((c) => (
                  <div key={c.id} className="rounded-lg border border-border p-3">
                    <div className="mb-1 flex items-center justify-between">
                      <Badge variant="outline">Chunk {c.index + 1}</Badge>
                      <span className="text-xs text-muted-foreground">
                        {c.wordCount} words · {c.charCount} chars
                      </span>
                    </div>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                      {c.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="versions" className="pt-4">
            {versionsLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
              </div>
            ) : !versions || versions.length === 0 ? (
              <EmptyState
                icon={<History className="h-6 w-6" />}
                title="No version history"
                description="This document was created without a stored file."
              />
            ) : (
              <div className="space-y-2">
                {versions.map((v) => (
                  <div key={v.id} className="flex items-center justify-between rounded-lg border border-border p-3">
                    <div className="flex items-center gap-3">
                      <Badge variant={v.version === doc.version ? "success" : "secondary"}>v{v.version}</Badge>
                      <div>
                        <p className="text-sm font-medium">{v.originalFilename || "file"}</p>
                        <p className="text-xs text-muted-foreground">
                          {v.changeNote || "—"}{v.uploadedBy ? ` · ${v.uploadedBy}` : ""}
                        </p>
                      </div>
                    </div>
                    <div className="text-right text-xs text-muted-foreground">
                      <p>{formatBytes(v.fileSize)}</p>
                      <p>{formatDate(v.createdAt)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => knowledgeService.download(doc.id, doc.originalFilename || doc.title).catch(() => toast.error("Download failed"))}
          >
            <Download className="h-4 w-4" />
            Download
          </Button>
          <Button variant="gradient" onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// --------------------------------------------------------------------------- //
// Index stats bar
// --------------------------------------------------------------------------- //
function IndexStatCard({ icon, label, value, hint }: { icon: React.ReactNode; label: string; value: React.ReactNode; hint?: string }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
          {icon}
        </div>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="truncate text-lg font-semibold leading-tight">{value}</p>
          {hint && <p className="truncate text-xs text-muted-foreground">{hint}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

function IndexStatsBar() {
  const { data: stats } = useIndexStats();
  const deleteIndexMut = useDeleteIndex();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const confirmDeleteIndex = async () => {
    try {
      await deleteIndexMut.mutateAsync();
      toast.success("Vector index deleted", {
        description: "Documents and chunks are untouched — re-index to rebuild.",
      });
      setConfirmOpen(false);
    } catch (err) {
      toast.error("Could not delete index", { description: normalizeError(err).message });
    }
  };

  const embedded = stats?.documentsByStatus?.completed ?? 0;

  return (
    <>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <IndexStatCard
          icon={<FileBox className="h-4 w-4" />}
          label="Documents embedded"
          value={`${embedded} / ${stats?.documentCount ?? 0}`}
        />
        <IndexStatCard
          icon={<Layers className="h-4 w-4" />}
          label="Chunks"
          value={stats?.chunkCount?.toLocaleString() ?? "—"}
        />
        <IndexStatCard
          icon={<Database className="h-4 w-4" />}
          label="Vectors"
          value={stats?.vectorCount?.toLocaleString() ?? "—"}
          hint={stats ? `${stats.embeddingDimension} dims` : undefined}
        />
        <IndexStatCard
          icon={<Zap className="h-4 w-4" />}
          label="Index status"
          value={<span className="capitalize">{stats?.indexStatus?.replace("_", " ") ?? "—"}</span>}
          hint={stats?.embeddingModel}
        />
        <Card className="border-dashed">
          <CardContent className="flex h-full items-center justify-center p-4">
            <Button
              variant="outline"
              size="sm"
              className="text-muted-foreground hover:border-destructive/40 hover:bg-destructive/10 hover:text-destructive"
              onClick={() => setConfirmOpen(true)}
              disabled={!stats || stats.vectorCount === 0}
            >
              <Trash2 className="h-4 w-4" />
              Delete Index
            </Button>
          </CardContent>
        </Card>
      </div>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete the vector index?</DialogTitle>
            <DialogDescription>
              All {stats?.vectorCount?.toLocaleString()} vectors will be removed from Qdrant and
              semantic search will stop returning results. Documents and chunks are kept — you can
              rebuild by re-indexing documents.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={confirmDeleteIndex} disabled={deleteIndexMut.isPending}>
              {deleteIndexMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              Delete index
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// --------------------------------------------------------------------------- //
// Semantic search panel
// --------------------------------------------------------------------------- //
function ScoreBar({ score }: { score: number }) {
  const percent = Math.round(Math.max(0, Math.min(1, score)) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary" style={{ width: `${percent}%` }} />
      </div>
      <span className="text-xs font-medium tabular-nums text-muted-foreground">{score.toFixed(3)}</span>
    </div>
  );
}

function SemanticSearchPanel({ onOpenDocument }: { onOpenDocument: (documentId: string) => void }) {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState("5");
  const [categoryId, setCategoryId] = useState("all");
  const [brand, setBrand] = useState("");
  const { data: categories } = useKnowledgeCategories();
  const searchMut = useSemanticSearch();

  const runSearch = () => {
    if (!query.trim()) return;
    searchMut.mutate({
      query: query.trim(),
      topK: Number(topK),
      categoryId,
      brand: brand.trim() || undefined,
    });
  };

  const data = searchMut.data;

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="space-y-3 p-4">
          <div className="flex flex-col gap-3 lg:flex-row">
            <div className="relative flex-1">
              <Sparkles className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Ask the knowledge base… e.g. “what is our brand tone of voice?”"
                className="pl-9"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && runSearch()}
              />
            </div>
            <Select value={topK} onValueChange={setTopK}>
              <SelectTrigger className="lg:w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {["3", "5", "10", "20"].map((k) => (
                  <SelectItem key={k} value={k}>Top {k}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={categoryId} onValueChange={setCategoryId}>
              <SelectTrigger className="lg:w-[190px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All categories</SelectItem>
                {(categories || []).map((c) => (
                  <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              placeholder="Brand filter"
              className="lg:w-[150px]"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runSearch()}
            />
            <Button variant="gradient" onClick={runSearch} disabled={!query.trim() || searchMut.isPending}>
              {searchMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Search
            </Button>
          </div>
          {data && (
            <p className="text-xs text-muted-foreground">
              {data.total} result{data.total === 1 ? "" : "s"} · {data.tookMs.toFixed(0)} ms · similarity via vector search
            </p>
          )}
        </CardContent>
      </Card>

      {searchMut.isPending ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24 w-full" />)}
        </div>
      ) : !data ? (
        <EmptyState
          icon={<FileSearch className="h-6 w-6" />}
          title="Search your knowledge base"
          description="Results are matched by meaning, not keywords — chunks from your indexed documents ranked by similarity."
        />
      ) : data.results.length === 0 ? (
        <EmptyState
          icon={<FileSearch className="h-6 w-6" />}
          title="No matches"
          description="No indexed chunks matched this query. Check that documents are embedded, or loosen the filters."
        />
      ) : (
        <div className="space-y-3">
          {data.results.map((r: SemanticSearchResult, i: number) => (
            <motion.div
              key={r.chunkId}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <Card>
                <CardContent className="space-y-2 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <button
                      className="flex items-center gap-2 text-left text-sm font-medium hover:text-primary"
                      onClick={() => onOpenDocument(r.documentId)}
                    >
                      <FileText className="h-4 w-4 shrink-0 text-primary" />
                      {r.title || "Untitled document"}
                      <span className="text-xs font-normal text-muted-foreground">
                        {r.docType?.toUpperCase()}
                        {r.page ? ` · page ${r.page}` : ""} · chunk {r.chunkIndex + 1}
                      </span>
                    </button>
                    <ScoreBar score={r.score} />
                  </div>
                  <p className="line-clamp-4 whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                    {r.content}
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {r.categoryName && <Badge variant="outline">{r.categoryName}</Badge>}
                    {r.brand && <Badge variant="outline">{r.brand}</Badge>}
                    {r.tags.slice(0, 4).map((t) => (
                      <Badge key={t} variant="secondary">#{t}</Badge>
                    ))}
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

// --------------------------------------------------------------------------- //
// Page
// --------------------------------------------------------------------------- //
export default function KnowledgeBase() {
  const [search, setSearch] = useState("");
  const [type, setType] = useState("all");
  const [status, setStatus] = useState("all");
  const [categoryId, setCategoryId] = useState("all");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [preview, setPreview] = useState<KnowledgeDocument | null>(null);
  const [replaceTarget, setReplaceTarget] = useState<KnowledgeDocument | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<KnowledgeDocument | null>(null);

  const { data, isLoading } = useKnowledge({ search, type, status, categoryId });
  const { data: categories } = useKnowledgeCategories();
  const deleteMut = useDeleteKnowledge();
  const reindexMut = useReindexKnowledge();

  const rows = data || [];

  const openDocumentPreview = async (documentId: string) => {
    const known = rows.find((d) => d.id === documentId);
    if (known) {
      setPreview(known);
      return;
    }
    try {
      setPreview(await knowledgeService.get(documentId));
    } catch {
      toast.error("Could not load document");
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteMut.mutateAsync(deleteTarget.id);
      toast.success("Document deleted", { description: deleteTarget.title });
      setDeleteTarget(null);
    } catch {
      toast.error("Could not delete document");
    }
  };

  const handleReindex = async (d: KnowledgeDocument) => {
    try {
      const updated = await reindexMut.mutateAsync(d.id);
      if (updated.status === "ready") {
        toast.success("Document re-indexed", { description: `${updated.chunkCount} chunks extracted` });
      } else {
        toast.warning("Re-index failed", { description: updated.errorMessage || undefined });
      }
    } catch (err) {
      toast.error("Could not re-index", { description: normalizeError(err).message });
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Knowledge Base"
        description="Your indexed documents, brand guidelines and reference material."
        actions={
          <Button variant="gradient" size="sm" onClick={() => setUploadOpen(true)}>
            <Upload className="h-4 w-4" />
            Upload Document
          </Button>
        }
      />

      {/* Vector index stats */}
      <IndexStatsBar />

      <Tabs defaultValue="documents">
        <TabsList>
          <TabsTrigger value="documents" className="gap-1">
            <FileBox className="h-3.5 w-3.5" /> Documents
          </TabsTrigger>
          <TabsTrigger value="search" className="gap-1">
            <Sparkles className="h-3.5 w-3.5" /> Semantic Search
          </TabsTrigger>
        </TabsList>

        <TabsContent value="documents" className="space-y-6 pt-4">
      {/* Filters */}
      <Card>
        <CardContent className="flex flex-col gap-3 p-4 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search by title, tag or brand…"
              className="pl-9"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={type} onValueChange={setType}>
            <SelectTrigger className="lg:w-[140px]">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {["pdf", "docx", "txt", "md", "csv", "image"].map((t) => (
                <SelectItem key={t} value={t}>{t.toUpperCase()}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={categoryId} onValueChange={setCategoryId}>
            <SelectTrigger className="lg:w-[190px]">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All categories</SelectItem>
              {(categories || []).map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.name} ({c.documentCount})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="lg:w-[150px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="ready">Ready</SelectItem>
              <SelectItem value="processing">Processing</SelectItem>
              <SelectItem value="queued">Queued</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : rows.length === 0 ? (
            <EmptyState
              icon={<FileBox className="h-6 w-6" />}
              title="No documents found"
              description="Try adjusting your filters or upload a new document to the knowledge base."
              className="m-4"
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Document</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Ver.</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Vectors</TableHead>
                  <TableHead>Uploaded By</TableHead>
                  <TableHead>Uploaded</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((d, i) => (
                  <motion.tr
                    key={d.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.03 }}
                    className="border-b border-border/70 transition-colors hover:bg-muted/40"
                  >
                    <TableCell>
                      <button
                        onClick={() => setPreview(d)}
                        className="flex items-center gap-3 text-left"
                      >
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                          {TYPE_ICON[d.type] ?? <File className="h-4 w-4" />}
                        </div>
                        <div className="min-w-0">
                          <p className="max-w-[260px] truncate text-sm font-medium hover:text-primary">{d.title}</p>
                          <p className="max-w-[260px] truncate text-xs text-muted-foreground">
                            {d.status === "failed" ? d.errorMessage || "Indexing failed" : d.excerpt?.slice(0, 64) || "—"}
                          </p>
                        </div>
                      </button>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="uppercase">{d.type}</Badge>
                    </TableCell>
                    <TableCell><CategoryBadge doc={d} /></TableCell>
                    <TableCell className="text-muted-foreground">v{d.version}</TableCell>
                    <TableCell className="text-muted-foreground">{formatBytes(d.size)}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_BADGE[d.status].variant} className="gap-1">
                        {STATUS_BADGE[d.status].icon}
                        {STATUS_BADGE[d.status].label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={EMBED_BADGE[d.embeddingStatus].variant}
                        className="gap-1"
                        title={d.embeddingStatus === "failed" ? d.embeddingError || undefined : d.embeddingModel || undefined}
                      >
                        {EMBED_BADGE[d.embeddingStatus].icon}
                        {d.embeddingStatus === "completed" ? `${d.vectorCount} vectors` : EMBED_BADGE[d.embeddingStatus].label}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{d.uploadedBy}</TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(d.uploadedAt)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon-sm" onClick={() => setPreview(d)} aria-label="Preview">
                          <Eye className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label="Download"
                          onClick={() =>
                            knowledgeService
                              .download(d.id, d.originalFilename || d.title)
                              .catch(() => toast.error("Download failed"))
                          }
                        >
                          <Download className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label="Replace"
                          onClick={() => setReplaceTarget(d)}
                        >
                          <RefreshCw className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label="Re-index"
                          disabled={reindexMut.isPending}
                          onClick={() => handleReindex(d)}
                        >
                          <RotateCw className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                          onClick={() => setDeleteTarget(d)}
                          aria-label="Delete"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </motion.tr>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
        </TabsContent>

        <TabsContent value="search" className="pt-4">
          <SemanticSearchPanel onOpenDocument={openDocumentPreview} />
        </TabsContent>
      </Tabs>

      <UploadDialog open={uploadOpen} onClose={() => setUploadOpen(false)} />
      <ReplaceDialog doc={replaceTarget} onClose={() => setReplaceTarget(null)} />
      <PreviewDialog doc={preview} onClose={() => setPreview(null)} />

      {/* Delete confirm */}
      <Dialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete document?</DialogTitle>
            <DialogDescription>
              You're about to permanently delete{" "}
              <span className="font-semibold text-foreground">{deleteTarget?.title}</span>{" "}
              — including its chunks, version history and stored files.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDelete} disabled={deleteMut.isPending}>
              Delete document
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
