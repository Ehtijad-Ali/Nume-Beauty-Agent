import {
  LayoutDashboard,
  Package,
  BookOpen,
  Megaphone,
  UploadCloud,
  Swords,
  Star,
  Users,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  badge?: string;
}

export interface NavGroup {
  label?: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    items: [
      { label: "Dashboard", to: "/", icon: LayoutDashboard },
      { label: "Products", to: "/products", icon: Package },
      { label: "Knowledge Base", to: "/knowledge", icon: BookOpen },
      { label: "Campaigns", to: "/campaigns", icon: Megaphone },
      { label: "Uploads", to: "/uploads", icon: UploadCloud },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { label: "Competitors", to: "/competitors", icon: Swords },
      { label: "Customer Reviews", to: "/reviews", icon: Star },
    ],
  },
  {
    label: "Workspace",
    items: [
      { label: "Users", to: "/users", icon: Users },
      { label: "Settings", to: "/settings", icon: Settings },
    ],
  },
];
