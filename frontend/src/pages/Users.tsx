import { useState } from "react";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import type { LucideIcon } from "lucide-react";
import { Plus, Trash2, UserPlus, Shield, MoreHorizontal, Mail } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { useUsers, useCreateUser, useDeleteUser } from "@/hooks/useApi";
import { cn, formatDate, getInitials, timeAgo } from "@/lib/utils";
import type { User } from "@/types";

const ROLE_VARIANT: Record<string, "default" | "secondary" | "success" | "warning"> = {
  admin: "warning",
  manager: "default",
  editor: "secondary",
  viewer: "success",
};

const STATUS_VARIANT: Record<User["status"], "success" | "warning" | "destructive"> = {
  active: "success",
  invited: "warning",
  suspended: "destructive",
};

const schema = z.object({
  name: z.string().min(2, "Name is required"),
  email: z.string().email("Valid email required"),
  role: z.enum(["admin", "manager", "editor", "viewer"]),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Must contain at least one uppercase letter")
    .regex(/[0-9]/, "Must contain at least one digit"),
});

type FormValues = z.infer<typeof schema>;

export default function Users() {
  const { data, isLoading } = useUsers();
  const createMut = useCreateUser();
  const deleteMut = useDeleteUser();
  const [open, setOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", email: "", role: "viewer", password: "" },
  });

  const users = data || [];

  const onSubmit = async (values: FormValues) => {
    try {
      await createMut.mutateAsync(values);
      toast.success("User invited", { description: `${values.name} (${values.email})` });
      setOpen(false);
      form.reset();
    } catch {
      toast.error("Could not invite user");
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    await deleteMut.mutateAsync(deleteTarget.id);
    toast.success("User removed", { description: deleteTarget.name });
    setDeleteTarget(null);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Users"
        description="Manage team members, their roles and access to your workspace."
        actions={
          <Button variant="gradient" size="sm" onClick={() => setOpen(true)}>
            <Plus className="h-4 w-4" />
            Invite User
          </Button>
        }
      />

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Members", value: users.length, icon: UserPlus },
          { label: "Admins", value: users.filter((u) => u.role === "admin").length, icon: Shield },
          { label: "Active", value: users.filter((u) => u.status === "active").length, icon: Shield },
          { label: "Pending Invites", value: users.filter((u) => u.status === "invited").length, icon: Mail },
        ].map((s, i) => {
          const Icon = s.icon as LucideIcon;
          return (
            <Card key={i}>
              <CardContent className="flex items-center gap-3 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">{s.label}</p>
                  <p className="text-xl font-bold">{s.value}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Users table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : users.length === 0 ? (
            <EmptyState
              icon={<UserPlus className="h-6 w-6" />}
              title="No users yet"
              description="Invite team members to collaborate."
              className="m-4"
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Active</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((u) => (
                  <tr
                    key={u.id}
                    className="border-b border-border/70 transition-colors hover:bg-muted/40"
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-9 w-9">
                          <AvatarFallback>{u.name ? getInitials(u.name) : "??"}</AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="text-sm font-medium">{u.name}</p>
                          <p className="text-xs text-muted-foreground">{u.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={ROLE_VARIANT[u.role] || "default"}>{u.role}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[u.status] || "success"} className="capitalize">
                        {u.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{u.lastActive ? timeAgo(u.lastActive) : "Never"}</TableCell>
                    <TableCell className="text-muted-foreground">{u.createdAt ? formatDate(u.createdAt) : "N/A"}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        {u.role !== "admin" && (
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                            onClick={() => setDeleteTarget(u)}
                            aria-label="Remove"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        <Button variant="ghost" size="icon-sm" aria-label="More">
                          <MoreHorizontal className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </tr>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Invite dialog */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Invite team member</DialogTitle>
            <DialogDescription>
              Send an invitation to join your NUMÉ workspace.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="name">Full Name</Label>
              <Input id="name" placeholder="Jane Doe" {...form.register("name")} />
              {form.formState.errors.name && (
                <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="jane@nume.ai" {...form.register("email")} />
              {form.formState.errors.email && (
                <p className="text-xs text-destructive">{form.formState.errors.email.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="role">Role</Label>
              <Select value={form.watch("role")} onValueChange={(v) => form.setValue("role", v as any)}>
                <SelectTrigger id="role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin — full access</SelectItem>
                  <SelectItem value="manager">Manager — manage campaigns</SelectItem>
                  <SelectItem value="editor">Editor — manage content</SelectItem>
                  <SelectItem value="viewer">Viewer — read only</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Temporary Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Min 8 chars, 1 uppercase, 1 digit"
                {...form.register("password")}
              />
              {form.formState.errors.password && (
                <p className="text-xs text-destructive">{form.formState.errors.password.message}</p>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="gradient" disabled={createMut.isPending}>
                Send invite
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete confirm */}
      <Dialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Remove user?</DialogTitle>
            <DialogDescription>
              You're about to remove{" "}
              <span className="font-semibold text-foreground">{deleteTarget?.name}</span> from the
              workspace. They will lose access immediately.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={deleteMut.isPending} onClick={confirmDelete}>
              Remove user
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}