import { useState, useMemo } from "react";
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
  Trash2,
  Eye,
  Download,
  FileBox,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
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
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { useKnowledge, useDeleteKnowledge } from "@/hooks/useApi";
import { cn, formatCompact, formatDate } from "@/lib/utils";
import type { KnowledgeDocument } from "@/types";

const TYPE_ICON: Record<KnowledgeDocument["type"], React.ReactNode> = {
  pdf: <FileText className="h-4 w-4" />,
  docx: <FileText className="h-4 w-4" />,
  xlsx: <FileSpreadsheet className="h-4 w-4" />,
  csv: <FileSpreadsheet className="h-4 w-4" />,
  txt: <File className="h-4 w-4" />,
  md: <FileCode className="h-4 w-4" />,
  url: <Globe className="h-4 w-4" />,
};

const STATUS_BADGE: Record<KnowledgeDocument["status"], { variant: "success" | "warning" | "destructive" | "secondary"; label: string; icon: React.ReactNode }> = {
  ready: { variant: "success", label: "Ready", icon: <CheckCircle2 className="h-3 w-3" /> },
  processing: { variant: "warning", label: "Processing", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
  queued: { variant: "secondary", label: "Queued", icon: <Clock className="h-3 w-3" /> },
  failed: { variant: "destructive", label: "Failed", icon: <AlertCircle className="h-3 w-3" /> },
};

function formatBytes(b: number): string {
  if (!b) return "—";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
}

export default function KnowledgeBase() {
  const [search, setSearch] = useState("");
  const [type, setType] = useState("all");
  const [status, setStatus] = useState("all");
  const [preview, setPreview] = useState<KnowledgeDocument | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<KnowledgeDocument | null>(null);

  const { data, isLoading } = useKnowledge({ search, type, status });
  const deleteMut = useDeleteKnowledge();

  const rows = data || [];

  const handleUploadClick = () => {
    toast("Upload dialog", {
      description: "Drag & drop files in the Uploads page to add new documents.",
    });
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

  return (
    <div className="space-y-6">
      <PageHeader
        title="Knowledge Base"
        description="Your indexed documents, brand guidelines and reference material."
        actions={
          <Button variant="gradient" size="sm" onClick={handleUploadClick}>
            <Upload className="h-4 w-4" />
            Upload Document
          </Button>
        }
      />

      {/* Filters */}
      <Card>
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search by title or tag…"
              className="pl-9"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={type} onValueChange={setType}>
            <SelectTrigger className="sm:w-[160px]">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {["pdf", "docx", "xlsx", "csv", "txt", "md", "url"].map((t) => (
                <SelectItem key={t} value={t}>
                  {t.toUpperCase()}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="sm:w-[160px]">
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
                  <TableHead>Size</TableHead>
                  <TableHead>Status</TableHead>
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
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                          {TYPE_ICON[d.type]}
                        </div>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium hover:text-primary">{d.title}</p>
                          <p className="truncate text-xs text-muted-foreground">
                            {d.excerpt?.slice(0, 64) || "—"}
                          </p>
                        </div>
                      </button>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="uppercase">{d.type}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatBytes(d.size)}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_BADGE[d.status].variant} className="gap-1">
                        {STATUS_BADGE[d.status].icon}
                        {STATUS_BADGE[d.status].label}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{d.uploadedBy}</TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(d.uploadedAt)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon-sm" onClick={() => setPreview(d)} aria-label="Preview">
                          <Eye className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon-sm" aria-label="Download" onClick={() => toast.info("Download started")}>
                          <Download className="h-3.5 w-3.5" />
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

      {/* Preview Dialog */}
      <Dialog open={!!preview} onOpenChange={(o) => !o && setPreview(null)}>
        <DialogContent className="max-w-2xl">
          {preview && (
            <>
              <DialogHeader>
                <div className="flex items-start gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    {TYPE_ICON[preview.type]}
                  </div>
                  <div className="min-w-0 flex-1">
                    <DialogTitle className="break-words">{preview.title}</DialogTitle>
                    <DialogDescription>
                      {preview.type.toUpperCase()} · {formatBytes(preview.size)} · uploaded by{" "}
                      {preview.uploadedBy} on {formatDate(preview.uploadedAt)}
                    </DialogDescription>
                  </div>
                </div>
              </DialogHeader>
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {preview.tags.map((t) => (
                    <Badge key={t} variant="secondary" className="gap-1">
                      #{t}
                    </Badge>
                  ))}
                  <Badge variant={STATUS_BADGE[preview.status].variant} className="gap-1">
                    {STATUS_BADGE[preview.status].icon}
                    {STATUS_BADGE[preview.status].label}
                  </Badge>
                </div>
                <div className="rounded-lg border border-border bg-muted/30 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Excerpt
                  </p>
                  <p className="mt-2 text-sm leading-relaxed">
                    {preview.excerpt || "No preview available for this document."}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-lg border border-border p-3">
                    <p className="text-xs text-muted-foreground">Document ID</p>
                    <p className="font-mono text-xs">{preview.id}</p>
                  </div>
                  <div className="rounded-lg border border-border p-3">
                    <p className="text-xs text-muted-foreground">Last indexed</p>
                    <p>{formatDate(preview.uploadedAt, { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" })}</p>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => toast.info("Download started")}>
                  <Download className="h-4 w-4" />
                  Download
                </Button>
                <Button variant="gradient" onClick={() => setPreview(null)}>
                  Close
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete confirm */}
      <Dialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete document?</DialogTitle>
            <DialogDescription>
              You're about to permanently delete{" "}
              <span className="font-semibold text-foreground">{deleteTarget?.title}</span> from the
              knowledge base.
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
