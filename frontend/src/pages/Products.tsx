import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Plus,
  Search,
  Pencil,
  Trash2,
  Package,
  PackageX,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { StatusBadge } from "@/components/common/StatusBadge";
import {
  useProducts,
  useCreateProduct,
  useUpdateProduct,
  useDeleteProduct,
} from "@/hooks/useApi";
import {
  cn,
  formatCurrency,
  formatNumber,
} from "@/lib/utils";
import type { Product, Status } from "@/types";

const STATUSES: (Status | "all")[] = ["all", "active", "draft", "paused", "archived"];

const schema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  sku: z.string().min(3, "SKU must be at least 3 characters"),
  category: z.string().min(2, "Category is required"),
  price: z.coerce.number().min(0, "Price must be ≥ 0"),
  stock: z.coerce.number().min(0, "Stock must be ≥ 0"),
  status: z.enum(["active", "draft", "paused", "archived"]),
});

type FormValues = z.infer<typeof schema>;

export default function Products() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(8);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<string>("all");
  const [formOpen, setFormOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);
  const [editing, setEditing] = useState<Product | null>(null);

  const { data, isLoading, isFetching } = useProducts({ page, pageSize, search, status });
  const createMut = useCreateProduct();
  const updateMut = useUpdateProduct();
  const deleteMut = useDeleteProduct();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", sku: "", category: "", price: 0, stock: 0, status: "draft" },
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;

  const openCreate = () => {
    setEditing(null);
    form.reset({ name: "", sku: "", category: "", price: 0, stock: 0, status: "draft" });
    setFormOpen(true);
  };

  const openEdit = (p: Product) => {
    setEditing(p);
    form.reset({
      name: p.name,
      sku: p.sku,
      category: p.category,
      price: p.price,
      stock: p.stock,
      status: p.status,
    });
    setFormOpen(true);
  };

  const onSubmit = async (values: FormValues) => {
    try {
      if (editing) {
        await updateMut.mutateAsync({ id: editing.id, payload: values });
        toast.success("Product updated", { description: values.name });
      } else {
        await createMut.mutateAsync(values);
        toast.success("Product created", { description: values.name });
      }
      setFormOpen(false);
    } catch (e) {
      toast.error("Could not save product");
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteMut.mutateAsync(deleteTarget.id);
      toast.success("Product deleted", { description: deleteTarget.name });
      setDeleteTarget(null);
    } catch {
      toast.error("Could not delete product");
    }
  };

  const filtered = data?.data || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Products"
        description="Manage your product catalogue, inventory and pricing."
        actions={
          <Button variant="gradient" size="sm" onClick={openCreate}>
            <Plus className="h-4 w-4" />
            New Product
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
              placeholder="Search by name, SKU or category…"
              className="pl-9"
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
            />
          </div>
          <Select value={status} onValueChange={(v) => { setPage(1); setStatus(v); }}>
            <SelectTrigger className="sm:w-[180px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              {STATUSES.map((s) => (
                <SelectItem key={s} value={s}>
                  {s === "all" ? "All statuses" : s.charAt(0).toUpperCase() + s.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={<PackageX className="h-6 w-6" />}
              title="No products found"
              description="Try adjusting your search or filters, or create your first product."
              action={
                <Button variant="gradient" size="sm" onClick={openCreate}>
                  <Plus className="h-4 w-4" />
                  New Product
                </Button>
              }
              className="m-4"
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead className="text-right">Sales</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((p, i) => (
                  <motion.tr
                    key={p.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.03 }}
                    className="border-b border-border/70 transition-colors hover:bg-muted/40"
                  >
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary/15 to-[hsl(var(--chart-2)/0.15)] text-primary">
                          <Package className="h-4 w-4" />
                        </div>
                        <span>{p.name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">{p.sku}</TableCell>
                    <TableCell>{p.category}</TableCell>
                    <TableCell className="text-right font-medium">{formatCurrency(p.price)}</TableCell>
                    <TableCell className="text-right">
                      <span className={cn(p.stock === 0 && "text-destructive font-medium")}>
                        {formatNumber(p.stock)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">{formatNumber(p.sales)}</TableCell>
                    <TableCell><StatusBadge status={p.status} /></TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => openEdit(p)}
                          aria-label="Edit"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                          onClick={() => setDeleteTarget(p)}
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

      {/* Pagination */}
      {!isLoading && filtered.length > 0 && (
        <div className="flex items-center justify-between text-sm">
          <p className="text-muted-foreground">
            Showing <span className="font-medium text-foreground">{(page - 1) * pageSize + 1}</span>–
            <span className="font-medium text-foreground">{Math.min(page * pageSize, data?.total ?? 0)}</span> of{" "}
            <span className="font-medium text-foreground">{data?.total ?? 0}</span>
            {isFetching && <span className="ml-2 text-xs">· refreshing…</span>}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              <ChevronLeft className="h-4 w-4" />
              Prev
            </Button>
            <span className="text-xs text-muted-foreground">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>{editing ? "Edit Product" : "New Product"}</DialogTitle>
            <DialogDescription>
              {editing
                ? "Update the details for this product."
                : "Fill in the details below to add a new product to your catalogue."}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2 space-y-1.5">
                <Label htmlFor="name">Product Name</Label>
                <Input id="name" {...form.register("name")} placeholder="Aurora Serum" />
                {form.formState.errors.name && (
                  <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="sku">SKU</Label>
                <Input id="sku" {...form.register("sku")} placeholder="NUM-SRM-001" />
                {form.formState.errors.sku && (
                  <p className="text-xs text-destructive">{form.formState.errors.sku.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="category">Category</Label>
                <Input id="category" {...form.register("category")} placeholder="Skincare" />
                {form.formState.errors.category && (
                  <p className="text-xs text-destructive">{form.formState.errors.category.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="price">Price (USD)</Label>
                <Input id="price" type="number" step="0.01" {...form.register("price")} />
                {form.formState.errors.price && (
                  <p className="text-xs text-destructive">{form.formState.errors.price.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="stock">Stock</Label>
                <Input id="stock" type="number" {...form.register("stock")} />
                {form.formState.errors.stock && (
                  <p className="text-xs text-destructive">{form.formState.errors.stock.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={form.watch("status")}
                  onValueChange={(v) => form.setValue("status", v as Status)}
                >
                  <SelectTrigger id="status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(["active", "draft", "paused", "archived"] as Status[]).map((s) => (
                      <SelectItem key={s} value={s}>
                        {s.charAt(0).toUpperCase() + s.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="gradient"
                disabled={createMut.isPending || updateMut.isPending}
              >
                {editing ? "Save changes" : "Create product"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete confirm */}
      <Dialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10 text-destructive">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <DialogTitle>Delete product?</DialogTitle>
            <DialogDescription>
              You're about to permanently delete{" "}
              <span className="font-semibold text-foreground">{deleteTarget?.name}</span>. This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDelete}
              disabled={deleteMut.isPending}
            >
              Delete product
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
