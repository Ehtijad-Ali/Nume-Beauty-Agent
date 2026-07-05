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

export interface KnowledgeCategory {
  id: ID;
  name: string;
  slug: string;
  description?: string;
  color?: string;
  documentCount: number;
}

export interface KnowledgeDocument {
  id: ID;
  title: string;
  type: "pdf" | "docx" | "xlsx" | "csv" | "txt" | "url" | "md" | "image";
  size: number; // bytes
  status: "ready" | "processing" | "failed" | "queued";
  tags: string[];
  uploadedBy: string;
  uploadedAt: string;
  excerpt?: string;
  brand?: string;
  version: number;
  categoryId?: string | null;
  category?: KnowledgeCategory | null;
  originalFilename?: string;
  mimeType?: string;
  pageCount?: number | null;
  wordCount?: number | null;
  chunkCount: number;
  errorMessage?: string | null;
  lastIndexedAt?: string | null;
  metadata?: Record<string, unknown> | null;
  embeddingStatus: "none" | "pending" | "processing" | "completed" | "failed";
  embeddingError?: string | null;
  embeddingModel?: string | null;
  embeddedAt?: string | null;
  vectorCount: number;
}

export interface IndexStats {
  collection: string;
  indexStatus: string;
  vectorCount: number;
  chunkCount: number;
  documentCount: number;
  documentsByStatus: Record<string, number>;
  embeddingModel: string;
  embeddingDimension: number;
}

export interface SemanticSearchResult {
  chunkId: string;
  documentId: string;
  title?: string;
  content: string;
  score: number;
  chunkIndex: number;
  page?: number | null;
  docType?: string;
  categoryId?: string | null;
  categoryName?: string | null;
  brand?: string | null;
  tags: string[];
}

export interface SemanticSearchParams {
  query: string;
  topK?: number;
  scoreThreshold?: number;
  documentId?: string;
  categoryId?: string;
  brand?: string;
  docType?: string;
}

export interface DocumentChunk {
  id: ID;
  index: number;
  content: string;
  charCount: number;
  wordCount: number;
}

export interface DocumentVersion {
  id: ID;
  version: number;
  fileSize: number;
  originalFilename?: string;
  mimeType?: string;
  changeNote?: string;
  uploadedBy?: string;
  createdAt: string;
}

// ---------- RAG engine (Phase 2.3) ----------

export interface RagRetrievedChunk extends SemanticSearchResult {
  rankScore?: number | null;
  priority: boolean;
  citation?: number | null;
}

export interface RagSource {
  documentId: string;
  title?: string | null;
  docType?: string | null;
  categoryName?: string | null;
  brand?: string | null;
  citations: number[];
  chunksUsed: number;
  bestScore: number;
}

export interface RagUsage {
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
}

export interface RagTimings {
  retrievalMs: number;
  llmMs: number;
  totalMs: number;
}

export interface RagFinalPrompt {
  system: string;
  messages: { role: string; content: string }[];
}

export interface RagQueryResponse {
  conversationId: string;
  messageId: string;
  answer: string;
  sources: RagSource[];
  retrievedChunks: RagRetrievedChunk[];
  finalPrompt: RagFinalPrompt;
  provider: string;
  model?: string | null;
  usage: RagUsage;
  timings: RagTimings;
}

export interface RagQueryParams {
  message: string;
  conversationId?: string;
  topK?: number;
  scoreThreshold?: number;
  categoryId?: string;
  brand?: string;
  docType?: string;
  allowGeneralKnowledge?: boolean;
}

export interface RagConversation {
  id: ID;
  title: string;
  messageCount: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  lastMessageAt?: string | null;
  createdAt: string;
}

export interface RagChatMessage {
  id: ID;
  conversationId: string;
  role: "user" | "assistant";
  content: string;
  provider?: string | null;
  model?: string | null;
  inputTokens: number;
  outputTokens: number;
  retrievalMs?: number | null;
  llmMs?: number | null;
  totalMs?: number | null;
  sources?: RagSource[] | null;
  createdAt: string;
}

export interface RagStats {
  conversationCount: number;
  queryCount: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalTokens: number;
  avgTotalMs?: number | null;
  avgRetrievalMs?: number | null;
  avgLlmMs?: number | null;
  byModel: { provider: string; model?: string | null; queries: number; inputTokens: number; outputTokens: number }[];
}

export interface RagConfig {
  llmProvider: string;
  llmModel: string;
  llmConfigured: boolean;
  embeddingModel: string;
  topK: number;
  scoreThreshold: number;
  maxContextChars: number;
  maxChunksPerDocument: number;
  historyMessages: number;
  allowGeneralKnowledge: boolean;
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
  organicTraffic: number;
  paidTraffic: number;
  organicKeywords: number;
  paidKeywords: number;
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
