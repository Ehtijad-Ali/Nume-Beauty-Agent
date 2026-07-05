import { useState } from "react";
import { useNavigate, useLocation, Navigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { Eye, EyeOff, Loader2, Mail, Lock, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Logo } from "@/components/common/Logo";
import { useAuth } from "@/context/AuthContext";

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type FormValues = z.infer<typeof schema>;

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showPwd, setShowPwd] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "admin@nume.ai", password: "Admin@12345" },
  });

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const onSubmit = async (values: FormValues) => {
    try {
      await login(values.email, values.password);
      toast.success("Welcome back!", { description: "You're now signed in to NUMÉ." });
      const from = (location.state as any)?.from?.pathname || "/";
      navigate(from, { replace: true });
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || err?.message || "Please try again.";
      toast.error("Login failed", { description: msg });
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Left: form */}
      <div className="flex flex-col justify-between p-6 sm:p-10 lg:p-12">
        <div className="flex items-center justify-between">
          <Logo />
          <span className="text-xs text-muted-foreground">v1.0 · SaaS</span>
        </div>

        <div className="mx-auto w-full max-w-sm py-10">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="space-y-2"
          >
            <h1 className="font-display text-3xl font-semibold tracking-tight">Welcome back</h1>
            <p className="text-sm text-muted-foreground">
              Sign in to your NUMÉ workspace to continue.
            </p>
          </motion.div>

          <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@brand.com"
                  className="pl-9"
                  {...register("email")}
                />
              </div>
              {errors.email && (
                <p className="text-xs text-destructive">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <a href="#" className="text-xs text-primary hover:underline">
                  Forgot?
                </a>
              </div>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPwd ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="px-9"
                  {...register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPwd((s) => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-xs text-destructive">{errors.password.message}</p>
              )}
            </div>

            <Button
              type="submit"
              variant="gradient"
              size="lg"
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Signing in…
                </>
              ) : (
                "Sign in"
              )}
            </Button>

            <p className="text-center text-xs text-muted-foreground">
              Demo credentials are pre-filled — just hit{" "}
              <span className="font-medium text-foreground">Sign in</span>.
            </p>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <a href="#" className="font-medium text-primary hover:underline">
              Start a trial
            </a>
          </p>
        </div>

        <p className="text-center text-xs text-muted-foreground">
          © 2025 NUMÉ Beauty Labs · All rights reserved
        </p>
      </div>

      {/* Right: brand showcase — campaign teaser shot */}
      <div className="relative hidden overflow-hidden lg:block">
        <img
          src="/brand/teaser-wand.jpg"
          alt="NUMÉ Beauty — coming soon campaign teaser"
          className="absolute inset-0 h-full w-full object-cover"
        />
        {/* darken the top edge so the copy stays legible over the photo */}
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-transparent" />

        <div className="relative flex h-full flex-col p-12 text-white">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="max-w-md"
          >
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur">
              <Sparkles className="h-3.5 w-3.5" />
              AI Marketing Intelligence
            </span>
            <h2 className="mt-6 font-display text-4xl font-medium leading-tight">
              Turn every signal into your next campaign.
            </h2>
            <p className="mt-3 text-white/80">
              NUMÉ unifies your products, knowledge base, competitor data and
              customer reviews into one beautiful command centre.
            </p>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
