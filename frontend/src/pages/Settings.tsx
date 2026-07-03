import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Building2,
  Globe,
  Palette,
  KeyRound,
  Save,
  Eye,
  EyeOff,
  Check,
  Copy,
  Sun,
  Moon,
  Monitor,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { useSettings, useUpdateSettings } from "@/hooks/useApi";
import { useTheme } from "@/context/ThemeProvider";
import { cn, maskApiKey } from "@/lib/utils";
import type { AppSettings } from "@/types";

const TIMEZONES = [
  "Asia/Karachi",
  "Asia/Dubai",
  "Asia/Tokyo",
  "Europe/London",
  "Europe/Paris",
  "America/New_York",
  "America/Los_Angeles",
  "UTC",
];

const LANGUAGES = ["English", "Urdu", "Arabic", "French", "German", "Spanish", "Mandarin"];

const PROVIDERS = [
  { id: "openai", label: "OpenAI", desc: "GPT-4o, GPT-4 Turbo" },
  { id: "anthropic", label: "Anthropic", desc: "Claude 3.5 Sonnet, Haiku" },
  { id: "gemini", label: "Google Gemini", desc: "Gemini 1.5 Pro, Flash" },
  { id: "cohere", label: "Cohere", desc: "Command R+" },
  { id: "mistral", label: "Mistral", desc: "Mistral Large, Nemo" },
] as const;

function MaskedKey({ value, label }: { value: string; label: string }) {
  const [visible, setVisible] = useState(false);
  const [copied, setCopied] = useState(false);
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <KeyRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            readOnly
            value={visible ? value : maskApiKey(value)}
            className="pl-9 font-mono"
          />
        </div>
        <Button type="button" variant="outline" size="icon" onClick={() => setVisible((v) => !v)}>
          {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="icon"
          onClick={() => {
            navigator.clipboard?.writeText(value);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
          }}
        >
          {copied ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}

export default function Settings() {
  const { data, isLoading } = useSettings();
  const updateMut = useUpdateSettings();
  const { theme, setTheme } = useTheme();
  const [form, setForm] = useState<AppSettings | null>(null);

  useEffect(() => {
    if (data) setForm(data);
  }, [data]);

  if (isLoading || !form) {
    return (
      <div className="space-y-6">
        <PageHeader title="Settings" description="Configure your workspace." />
        <Skeleton className="h-10 w-full max-w-md" />
        <Skeleton className="h-96 rounded-xl" />
      </div>
    );
  }

  const update = (patch: Partial<AppSettings>) => setForm((f) => (f ? { ...f, ...patch } : f));

  const save = async () => {
    try {
      await updateMut.mutateAsync(form);
      toast.success("Settings saved", { description: "Your changes have been applied." });
    } catch {
      toast.error("Could not save settings");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Manage your company, branding, language and AI provider configuration."
        actions={
          <Button variant="gradient" size="sm" onClick={save} disabled={updateMut.isPending}>
            <Save className="h-4 w-4" />
            Save Changes
          </Button>
        }
      />

      <Tabs defaultValue="company">
        <TabsList>
          <TabsTrigger value="company">Company</TabsTrigger>
          <TabsTrigger value="localization">Localisation</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="ai">AI Provider</TabsTrigger>
        </TabsList>

        {/* Company */}
        <TabsContent value="company" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-muted-foreground" />
                <CardTitle>Company Information</CardTitle>
              </div>
              <CardDescription>Basic information about your organisation.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="companyName">Company Name</Label>
                <Input
                  id="companyName"
                  value={form.companyName}
                  onChange={(e) => update({ companyName: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="brandName">Brand Name</Label>
                <Input
                  id="brandName"
                  value={form.brandName}
                  onChange={(e) => update({ brandName: e.target.value })}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Localisation */}
        <TabsContent value="localization" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-muted-foreground" />
                <CardTitle>Localisation</CardTitle>
              </div>
              <CardDescription>Set timezone and language preferences for your workspace.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Timezone</Label>
                <Select value={form.timezone} onValueChange={(v) => update({ timezone: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TIMEZONES.map((tz) => (
                      <SelectItem key={tz} value={tz}>
                        {tz}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Language</Label>
                <Select value={form.language} onValueChange={(v) => update({ language: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LANGUAGES.map((l) => (
                      <SelectItem key={l} value={l}>
                        {l}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance */}
        <TabsContent value="appearance" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Palette className="h-4 w-4 text-muted-foreground" />
                <CardTitle>Theme</CardTitle>
              </div>
              <CardDescription>Choose how NUMÉ looks across your devices.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-3">
                {[
                  { id: "light", label: "Light", icon: Sun },
                  { id: "dark", label: "Dark", icon: Moon },
                  { id: "system", label: "System", icon: Monitor },
                ].map((opt) => {
                  const active = theme === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setTheme(opt.id as any)}
                      className={cn(
                        "flex flex-col items-center justify-center gap-2 rounded-xl border p-5 text-sm transition-all",
                        active
                          ? "border-primary bg-primary/5 shadow-glow"
                          : "border-border bg-card hover:border-primary/40 hover:bg-muted/40"
                      )}
                    >
                      <opt.icon
                        className={cn("h-5 w-5", active ? "text-primary" : "text-muted-foreground")}
                      />
                      <span className="font-medium">{opt.label}</span>
                      {active && (
                        <Badge variant="default" className="mt-1 gap-1">
                          <Check className="h-3 w-3" />
                          Active
                        </Badge>
                      )}
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Provider */}
        <TabsContent value="ai" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <KeyRound className="h-4 w-4 text-muted-foreground" />
                <CardTitle>LLM Provider</CardTitle>
              </div>
              <CardDescription>
                Choose your default AI provider and manage API keys. Keys are stored locally for this demo.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {PROVIDERS.map((p) => {
                  const active = form.llmProvider === p.id;
                  return (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => update({ llmProvider: p.id as AppSettings["llmProvider"] })}
                      className={cn(
                        "flex flex-col gap-1 rounded-xl border p-4 text-left transition-all",
                        active
                          ? "border-primary bg-primary/5 shadow-glow"
                          : "border-border bg-card hover:border-primary/40 hover:bg-muted/40"
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">{p.label}</span>
                        {active && (
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground">
                            <Check className="h-3 w-3" />
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">{p.desc}</p>
                    </button>
                  );
                })}
              </div>

              <Separator />

              <div className="space-y-4">
                <div>
                  <p className="text-sm font-semibold">API Keys</p>
                  <p className="text-xs text-muted-foreground">
                    Keys are masked by default. Click the eye icon to reveal.
                  </p>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <MaskedKey label="OpenAI API Key" value={form.openaiKey} />
                  <MaskedKey label="Anthropic API Key" value={form.anthropicKey} />
                  <MaskedKey label="Google Gemini API Key" value={form.geminiKey} />
                  <div className="space-y-1.5">
                    <Label htmlFor="model">Default Model</Label>
                    <Input
                      id="model"
                      value={form.defaultModel}
                      onChange={(e) => update({ defaultModel: e.target.value })}
                      placeholder="gpt-4o"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
