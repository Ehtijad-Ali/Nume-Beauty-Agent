import { useState } from "react";
import { toast } from "sonner";
import { Camera, Mail, Briefcase, Calendar, Shield, Save, KeyRound } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/context/AuthContext";
import { getInitials } from "@/lib/utils";

export default function Profile() {
  const { user } = useAuth();
  const [name, setName] = useState(user?.name || "");
  const [email, setEmail] = useState(user?.email || "");

  const handleSave = () => {
    toast.success("Profile updated", { description: "Your changes have been saved." });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Profile"
        description="Manage your personal information and account preferences."
      />

      {/* Profile header */}
      <Card className="overflow-hidden">
        <div className="h-32 w-full bg-brand-gradient" />
        <CardContent className="px-6 pb-6">
          <div className="-mt-12 flex flex-col gap-4 sm:flex-row sm:items-end">
            <div className="relative">
              <Avatar className="h-24 w-24 border-4 border-card shadow-elevated">
                <AvatarFallback className="text-2xl">{user ? getInitials(user.name) : "?"}</AvatarFallback>
              </Avatar>
              <button
                className="absolute bottom-1 right-1 flex h-7 w-7 items-center justify-center rounded-full border border-border bg-card text-foreground shadow-soft hover:bg-muted"
                aria-label="Change avatar"
              >
                <Camera className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="flex-1 pb-2">
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold">{user?.name}</h2>
                <Badge variant="default">{user?.role}</Badge>
              </div>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
            </div>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-border p-4">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Mail className="h-4 w-4" />
                <span className="text-xs">Email</span>
              </div>
              <p className="mt-1 truncate text-sm font-medium">{user?.email}</p>
            </div>
            <div className="rounded-lg border border-border p-4">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Briefcase className="h-4 w-4" />
                <span className="text-xs">Role</span>
              </div>
              <p className="mt-1 text-sm font-medium">{user?.role}</p>
            </div>
            <div className="rounded-lg border border-border p-4">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span className="text-xs">Member since</span>
              </div>
              <p className="mt-1 text-sm font-medium">Jan 2024</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Personal info */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Update your account details.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="name">Full Name</Label>
                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
            </div>
            <Separator />
            <div className="flex justify-end">
              <Button variant="gradient" onClick={handleSave}>
                <Save className="h-4 w-4" />
                Save changes
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Security */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <CardTitle>Security</CardTitle>
            </div>
            <CardDescription>Manage your password and access.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5">
              <Label>Current Password</Label>
              <Input type="password" placeholder="••••••••" />
            </div>
            <div className="space-y-1.5">
              <Label>New Password</Label>
              <Input type="password" placeholder="••••••••" />
            </div>
            <Button variant="outline" className="w-full" onClick={() => toast.info("Password update link sent to your email")}>
              <KeyRound className="h-4 w-4" />
              Update Password
            </Button>
            <div className="rounded-lg border border-border bg-muted/30 p-3">
              <p className="text-xs font-medium">Two-factor authentication</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Add an extra layer of security to your account.
              </p>
              <Button variant="outline" size="sm" className="mt-2 w-full" onClick={() => toast.success("2FA setup started")}>
                Enable 2FA
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
