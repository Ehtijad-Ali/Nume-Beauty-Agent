import { useState, useCallback, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import {
  UploadCloud,
  File as FileIcon,
  Download,
  Trash2,
  CheckCircle2,
  XCircle,
  Loader2,
  FileType2,
  X,
  RefreshCw,
  Search,
  Eye,
  Image as ImageIcon,
  FileText,
  FileSpreadsheet,
  FileVideo,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useUploads,
  useDeleteUpload,
  useUploadFile,
  useReplaceFile,
} from "@/hooks/useApi";
import { apiClient } from "@/api";
import { cn, formatDate } from "@/lib/utils";
import type { UploadRecord } from "@/types";

// --------------------------------------------------------------------------- //
// Helpers
// --------------------------------------------------------------------------- //
function formatBytes(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  if (b < 1024 * 1024 * 1024) return `${(b / 1024 / 1024).toFixed(1)} MB`;
  return `${(b / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

const ACCEPTED_TYPES: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  pdf: { label: "PDF", icon: <FileText className="h-4 w-4" />, color: "text-primary" },
  docx: { label: "DOCX", icon: <FileText className="h-4 w-4" />, color: "text-[hsl(var(--chart-4))]" },
  txt: { label: "TXT", icon: <FileText className="h-4 w-4" />, color: "text-muted-foreground" },
  csv: { label: "CSV", icon: <FileSpreadsheet className="h-4 w-4" />, color: "text-success" },
  xlsx: { label: "XLSX", icon: <FileSpreadsheet className="h-4 w-4" />, color: "text-success" },
  png: { label: "PNG", icon: <ImageIcon className="h-4 w-4" />, color: "text-[hsl(var(--chart-2))]" },
  jpg: { label: "JPG", icon: <ImageIcon className="h-4 w-4" />, color: "text-[hsl(var(--chart-2))]" },
  jpeg: { label: "JPEG", icon: <ImageIcon className="h-4 w-4" />, color: "text-[hsl(var(--chart-2))]" },
  webp: { label: "WEBP", icon: <ImageIcon className="h-4 w-4" />, color: "text-[hsl(var(--chart-2))]" },
  mp4: { label: "MP4", icon: <FileVideo className="h-4 w-4" />, color: "text-[hsl(var(--chart-3))]" },
  mov: { label: "MOV", icon: <FileVideo className="h-4 w-4" />, color: "text-[hsl(var(--chart-3))]" },
};

const ACCEPT_EXT = ".pdf,.docx,.txt,.csv,.png,.jpg,.jpeg,.webp,.mp4,.mov";

function getExt(filename: string): string {
  return filename.split(".").pop()?.toLowerCase() || "";
}

function getTypeMeta(filename: string) {
  const ext = getExt(filename);
  return ACCEPTED_TYPES[ext] || { label: ext.toUpperCase() || "FILE", icon: <FileType2 className="h-4 w-4" />, color: "text-muted-foreground" };
}

function isImage(filename: string): boolean {
  return ["png", "jpg", "jpeg", "webp"].includes(getExt(filename));
}

function isVideo(filename: string): boolean {
  return ["mp4", "mov"].includes(getExt(filename));
}

function detectCategory(filename: string): string {
  const ext = getExt(filename);
  if (["pdf", "docx", "txt"].includes(ext)) return "Knowledge";
  if (["xlsx", "csv"].includes(ext)) return "Report";
  if (["png", "jpg", "jpeg", "webp", "mp4", "mov"].includes(ext)) return "Asset";
  return "Other";
}

function previewUrl(upload: UploadRecord): string {
  // Build a relative URL that the axios baseURL will resolve.
  const base = apiClient.defaults.baseURL || "";
  return `${base}/uploads/${upload.id}/download`;
}

// --------------------------------------------------------------------------- //
// Pending file (upload in progress)
// --------------------------------------------------------------------------- //
interface PendingFile {
  id: string;
  file: File;
  progress: number;
  status: "uploading" | "completed" | "failed";
  category: string;
  error?: string;
}

// --------------------------------------------------------------------------- //
// Page
// --------------------------------------------------------------------------- //
export default function Uploads() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [status, setStatus] = useState("all");
  const { data, isLoading } = useUploads({ search, category, status });
  const deleteMut = useDeleteUpload();
  const uploadMut = useUploadFile();
  const replaceMut = useReplaceFile();

  const [pending, setPending] = useState<PendingFile[]>([]);
  const [dragging, setDragging] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<UploadRecord | null>(null);
  const [previewTarget, setPreviewTarget] = useState<UploadRecord | null>(null);
  const [replaceTarget, setReplaceTarget] = useState<UploadRecord | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const replaceInputRef = useRef<HTMLInputElement>(null);

  const uploads = data || [];

  const startUpload = useCallback(
    (file: File) => {
      const id = `pending_${Math.random().toString(36).slice(2, 8)}`;
      const pf: PendingFile = {
        id,
        file,
        progress: 0,
        status: "uploading",
        category: detectCategory(file.name),
      };
      setPending((p) => [pf, ...p]);

      uploadMut.mutate(
        {
          file,
          category: pf.category,
          onProgress: (e) => {
            setPending((arr) =>
              arr.map((x) => (x.id === id ? { ...x, progress: e.percent } : x))
            );
          },
        },
        {
          onSuccess: () => {
            setPending((arr) =>
              arr.map((x) => (x.id === id ? { ...x, progress: 100, status: "completed" } : x))
            );
            toast.success("Upload complete", { description: file.name });
            setTimeout(() => {
              setPending((arr) => arr.filter((x) => x.id !== id));
            }, 2000);
          },
          onError: (err: any) => {
            const msg = err?.response?.data?.error?.message || "Upload failed";
            setPending((arr) =>
              arr.map((x) => (x.id === id ? { ...x, status: "failed", error: msg } : x))
            );
            toast.error("Upload failed", { description: `${file.name}: ${msg}` });
          },
        }
      );
    },
    [uploadMut]
  );

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach((f) => startUpload(f));
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleReplace = (file: File) => {
    if (!replaceTarget) return;
    const id = `replace_${Math.random().toString(36).slice(2, 8)}`;
    setPending((p) => [
      { id, file, progress: 0, status: "uploading", category: replaceTarget.category },
      ...p,
    ]);
    replaceMut.mutate(
      {
        id: replaceTarget.id,
        file,
        category: replaceTarget.category,
        onProgress: (e) => {
          setPending((arr) =>
            arr.map((x) => (x.id === id ? { ...x, progress: e.percent } : x))
          );
        },
      },
      {
        onSuccess: () => {
          setPending((arr) =>
            arr.map((x) => (x.id === id ? { ...x, progress: 100, status: "completed" } : x))
          );
          toast.success("File replaced", { description: file.name });
          setReplaceTarget(null);
          setTimeout(() => {
            setPending((arr) => arr.filter((x) => x.id !== id));
          }, 2000);
        },
        onError: (err: any) => {
          const msg = err?.response?.data?.error?.message || "Replace failed";
          setPending((arr) =>
            arr.map((x) => (x.id === id ? { ...x, status: "failed", error: msg } : x))
          );
          toast.error("Replace failed", { description: msg });
        },
      }
    );
  };

  const handleDownload = async (u: UploadRecord) => {
    try {
      const res = await apiClient.get(`/uploads/${u.id}/download`, { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = u.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Download started", { description: u.filename });
    } catch (err: any) {
      toast.error("Download failed", { description: err?.message });
    }
  };

  // Compute metadata summary
  const summary = useMemo(() => {
    const total = uploads.length;
    const totalSize = uploads.reduce((s, u) => s + u.size, 0);
    const byCategory: Record<string, number> = {};
    uploads.forEach((u) => {
      byCategory[u.category] = (byCategory[u.category] || 0) + 1;
    });
    return { total, totalSize, byCategory };
  }, [uploads]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Uploads"
        description="Drag & drop files to upload assets, reports and knowledge documents. Supports PDF, DOCX, TXT, CSV, PNG, JPG, WEBP, MP4, MOV."
      />

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Files", value: summary.total, sub: "in storage" },
          { label: "Total Size", value: formatBytes(summary.totalSize), sub: "across all files" },
          { label: "Knowledge", value: summary.byCategory.Knowledge || 0, sub: "documents" },
          { label: "Assets", value: (summary.byCategory.Asset || 0) + (summary.byCategory.Report || 0), sub: "media + reports" },
        ].map((s, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className="mt-1 text-2xl font-bold">{s.value}</p>
              <p className="text-xs text-muted-foreground">{s.sub}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Dropzone */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <Card
          className={cn(
            "border-2 border-dashed transition-colors",
            dragging ? "border-primary bg-primary/5" : "border-border"
          )}
        >
          <CardContent className="p-0">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => inputRef.current?.click()}
              className="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center cursor-pointer"
            >
              <div
                className={cn(
                  "flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/15 to-[hsl(var(--chart-2)/0.15)] text-primary transition-transform",
                  dragging && "scale-110"
                )}
              >
                <UploadCloud className="h-8 w-8" />
              </div>
              <div>
                <p className="text-base font-semibold">
                  {dragging ? "Drop files to upload" : "Drag & drop files here"}
                </p>
                <p className="text-sm text-muted-foreground">
                  or <span className="text-primary font-medium">browse</span> from your computer
                </p>
              </div>
              <p className="text-xs text-muted-foreground">
                Multiple files supported · PDF, DOCX, TXT, CSV, PNG, JPG, WEBP, MP4, MOV · up to 50 MB each
              </p>
              <input
                ref={inputRef}
                type="file"
                multiple
                accept={ACCEPT_EXT}
                className="hidden"
                onChange={(e) => handleFiles(e.target.files)}
              />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Pending uploads */}
      <AnimatePresence>
        {pending.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card>
              <CardContent className="space-y-3 p-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">In progress</p>
                  <Button variant="ghost" size="sm" onClick={() => setPending([])}>
                    Clear
                  </Button>
                </div>
                {pending.map((p) => {
                  const meta = getTypeMeta(p.file.name);
                  return (
                    <div key={p.id} className="rounded-lg border border-border bg-muted/30 p-3">
                      <div className="flex items-center gap-3">
                        <div className={cn("flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10", meta.color)}>
                          {meta.icon}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between">
                            <p className="truncate text-sm font-medium">{p.file.name}</p>
                            <span className="text-xs text-muted-foreground">{formatBytes(p.file.size)}</span>
                          </div>
                          <div className="mt-1.5 flex items-center gap-2">
                            <Progress value={p.progress} className="h-1.5" />
                            <span className="w-10 text-right text-xs font-medium">
                              {p.status === "failed" ? "—" : `${Math.round(p.progress)}%`}
                            </span>
                          </div>
                          {p.status === "failed" && p.error && (
                            <p className="mt-1 text-xs text-destructive">{p.error}</p>
                          )}
                        </div>
                        <div className="flex items-center">
                          {p.status === "completed" ? (
                            <CheckCircle2 className="h-4 w-4 text-success" />
                          ) : p.status === "failed" ? (
                            <XCircle className="h-4 w-4 text-destructive" />
                          ) : (
                            <Loader2 className="h-4 w-4 animate-spin text-primary" />
                          )}
                        </div>
                        <button
                          onClick={() => setPending((arr) => arr.filter((x) => x.id !== p.id))}
                          className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Search + filter bar */}
      <Card>
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search by filename or category…"
              className="pl-9"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={category} onValueChange={setCategory}>
            <SelectTrigger className="sm:w-[160px]">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All categories</SelectItem>
              <SelectItem value="Knowledge">Knowledge</SelectItem>
              <SelectItem value="Asset">Asset</SelectItem>
              <SelectItem value="Report">Report</SelectItem>
              <SelectItem value="Other">Other</SelectItem>
            </SelectContent>
          </Select>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="sm:w-[160px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="uploading">Uploading</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Uploaded files */}
      <Card>
        <CardContent className="p-0">
          <div className="border-b border-border p-4">
            <p className="text-sm font-semibold">Uploaded Files</p>
            <p className="text-xs text-muted-foreground">
              {uploads.length} file{uploads.length !== 1 ? "s" : ""} in storage
            </p>
          </div>

          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : uploads.length === 0 ? (
            <EmptyState
              icon={<FileIcon className="h-6 w-6" />}
              title="No uploads yet"
              description="Drag & drop files above to see them listed here."
              className="m-4"
            />
          ) : (
            <ul className="divide-y divide-border">
              {uploads.map((u) => {
                const meta = getTypeMeta(u.filename);
                const image = isImage(u.filename);
                const video = isVideo(u.filename);
                return (
                  <li key={u.id} className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/30">
                    {/* Preview thumbnail for images, icon otherwise */}
                    <button
                      onClick={() => setPreviewTarget(u)}
                      className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-primary/10"
                      aria-label="Preview"
                    >
                      {image ? (
                        <img src={previewUrl(u)} alt={u.filename} className="h-full w-full object-cover" />
                      ) : video ? (
                        <FileVideo className={cn("h-5 w-5", meta.color)} />
                      ) : (
                        <span className={meta.color}>{meta.icon}</span>
                      )}
                    </button>

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{u.filename}</p>
                      <div className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline" className={cn("uppercase", meta.color)}>{meta.label}</Badge>
                        <span>{formatBytes(u.size)}</span>
                        <span>·</span>
                        <span>{formatDate(u.uploadedAt)}</span>
                        <Badge variant="secondary" className="ml-1">{u.category}</Badge>
                      </div>
                    </div>

                    <div className="flex items-center gap-1">
                      {u.status === "completed" && (
                        <Badge variant="success" className="mr-2 gap-1">
                          <CheckCircle2 className="h-3 w-3" /> Completed
                        </Badge>
                      )}
                      {u.status === "uploading" && (
                        <Badge variant="warning" className="mr-2 gap-1">
                          <Loader2 className="h-3 w-3 animate-spin" /> {u.progress}%
                        </Badge>
                      )}
                      {u.status === "failed" && (
                        <Badge variant="destructive" className="mr-2 gap-1">
                          <XCircle className="h-3 w-3" /> Failed
                        </Badge>
                      )}
                      <Button variant="ghost" size="icon-sm" aria-label="Preview" onClick={() => setPreviewTarget(u)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon-sm" aria-label="Replace" onClick={() => setReplaceTarget(u)}>
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon-sm" aria-label="Download" onClick={() => handleDownload(u)}>
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                        aria-label="Delete"
                        onClick={() => setDeleteTarget(u)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Preview Dialog */}
      <Dialog open={!!previewTarget} onOpenChange={(o) => !o && setPreviewTarget(null)}>
        <DialogContent className="max-w-3xl">
          {previewTarget && (
            <>
              <DialogHeader>
                <div className="flex items-start gap-3">
                  <div className={cn("flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10", getTypeMeta(previewTarget.filename).color)}>
                    {getTypeMeta(previewTarget.filename).icon}
                  </div>
                  <div className="min-w-0 flex-1">
                    <DialogTitle className="break-words">{previewTarget.filename}</DialogTitle>
                    <DialogDescription>
                      {getTypeMeta(previewTarget.filename).label} · {formatBytes(previewTarget.size)} · uploaded {formatDate(previewTarget.uploadedAt)}
                    </DialogDescription>
                  </div>
                </div>
              </DialogHeader>
              <div className="space-y-4">
                {/* Inline preview for images and videos */}
                {isImage(previewTarget.filename) && (
                  <div className="overflow-hidden rounded-lg border border-border bg-muted/30">
                    <img src={previewUrl(previewTarget)} alt={previewTarget.filename} className="mx-auto max-h-[420px] object-contain" />
                  </div>
                )}
                {isVideo(previewTarget.filename) && (
                  <div className="overflow-hidden rounded-lg border border-border bg-black">
                    <video src={previewUrl(previewTarget)} controls className="mx-auto max-h-[420px]" />
                  </div>
                )}
                {!isImage(previewTarget.filename) && !isVideo(previewTarget.filename) && (
                  <div className="rounded-lg border border-border bg-muted/30 p-8 text-center">
                    <FileType2 className="mx-auto h-10 w-10 text-muted-foreground" />
                    <p className="mt-3 text-sm text-muted-foreground">
                      No inline preview available for {getTypeMeta(previewTarget.filename).label} files.
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">Use the download button below to view the file.</p>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-lg border border-border p-3">
                    <p className="text-xs text-muted-foreground">File ID</p>
                    <p className="font-mono text-xs truncate">{previewTarget.id}</p>
                  </div>
                  <div className="rounded-lg border border-border p-3">
                    <p className="text-xs text-muted-foreground">Category</p>
                    <p>{previewTarget.category}</p>
                  </div>
                  <div className="rounded-lg border border-border p-3">
                    <p className="text-xs text-muted-foreground">Size</p>
                    <p>{formatBytes(previewTarget.size)}</p>
                  </div>
                  <div className="rounded-lg border border-border p-3">
                    <p className="text-xs text-muted-foreground">Uploaded</p>
                    <p>{formatDate(previewTarget.uploadedAt, { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" })}</p>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => handleDownload(previewTarget)}>
                  <Download className="h-4 w-4" />
                  Download
                </Button>
                <Button variant="gradient" onClick={() => setPreviewTarget(null)}>
                  Close
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Replace Dialog */}
      <Dialog open={!!replaceTarget} onOpenChange={(o) => !o && setReplaceTarget(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Replace file</DialogTitle>
            <DialogDescription>
              Select a new file to replace{" "}
              <span className="font-semibold text-foreground">{replaceTarget?.filename}</span>.
              The original will be deleted.
            </DialogDescription>
          </DialogHeader>
          <div
            onClick={() => replaceInputRef.current?.click()}
            className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border p-8 text-center hover:border-primary/40 hover:bg-muted/30"
          >
            <UploadCloud className="h-8 w-8 text-primary" />
            <p className="text-sm font-medium">Click to choose a new file</p>
            <p className="text-xs text-muted-foreground">{ACCEPT_EXT}</p>
            <input
              ref={replaceInputRef}
              type="file"
              accept={ACCEPT_EXT}
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleReplace(f);
              }}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setReplaceTarget(null)}>
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirm */}
      <Dialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete file?</DialogTitle>
            <DialogDescription>
              You're about to permanently delete{" "}
              <span className="font-semibold text-foreground">{deleteTarget?.filename}</span>.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={deleteMut.isPending}
              onClick={async () => {
                if (!deleteTarget) return;
                try {
                  await deleteMut.mutateAsync(deleteTarget.id);
                  toast.success("File deleted", { description: deleteTarget.filename });
                  setDeleteTarget(null);
                } catch (err: any) {
                  toast.error("Could not delete file", { description: err?.message });
                }
              }}
            >
              Delete file
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
