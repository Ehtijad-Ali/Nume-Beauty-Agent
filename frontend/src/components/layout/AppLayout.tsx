import { Navigate, Outlet, useLocation } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useSidebar } from "@/context/SidebarContext";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export function AppLayout() {
  const { collapsed } = useSidebar();
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // While hydrating the user from /auth/me, show a centered spinner instead
  // of redirecting to /login (which would cause a flicker on reload).
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div className="min-h-screen bg-background">
        <Sidebar />
        <div
          className={cn(
            "flex min-h-screen flex-col transition-[padding] duration-300 ease-out",
            collapsed ? "lg:pl-[76px]" : "lg:pl-[260px]"
          )}
        >
          <Topbar />
          <main className="flex-1 px-4 py-6 lg:px-8 lg:py-8">
            <div className="page-enter mx-auto max-w-[1400px]">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </TooltipProvider>
  );
}
