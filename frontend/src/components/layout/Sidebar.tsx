import { NavLink, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronsLeft, LogOut, Moon, Sun, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import { Logo } from "@/components/common/Logo";
import { useSidebar } from "@/context/SidebarContext";
import { useTheme } from "@/context/ThemeProvider";
import { useAuth } from "@/context/AuthContext";
import { NAV_GROUPS } from "@/lib/nav";
import { cn, getInitials } from "@/lib/utils";

export function Sidebar() {
  const { collapsed, toggleCollapsed, mobileOpen, setMobileOpen } = useSidebar();
  const { resolvedTheme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-[hsl(340_25%_5%/0.65)] backdrop-blur-sm lg:hidden"
            onClick={() => setMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col border-r border-sidebar-border bg-sidebar transition-[width,transform] duration-300 ease-out lg:translate-x-0",
          collapsed ? "w-[4.75rem]" : "w-[16.25rem]",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Header / Logo */}
        <div className="flex h-16 items-center justify-between px-4">
          <Logo collapsed={collapsed} />
          <button
            onClick={() => setMobileOpen(false)}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted lg:hidden"
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <Separator />

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <div className="space-y-6">
            {NAV_GROUPS.map((group, gi) => (
              <div key={gi} className="space-y-1">
                {group.label && !collapsed && (
                  <p className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                    {group.label}
                  </p>
                )}
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const content = (
                    <NavLink
                      to={item.to}
                      end={item.to === "/"}
                      onClick={() => setMobileOpen(false)}
                      className={({ isActive }) =>
                        cn(
                          "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
                          collapsed && "justify-center px-0",
                          isActive
                            ? "bg-primary/10 text-primary"
                            : "text-muted-foreground hover:bg-accent hover:text-foreground"
                        )
                      }
                    >
                      {({ isActive }) => (
                        <>
                          {isActive && (
                            <motion.span
                              layoutId="sidebar-active"
                              className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-primary"
                              transition={{ type: "spring", stiffness: 350, damping: 30 }}
                            />
                          )}
                          <Icon
                            className={cn(
                              "h-[18px] w-[18px] shrink-0 transition-colors",
                              isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                            )}
                          />
                          {!collapsed && <span className="truncate">{item.label}</span>}
                          {!collapsed && item.badge && (
                            <span className="ml-auto rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-semibold text-primary">
                              {item.badge}
                            </span>
                          )}
                        </>
                      )}
                    </NavLink>
                  );

                  if (collapsed) {
                    return (
                      <Tooltip key={item.to} delayDuration={0}>
                        <TooltipTrigger asChild>
                          <div>{content}</div>
                        </TooltipTrigger>
                        <TooltipContent side="right" sideOffset={8}>
                          {item.label}
                        </TooltipContent>
                      </Tooltip>
                    );
                  }
                  return <div key={item.to}>{content}</div>;
                })}
              </div>
            ))}
          </div>
        </nav>

        <Separator />

        {/* Footer: theme + user */}
        <div className="space-y-2 p-3">
          <Tooltip delayDuration={0}>
            <TooltipTrigger asChild>
              <button
                onClick={toggleTheme}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
                  collapsed && "justify-center px-0"
                )}
              >
                {resolvedTheme === "dark" ? (
                  <Sun className="h-[18px] w-[18px]" />
                ) : (
                  <Moon className="h-[18px] w-[18px]" />
                )}
                {!collapsed && (
                  <span>{resolvedTheme === "dark" ? "Light Mode" : "Dark Mode"}</span>
                )}
              </button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent side="right">Toggle theme</TooltipContent>
            )}
          </Tooltip>

          <div
            className={cn(
              "flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-accent",
              collapsed && "justify-center"
            )}
          >
            <Avatar className="h-8 w-8">
              <AvatarFallback>{user ? getInitials(user.name) : "?"}</AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{user?.name}</p>
                <p className="truncate text-xs text-muted-foreground">{user?.role}</p>
              </div>
            )}
            {!collapsed && (
              <button
                onClick={handleLogout}
                className="rounded-md p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                aria-label="Logout"
              >
                <LogOut className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>

        {/* Collapse toggle (desktop) */}
        <button
          onClick={toggleCollapsed}
          className="absolute -right-3 top-20 hidden h-6 w-6 items-center justify-center rounded-full border border-border bg-card text-muted-foreground shadow-soft transition-colors hover:text-foreground lg:flex"
          aria-label="Toggle sidebar"
        >
          {collapsed ? <ChevronLeft className="h-3.5 w-3.5 rotate-180" /> : <ChevronsLeft className="h-3.5 w-3.5" />}
        </button>
      </aside>
    </>
  );
}
