import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind classes intelligently (dedupe + conflict resolution).
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a number into a compact form (e.g. 1.2K, 3.4M).
 */
export function formatCompact(n: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(n);
}

/**
 * Format a number with thousands separators.
 */
export function formatNumber(n: number): string {
  return new Intl.NumberFormat("en-US").format(n);
}

/**
 * Format a PKR currency value (e.g. "Rs 2,400").
 */
export function formatCurrency(n: number, opts: Intl.NumberFormatOptions = {}): string {
  return new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency: "PKR",
    maximumFractionDigits: 0,
    ...opts,
  }).format(n);
}

/**
 * Format an ISO date string into a human readable date.
 */
export function formatDate(
  date: string | Date,
  opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric", year: "numeric" }
): string {
  return new Intl.DateTimeFormat("en-US", opts).format(new Date(date));
}

/**
 * Format an ISO date string into a relative "time ago" label.
 */
export function timeAgo(date: string | Date): string {
  const d = new Date(date).getTime();
  const now = Date.now();
  const seconds = Math.round((now - d) / 1000);
  const minutes = Math.round(seconds / 60);
  const hours = Math.round(minutes / 60);
  const days = Math.round(hours / 24);
  if (seconds < 60) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return formatDate(date);
}

/**
 * Simulate async network latency for mock API calls.
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Returns initials (max 2 chars) from a name.
 */
export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

/**
 * Mask an API key, showing only the last 4 characters.
 */
export function maskApiKey(key: string): string {
  if (key.length <= 4) return "••••";
  return `••••••••••••••${key.slice(-4)}`;
}

/**
 * Build a paginated slice from a source array.
 */
export function paginate<T>(arr: T[], page: number, pageSize: number): T[] {
  const start = (page - 1) * pageSize;
  return arr.slice(start, start + pageSize);
}
