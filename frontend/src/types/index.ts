// ============================================================
// Core domain types used across the NUMÉ AI Marketing Assistant
// ============================================================

export type ID = string;

export type Status = "active" | "draft" | "archived" | "paused";

export interface User {
  id: ID;
  name: string;
  email: string;
  role: string; // backend returns lowercase: admin | manager | editor | viewer
  avatarUrl?: string;
  status: "active" | "invited" | "suspended";
  lastActive: string; // ISO
  createdAt: string;
}

export interface Product {
  id: ID;
  name: string;
  sku: string;
  category: string;
  price: number;
  stock: number;
  status: Status;
  sales: number;
  createdAt: string;
  thumbnail?: string;
}

export interface KnowledgeDocument {
  id: ID;
  title: string;
  type: "pdf" | "docx" | "xlsx" | "csv" | "txt" | "url" | "md";
  size: number; // bytes
  status: "ready" | "processing" | "failed" | "queued";
  tags: string[];
  uploadedBy: string;
  uploadedAt: string;
  excerpt?: string;
}

export interface UploadRecord {
  id: ID;
  filename: string;
  mimeType: string;
  size: number;
  progress: number; // 0..100
  status: "uploading" | "completed" | "failed" | "queued";
  category: "Knowledge" | "Asset" | "Report" | "Other";
  uploadedAt: string;
  url?: string;
}

export interface Campaign {
  id: ID;
  name: string;
  channel: "Email" | "Social" | "Search" | "Display" | "Affiliate";
  status: Status;
  budget: number;
  spent: number;
  impressions: number;
  clicks: number;
  conversions: number;
  startDate: string;
  endDate: string;
}

export interface Competitor {
  id: ID;
  name: string;
  domain: string;
  logo?: string;
  shareOfVoice: number; // percentage 0..100
  traffic: number;
  keywords: number;
  ads: number;
  trend: number[]; // sparkline values
  change: number; // pct
}

export interface CustomerReview {
  id: ID;
  author: string;
  source: "Amazon" | "Trustpilot" | "Google" | "Yelp" | "Site";
  rating: number; // 1..5
  title: string;
  body: string;
  product: string;
  sentiment: "positive" | "neutral" | "negative";
  status: "new" | "responded" | "flagged";
  date: string;
}

export interface ActivityEvent {
  id: ID;
  type: "upload" | "campaign" | "product" | "user" | "review" | "knowledge" | "system";
  title: string;
  description: string;
  actor: string;
  timestamp: string;
}

export interface SystemService {
  name: string;
  status: "operational" | "degraded" | "outage";
  latency: number; // ms
  uptime: number; // pct
}

export interface AppSettings {
  companyName: string;
  brandName: string;
  timezone: string;
  language: string;
  theme: "light" | "dark" | "system";
  llmProvider: "openai" | "anthropic" | "gemini" | "cohere" | "mistral";
  openaiKey: string;
  anthropicKey: string;
  geminiKey: string;
  defaultModel: string;
}

export interface AuthUser {
  id: ID;
  name: string;
  email: string;
  role: User["role"];
  avatarUrl?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
}
