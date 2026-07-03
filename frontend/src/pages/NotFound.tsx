import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Home, ArrowLeft, Compass } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/common/Logo";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="text-center"
      >
        <Logo className="mx-auto justify-center" />

        <div className="relative mt-10">
          <p className="bg-brand-gradient bg-clip-text font-display text-[140px] font-bold leading-none text-transparent sm:text-[200px]">
            404
          </p>
          <div className="absolute inset-x-0 -bottom-2 flex justify-center">
            <Compass className="h-8 w-8 animate-pulse text-muted-foreground" />
          </div>
        </div>

        <h1 className="mt-6 font-display text-2xl font-semibold tracking-tight">Page not found</h1>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved. Let's get you back on track.
        </p>

        <div className="mt-8 flex items-center justify-center gap-3">
          <Button variant="outline" onClick={() => window.history.back()}>
            <ArrowLeft className="h-4 w-4" />
            Go back
          </Button>
          <Button variant="gradient" asChild>
            <Link to="/">
              <Home className="h-4 w-4" />
              Back to Dashboard
            </Link>
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
