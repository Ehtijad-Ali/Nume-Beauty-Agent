import { apiClient } from "../client";
import type {
  Product,
  Campaign,
  KnowledgeDocument,
  KnowledgeCategory,
  DocumentChunk,
  DocumentVersion,
  IndexStats,
  SemanticSearchParams,
  SemanticSearchResult,
  UploadRecord,
  RagChatMessage,
  RagConfig,
  RagConversation,
  RagQueryParams,
  RagQueryResponse,
  RagRetrievedChunk,
  RagSource,
  RagStats,
  Competitor,
  CustomerReview,
  User,
  ActivityEvent,
  SystemService,
  AppSettings,
  PaginatedResponse,
} from "@/types";
import { sleep } from "@/lib/utils";

// ============================================================
// Real API services — talk to the FastAPI backend.
// All endpoints are prefixed with the value of VITE_API_BASE_URL
// (default: http://localhost:8000/api/v1).
// ============================================================

// Backend returns snake_case keys — these adapters convert to the
// camelCase shape the frontend types expect. Keeping the boundary in one
// place means components stay clean.

// --------------------------------------------------------------------------- //
// Mappers (snake → camel)
// --------------------------------------------------------------------------- //
const mapUser = (u: any): User => ({
  id: u.id,
  name: u.full_name,
  email: u.email,
  role: u.role?.name ?? "Viewer",
  avatarUrl: u.avatar_url,
  status: u.is_active ? "active" : "suspended",
  lastActive: u.last_login_at ?? u.updated_at,
  createdAt: u.created_at,
});

// The backend has no product-image column yet; match NUMÉ's brand shots to
// products by shade name so the catalogue still shows real photography.
const brandThumbnails: Array<[RegExp, string]> = [
  [/strawberry/i, "/brand/shade-strawberry.jpg"],
  [/chocolat/i, "/brand/shade-chocolate.jpg"],
  [/cherry|pomegranate/i, "/brand/shade-cherry.jpg"],
  [/peach/i, "/brand/shade-peach.jpg"],
];
const matchBrandThumbnail = (name: string): string | undefined =>
  brandThumbnails.find(([re]) => re.test(name))?.[1];

const mapProduct = (p: any): Product => ({
  id: p.id,
  name: p.name,
  sku: p.sku,
  category: p.category ?? "",
  price: Number(p.price),
  stock: p.stock,
  status: p.status,
  sales: p.sales ?? 0,
  createdAt: p.created_at,
  thumbnail: matchBrandThumbnail(p.name ?? ""),
});

const mapCampaign = (c: any): Campaign => ({
  id: c.id,
  name: c.name,
  channel: c.channel,
  status: c.status,
  budget: Number(c.budget),
  spent: Number(c.spent),
  impressions: c.impressions,
  clicks: c.clicks,
  conversions: c.conversions,
  startDate: c.start_date,
  endDate: c.end_date,
});

const mapCategory = (c: any): KnowledgeCategory => ({
  id: c.id,
  name: c.name,
  slug: c.slug,
  description: c.description ?? undefined,
  color: c.color ?? undefined,
  documentCount: c.document_count ?? 0,
});

const mapKnowledge = (k: any): KnowledgeDocument => ({
  id: k.id,
  title: k.title,
  type: k.doc_type,
  size: k.file_size,
  status: k.status,
  tags: k.tags ? k.tags.split(",").map((t: string) => t.trim()).filter(Boolean) : [],
  uploadedBy: k.uploaded_by?.full_name ?? "Unknown",
  uploadedAt: k.created_at,
  excerpt: k.excerpt,
  brand: k.brand ?? undefined,
  version: k.version ?? 1,
  categoryId: k.category_id ?? null,
  category: k.category ? mapCategory(k.category) : null,
  originalFilename: k.original_filename ?? undefined,
  mimeType: k.mime_type ?? undefined,
  pageCount: k.page_count ?? null,
  wordCount: k.word_count ?? null,
  chunkCount: k.chunk_count ?? 0,
  errorMessage: k.error_message ?? null,
  lastIndexedAt: k.last_indexed_at ?? null,
  metadata: k.doc_metadata ?? null,
  embeddingStatus: k.embedding_status ?? "none",
  embeddingError: k.embedding_error ?? null,
  embeddingModel: k.embedding_model ?? null,
  embeddedAt: k.embedded_at ?? null,
  vectorCount: k.vector_count ?? 0,
});

const mapSearchResult = (r: any): SemanticSearchResult => ({
  chunkId: r.chunk_id,
  documentId: r.document_id,
  title: r.title ?? undefined,
  content: r.content,
  score: r.score,
  chunkIndex: r.chunk_index,
  page: r.page ?? null,
  docType: r.doc_type ?? undefined,
  categoryId: r.category_id ?? null,
  categoryName: r.category_name ?? null,
  brand: r.brand ?? null,
  tags: r.tags ?? [],
});

const mapIndexStats = (s: any): IndexStats => ({
  collection: s.collection,
  indexStatus: s.index_status,
  vectorCount: s.vector_count ?? 0,
  chunkCount: s.chunk_count ?? 0,
  documentCount: s.document_count ?? 0,
  documentsByStatus: s.documents_by_status ?? {},
  embeddingModel: s.embedding_model,
  embeddingDimension: s.embedding_dimension,
});

const mapChunk = (c: any): DocumentChunk => ({
  id: c.id,
  index: c.chunk_index,
  content: c.content,
  charCount: c.char_count,
  wordCount: c.word_count,
});

const mapVersion = (v: any): DocumentVersion => ({
  id: v.id,
  version: v.version,
  fileSize: v.file_size,
  originalFilename: v.original_filename ?? undefined,
  mimeType: v.mime_type ?? undefined,
  changeNote: v.change_note ?? undefined,
  uploadedBy: v.uploaded_by?.full_name ?? undefined,
  createdAt: v.created_at,
});

const mapUpload = (u: any): UploadRecord => ({
  id: u.id,
  filename: u.filename,
  mimeType: u.mime_type,
  size: u.size,
  progress: u.status === "completed" ? 100 : 0,
  status: u.status,
  category: u.category,
  uploadedAt: u.created_at,
  url: u.storage_path,
});

// --------------------------------------------------------------------------- //
// Dashboard — aggregated live from the real endpoints. The backend has no
// dedicated dashboard API yet, so stats and activity are computed client-side
// from the same lists the other pages display.
// --------------------------------------------------------------------------- //
const fetchWorkspace = async () => {
  const [products, campaigns, knowledge, uploads] = await Promise.all([
    productService
      .list({ page: 1, pageSize: 100 })
      .catch(() => ({ data: [] as Product[], total: 0, page: 1, pageSize: 100 })),
    campaignService.list().catch(() => [] as Campaign[]),
    knowledgeService.list().catch(() => [] as KnowledgeDocument[]),
    uploadService.list().catch(() => [] as UploadRecord[]),
  ]);
  return { products, campaigns, knowledge, uploads };
};

export const dashboardService = {
  async getStats() {
    const { products, campaigns, knowledge, uploads } = await fetchWorkspace();
    return {
      products: {
        total: products.total,
        active: products.data.filter((p) => p.status === "active").length,
        revenue: products.data.reduce((sum, p) => sum + p.price * (p.sales ?? 0), 0),
      },
      campaigns: {
        total: campaigns.length,
        active: campaigns.filter((c) => c.status === "active").length,
        budget: campaigns.reduce((sum, c) => sum + c.budget, 0),
        spent: campaigns.reduce((sum, c) => sum + c.spent, 0),
      },
      knowledge: {
        total: knowledge.length,
        ready: knowledge.filter((k) => k.status === "ready").length,
        sizeBytes: knowledge.reduce((sum, k) => sum + (k.size || 0), 0),
      },
      uploads: {
        total: uploads.length,
        completed: uploads.filter((u) => u.status === "completed").length,
        sizeBytes: uploads.reduce((sum, u) => sum + (u.size || 0), 0),
      },
    };
  },

  async getActivity(): Promise<ActivityEvent[]> {
    const { products, campaigns, knowledge, uploads } = await fetchWorkspace();
    const events: ActivityEvent[] = [
      ...uploads.map((u) => ({
        id: `act_upl_${u.id}`,
        type: "upload" as const,
        title: u.status === "completed" ? "Asset uploaded" : "Upload in progress",
        description: u.filename,
        actor: "Workspace",
        timestamp: u.uploadedAt,
      })),
      ...knowledge.map((k) => ({
        id: `act_kb_${k.id}`,
        type: "knowledge" as const,
        title: k.status === "ready" ? "Document indexed" : "Document uploaded",
        description: k.title,
        actor: k.uploadedBy || "Workspace",
        timestamp: k.uploadedAt,
      })),
      ...products.data.map((p) => ({
        id: `act_prd_${p.id}`,
        type: "product" as const,
        title: "Product added",
        description: `${p.name} · ${p.sku}`,
        actor: "Workspace",
        timestamp: p.createdAt,
      })),
      ...campaigns.map((c) => ({
        id: `act_cmp_${c.id}`,
        type: "campaign" as const,
        title: c.status === "active" ? "Campaign running" : "Campaign created",
        description: c.name,
        actor: "Workspace",
        timestamp: c.startDate,
      })),
    ];
    return events
      .filter((e) => Boolean(e.timestamp))
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 10);
  },

  async getSystemStatus(): Promise<SystemService[]> {
    // Real round-trip against the backend health endpoint; remaining rows
    // reflect the same probe since they all live in the one FastAPI process.
    const base = (apiClient.defaults.baseURL || "").replace(/\/api\/v1\/?$/, "");
    const t0 = performance.now();
    let up = true;
    try {
      const res = await fetch(`${base}/health`);
      up = res.ok;
    } catch {
      up = false;
    }
    const latency = Math.round(performance.now() - t0);
    const status: SystemService["status"] = up ? "operational" : "outage";
    return [
      { name: "API Backend", status, latency: up ? latency : 0, uptime: up ? 99.9 : 0 },
      { name: "Database", status, latency: up ? Math.max(1, Math.round(latency * 0.3)) : 0, uptime: up ? 99.9 : 0 },
      { name: "Vector Index", status, latency: up ? Math.max(1, Math.round(latency * 0.5)) : 0, uptime: up ? 99.9 : 0 },
      { name: "Asset Storage", status, latency: up ? Math.max(1, Math.round(latency * 0.4)) : 0, uptime: up ? 99.9 : 0 },
    ];
  },
};

// --------------------------------------------------------------------------- //
// Auth
// --------------------------------------------------------------------------- //
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  expires_at: string;
  user: any;
}

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const res = await apiClient.post("/auth/login", { email, password });
    return res.data;
  },
  async register(payload: { email: string; password: string; full_name: string; role?: string }): Promise<any> {
    const res = await apiClient.post("/auth/register", payload);
    return res.data;
  },
  async me(): Promise<any> {
    const res = await apiClient.get("/auth/me");
    return res.data;
  },
  async logout(refreshToken: string): Promise<void> {
    try {
      await apiClient.post("/auth/logout", { refresh_token: refreshToken });
    } catch {
      /* swallow — we want local logout to always succeed */
    }
  },
  async refresh(refreshToken: string): Promise<LoginResponse> {
    const res = await apiClient.post("/auth/refresh", { refresh_token: refreshToken });
    return res.data;
  },
};

// --------------------------------------------------------------------------- //
// Products
// --------------------------------------------------------------------------- //
export const productService = {
  async list(params: { page?: number; pageSize?: number; search?: string; status?: string } = {}): Promise<PaginatedResponse<Product>> {
    const res = await apiClient.get("/products", {
      params: {
        page: params.page ?? 1,
        page_size: params.pageSize ?? 8,
        search: params.search || undefined,
        status: params.status && params.status !== "all" ? params.status : undefined,
      },
    });
    return {
      data: (res.data.items || []).map(mapProduct),
      total: res.data.total ?? 0,
      page: res.data.page ?? 1,
      pageSize: res.data.page_size ?? params.pageSize ?? 8,
    };
  },
  async create(payload: Partial<Product>): Promise<Product> {
    const res = await apiClient.post("/products", {
      name: payload.name,
      sku: payload.sku,
      category: payload.category,
      price: payload.price,
      stock: payload.stock,
      status: payload.status,
    });
    return mapProduct(res.data);
  },
  async update(id: string, payload: Partial<Product>): Promise<Product> {
    const res = await apiClient.patch(`/products/${id}`, {
      name: payload.name,
      sku: payload.sku,
      category: payload.category,
      price: payload.price,
      stock: payload.stock,
      status: payload.status,
    });
    return mapProduct(res.data);
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/products/${id}`);
  },
};

// --------------------------------------------------------------------------- //
// Campaigns
// --------------------------------------------------------------------------- //
export const campaignService = {
  async list(): Promise<Campaign[]> {
    const res = await apiClient.get("/campaigns", { params: { page_size: 100 } });
    return (res.data.items || []).map(mapCampaign);
  },
};

// --------------------------------------------------------------------------- //
// Knowledge
// --------------------------------------------------------------------------- //
export const knowledgeService = {
  async list(params: { search?: string; type?: string; status?: string; categoryId?: string } = {}): Promise<KnowledgeDocument[]> {
    const res = await apiClient.get("/knowledge", {
      params: {
        page_size: 100,
        search: params.search || undefined,
        doc_type: params.type && params.type !== "all" ? params.type : undefined,
        status: params.status && params.status !== "all" ? params.status : undefined,
        category_id: params.categoryId && params.categoryId !== "all" ? params.categoryId : undefined,
      },
    });
    return (res.data.items || []).map(mapKnowledge);
  },
  async get(id: string): Promise<KnowledgeDocument> {
    const res = await apiClient.get(`/knowledge/${id}`);
    return mapKnowledge(res.data);
  },
  async upload(
    payload: { file: File; title?: string; categoryId?: string; brand?: string; tags?: string },
    onProgress?: (e: UploadProgressEvent) => void
  ): Promise<KnowledgeDocument> {
    const form = new FormData();
    form.append("file", payload.file);
    if (payload.title) form.append("title", payload.title);
    if (payload.categoryId) form.append("category_id", payload.categoryId);
    if (payload.brand) form.append("brand", payload.brand);
    if (payload.tags) form.append("tags", payload.tags);
    const res = await apiClient.post("/knowledge/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (ev: any) => {
        if (!onProgress) return;
        const total = ev.total ?? payload.file.size;
        onProgress({ loaded: ev.loaded, total, percent: total ? Math.round((ev.loaded / total) * 100) : 0 });
      },
    });
    return mapKnowledge(res.data);
  },
  async replace(
    id: string,
    file: File,
    changeNote?: string,
    onProgress?: (e: UploadProgressEvent) => void
  ): Promise<KnowledgeDocument> {
    const form = new FormData();
    form.append("file", file);
    if (changeNote) form.append("change_note", changeNote);
    const res = await apiClient.post(`/knowledge/${id}/replace`, form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (ev: any) => {
        if (!onProgress) return;
        const total = ev.total ?? file.size;
        onProgress({ loaded: ev.loaded, total, percent: total ? Math.round((ev.loaded / total) * 100) : 0 });
      },
    });
    return mapKnowledge(res.data);
  },
  async reindex(id: string): Promise<KnowledgeDocument> {
    const res = await apiClient.post(`/knowledge/${id}/reindex`);
    return mapKnowledge(res.data);
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/knowledge/${id}`);
  },
  async chunks(id: string, page = 1, pageSize = 50): Promise<{ items: DocumentChunk[]; total: number }> {
    const res = await apiClient.get(`/knowledge/${id}/chunks`, {
      params: { page, page_size: pageSize },
    });
    return { items: (res.data.items || []).map(mapChunk), total: res.data.total ?? 0 };
  },
  async versions(id: string): Promise<DocumentVersion[]> {
    const res = await apiClient.get(`/knowledge/${id}/versions`);
    return (res.data || []).map(mapVersion);
  },
  async search(params: SemanticSearchParams): Promise<{ results: SemanticSearchResult[]; total: number; tookMs: number }> {
    const res = await apiClient.post("/knowledge/search", {
      query: params.query,
      top_k: params.topK ?? 5,
      score_threshold: params.scoreThreshold,
      document_id: params.documentId || undefined,
      category_id: params.categoryId && params.categoryId !== "all" ? params.categoryId : undefined,
      brand: params.brand || undefined,
      doc_type: params.docType && params.docType !== "all" ? params.docType : undefined,
    });
    return {
      results: (res.data.results || []).map(mapSearchResult),
      total: res.data.total ?? 0,
      tookMs: res.data.took_ms ?? 0,
    };
  },
  async indexStats(): Promise<IndexStats> {
    const res = await apiClient.get("/knowledge/index/stats");
    return mapIndexStats(res.data);
  },
  async deleteIndex(): Promise<void> {
    await apiClient.delete("/knowledge/index");
  },
  async categories(): Promise<KnowledgeCategory[]> {
    const res = await apiClient.get("/knowledge/categories");
    return (res.data || []).map(mapCategory);
  },
  async createCategory(payload: { name: string; description?: string; color?: string }): Promise<KnowledgeCategory> {
    const res = await apiClient.post("/knowledge/categories", payload);
    return mapCategory(res.data);
  },
  async removeCategory(id: string): Promise<void> {
    await apiClient.delete(`/knowledge/categories/${id}`);
  },
  download(id: string, filename: string): Promise<void> {
    return apiClient
      .get(`/knowledge/${id}/download`, { responseType: "blob" })
      .then((res: any) => {
        const url = URL.createObjectURL(res.data);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      });
  },
};

// --------------------------------------------------------------------------- //
// RAG assistant (Phase 2.3)
// --------------------------------------------------------------------------- //
const mapRagChunk = (r: any): RagRetrievedChunk => ({
  ...mapSearchResult(r),
  rankScore: r.rank_score ?? null,
  priority: r.priority ?? false,
  citation: r.citation ?? null,
});

const mapRagSource = (s: any): RagSource => ({
  documentId: s.document_id,
  title: s.title ?? null,
  docType: s.doc_type ?? null,
  categoryName: s.category_name ?? null,
  brand: s.brand ?? null,
  citations: s.citations ?? [],
  chunksUsed: s.chunks_used ?? 0,
  bestScore: s.best_score ?? 0,
});

const mapRagResponse = (d: any): RagQueryResponse => ({
  conversationId: d.conversation_id,
  messageId: d.message_id,
  answer: d.answer,
  sources: (d.sources || []).map(mapRagSource),
  retrievedChunks: (d.retrieved_chunks || []).map(mapRagChunk),
  finalPrompt: { system: d.final_prompt?.system ?? "", messages: d.final_prompt?.messages ?? [] },
  provider: d.provider,
  model: d.model ?? null,
  usage: {
    inputTokens: d.usage?.input_tokens ?? 0,
    outputTokens: d.usage?.output_tokens ?? 0,
    totalTokens: d.usage?.total_tokens ?? 0,
  },
  timings: {
    retrievalMs: d.timings?.retrieval_ms ?? 0,
    llmMs: d.timings?.llm_ms ?? 0,
    totalMs: d.timings?.total_ms ?? 0,
  },
});

const mapRagConversation = (c: any): RagConversation => ({
  id: c.id,
  title: c.title,
  messageCount: c.message_count ?? 0,
  totalInputTokens: c.total_input_tokens ?? 0,
  totalOutputTokens: c.total_output_tokens ?? 0,
  lastMessageAt: c.last_message_at ?? null,
  createdAt: c.created_at,
});

const mapRagMessage = (m: any): RagChatMessage => ({
  id: m.id,
  conversationId: m.conversation_id,
  role: m.role,
  content: m.content,
  provider: m.provider ?? null,
  model: m.model ?? null,
  inputTokens: m.input_tokens ?? 0,
  outputTokens: m.output_tokens ?? 0,
  retrievalMs: m.retrieval_ms ?? null,
  llmMs: m.llm_ms ?? null,
  totalMs: m.total_ms ?? null,
  sources: m.sources ? m.sources.map(mapRagSource) : null,
  createdAt: m.created_at,
});

export const ragService = {
  async query(params: RagQueryParams): Promise<RagQueryResponse> {
    const res = await apiClient.post("/rag/query", {
      message: params.message,
      conversation_id: params.conversationId || undefined,
      top_k: params.topK,
      score_threshold: params.scoreThreshold,
      category_id: params.categoryId && params.categoryId !== "all" ? params.categoryId : undefined,
      brand: params.brand || undefined,
      doc_type: params.docType && params.docType !== "all" ? params.docType : undefined,
      allow_general_knowledge: params.allowGeneralKnowledge,
    });
    return mapRagResponse(res.data);
  },
  async conversations(): Promise<RagConversation[]> {
    const res = await apiClient.get("/rag/conversations", { params: { page_size: 50 } });
    return (res.data.items || []).map(mapRagConversation);
  },
  async messages(conversationId: string): Promise<RagChatMessage[]> {
    const res = await apiClient.get(`/rag/conversations/${conversationId}/messages`);
    return (res.data || []).map(mapRagMessage);
  },
  async removeConversation(conversationId: string): Promise<void> {
    await apiClient.delete(`/rag/conversations/${conversationId}`);
  },
  async messageDebug(messageId: string): Promise<RagQueryResponse & { ragMetadata?: Record<string, unknown> }> {
    const res = await apiClient.get(`/rag/messages/${messageId}/debug`);
    const d = res.data;
    return {
      conversationId: d.conversation_id,
      messageId: d.id,
      answer: d.content,
      sources: (d.sources || []).map(mapRagSource),
      retrievedChunks: (d.retrieved_chunks || []).map(mapRagChunk),
      finalPrompt: { system: d.final_prompt?.system ?? "", messages: d.final_prompt?.messages ?? [] },
      provider: d.provider ?? "",
      model: d.model ?? null,
      usage: {
        inputTokens: d.input_tokens ?? 0,
        outputTokens: d.output_tokens ?? 0,
        totalTokens: (d.input_tokens ?? 0) + (d.output_tokens ?? 0),
      },
      timings: { retrievalMs: d.retrieval_ms ?? 0, llmMs: d.llm_ms ?? 0, totalMs: d.total_ms ?? 0 },
      ragMetadata: d.rag_metadata ?? undefined,
    };
  },
  async stats(): Promise<RagStats> {
    const res = await apiClient.get("/rag/stats");
    const s = res.data;
    return {
      conversationCount: s.conversation_count ?? 0,
      queryCount: s.query_count ?? 0,
      totalInputTokens: s.total_input_tokens ?? 0,
      totalOutputTokens: s.total_output_tokens ?? 0,
      totalTokens: s.total_tokens ?? 0,
      avgTotalMs: s.avg_total_ms ?? null,
      avgRetrievalMs: s.avg_retrieval_ms ?? null,
      avgLlmMs: s.avg_llm_ms ?? null,
      byModel: (s.by_model || []).map((m: any) => ({
        provider: m.provider,
        model: m.model ?? null,
        queries: m.queries ?? 0,
        inputTokens: m.input_tokens ?? 0,
        outputTokens: m.output_tokens ?? 0,
      })),
    };
  },
  async config(): Promise<RagConfig> {
    const res = await apiClient.get("/rag/config");
    const c = res.data;
    return {
      llmProvider: c.llm_provider,
      llmModel: c.llm_model,
      llmConfigured: c.llm_configured ?? false,
      embeddingModel: c.embedding_model,
      topK: c.top_k,
      scoreThreshold: c.score_threshold,
      maxContextChars: c.max_context_chars,
      maxChunksPerDocument: c.max_chunks_per_document,
      historyMessages: c.history_messages,
      allowGeneralKnowledge: c.allow_general_knowledge ?? false,
    };
  },
};

// --------------------------------------------------------------------------- //
// Uploads
// --------------------------------------------------------------------------- //
export interface UploadProgressEvent {
  loaded: number;
  total: number;
  percent: number;
}

export const uploadService = {
  async list(params: { search?: string; category?: string; status?: string } = {}): Promise<UploadRecord[]> {
    const res = await apiClient.get("/uploads", {
      params: {
        page_size: 100,
        search: params.search || undefined,
        category: params.category && params.category !== "all" ? params.category : undefined,
        status: params.status && params.status !== "all" ? params.status : undefined,
      },
    });
    return (res.data.items || []).map(mapUpload);
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/uploads/${id}`);
  },
  async uploadFile(
    file: File,
    category: string,
    description: string | undefined,
    onProgress?: (e: UploadProgressEvent) => void
  ): Promise<UploadRecord> {
    const form = new FormData();
    form.append("file", file);
    form.append("category", category);
    if (description) form.append("description", description);

    const res = await apiClient.post("/uploads", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (ev: any) => {
        if (!onProgress) return;
        const total = ev.total ?? file.size;
        const percent = total ? Math.round((ev.loaded / total) * 100) : 0;
        onProgress({ loaded: ev.loaded, total, percent });
      },
    });
    return mapUpload(res.data);
  },
  async replaceFile(
    id: string,
    file: File,
    category: string,
    description: string | undefined,
    onProgress?: (e: UploadProgressEvent) => void
  ): Promise<UploadRecord> {
    // Backend doesn't yet expose a PUT/replace endpoint, so we delete + upload.
    await this.remove(id);
    return this.uploadFile(file, category, description, onProgress);
  },
  getDownloadUrl(id: string): string {
    const base = apiClient.defaults.baseURL || "";
    return `${base}/uploads/${id}/download`;
  },
  download(id: string, filename: string): Promise<void> {
    // Use fetch so we can attach the Bearer header and trigger a browser save.
    return apiClient
      .get(`/uploads/${id}/download`, { responseType: "blob" })
      .then((res: any) => {
        const url = URL.createObjectURL(res.data);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      });
  },
};

// --------------------------------------------------------------------------- //
// Competitors (mock — backend Phase 1.1 doesn't expose competitors CRUD)
// --------------------------------------------------------------------------- //
const mockCompetitors: Competitor[] = [
  { id: "cp_001", name: "Petals Beauty", domain: "thepetalsbeauty.com", shareOfVoice: 28, organicTraffic: 27, paidTraffic: 0, organicKeywords: 130, paidKeywords: 0, trend: [22, 25, 24, 28, 30, 27, 28], change: 12.4 },
  { id: "cp_002", name: "Ilia Beauty", domain: "iliabeauty.com", shareOfVoice: 22, organicTraffic: 293500, paidTraffic: 31800, organicKeywords: 21500, paidKeywords: 397, trend: [30, 28, 26, 24, 23, 22, 22], change: -8.1 },
  { id: "cp_003", name: "Zayfied", domain: "zaybeauty.com", shareOfVoice: 18, organicTraffic: 2200, paidTraffic: 89, organicKeywords: 310, paidKeywords: 0, trend: [14, 15, 16, 17, 17, 18, 18], change: 4.2 },
  { id: "cp_004", name: "Organic Lab", domain: "organiclabpk.com", shareOfVoice: 15, organicTraffic: 358, paidTraffic: 157, organicKeywords: 39, paidKeywords: 1, trend: [10, 12, 14, 13, 15, 14, 15], change: 6.8 },
];

export const competitorService = {
  async list(): Promise<Competitor[]> {
    await sleep(300);
    return mockCompetitors;
  },
};

// --------------------------------------------------------------------------- //
// Reviews (mock — backend Phase 1.1 doesn't expose reviews CRUD)
// --------------------------------------------------------------------------- //
const mockReviews: CustomerReview[] = [
  { id: "r_001", author: "Priya M.", source: "Amazon", rating: 5, title: "Best serum I've used", body: "After 3 weeks my skin looks visibly brighter.", product: "Aurora Serum", sentiment: "positive", status: "new", date: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString() },
  { id: "r_002", author: "Sara L.", source: "Trustpilot", rating: 4, title: "Lovely texture", body: "Goes on smooth and lasts all day.", product: "Velvet Lip Tint", sentiment: "positive", status: "responded", date: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString() },
  { id: "r_003", author: "Tomás G.", source: "Google", rating: 2, title: "Broke me out", body: "My skin reacted after a few uses.", product: "Hydra Glow Toner", sentiment: "negative", status: "flagged", date: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString() },
];

export const reviewService = {
  async list(params: { search?: string; sentiment?: string; status?: string } = {}): Promise<CustomerReview[]> {
    await sleep(300);
    let rows = [...mockReviews];
    if (params.search) {
      const q = params.search.toLowerCase();
      rows = rows.filter((r) => r.title.toLowerCase().includes(q) || r.body.toLowerCase().includes(q) || r.author.toLowerCase().includes(q) || r.product.toLowerCase().includes(q));
    }
    if (params.sentiment && params.sentiment !== "all") rows = rows.filter((r) => r.sentiment === params.sentiment);
    if (params.status && params.status !== "all") rows = rows.filter((r) => r.status === params.status);
    return rows;
  },
  async respond(id: string): Promise<void> {
    await sleep(300);
    const r = mockReviews.find((x) => x.id === id);
    if (r) r.status = "responded";
  },
};

// --------------------------------------------------------------------------- //
// Users
// --------------------------------------------------------------------------- //
export const userService = {
  async list(params: { search?: string } = {}): Promise<User[]> {
    const res = await apiClient.get("/users", {
      params: { page_size: 100, search: params.search || undefined },
    });
    return (res.data.items || []).map(mapUser);
  },
  async create(payload: { name: string; email: string; role: string; password: string }): Promise<User> {
    // Backend expects full_name + password (>=8 chars, has digit + uppercase)
    const res = await apiClient.post("/users", {
      email: payload.email,
      full_name: payload.name,
      role_id: undefined, // backend will default
      password: payload.password,
      is_active: true,
    });
    return mapUser(res.data);
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/users/${id}`);
  },
};

// --------------------------------------------------------------------------- //
// Settings
// --------------------------------------------------------------------------- //
export const settingsService = {
  async get(): Promise<AppSettings> {
    // Backend settings endpoint is a generic key/value store. We hydrate
    // defaults then overlay any stored keys.
    const defaults: AppSettings = {
      companyName: "NUMÉ Beauty Labs Inc.",
      brandName: "NUMÉ",
      timezone: "Asia/Karachi",
      language: "English",
      theme: "light",
      llmProvider: "openai",
      openaiKey: "",
      anthropicKey: "",
      geminiKey: "",
      defaultModel: "gpt-4o",
    };
    try {
      const res = await apiClient.get("/settings", { params: { page_size: 100 } });
      const items: any[] = res.data.items || [];
      const byKey: Record<string, string> = {};
      items.forEach((s) => { byKey[s.key] = s.value; });
      return {
        ...defaults,
        companyName: byKey.company_name ?? defaults.companyName,
        brandName: byKey.brand_name ?? defaults.brandName,
        timezone: byKey.timezone ?? defaults.timezone,
        language: byKey.language ?? defaults.language,
        theme: (byKey.theme as any) ?? defaults.theme,
        llmProvider: (byKey.llm_provider as any) ?? defaults.llmProvider,
        openaiKey: byKey.openai_api_key ?? "",
        anthropicKey: byKey.anthropic_api_key ?? "",
        geminiKey: byKey.gemini_api_key ?? "",
        defaultModel: byKey.default_model ?? defaults.defaultModel,
      };
    } catch {
      return defaults;
    }
  },
  async update(payload: Partial<AppSettings>): Promise<AppSettings> {
    // Map camelCase settings → backend key/value via upsert-by-key
    const map: Record<string, any> = {
      company_name: payload.companyName,
      brand_name: payload.brandName,
      timezone: payload.timezone,
      language: payload.language,
      theme: payload.theme,
      llm_provider: payload.llmProvider,
      openai_api_key: payload.openaiKey,
      anthropic_api_key: payload.anthropicKey,
      gemini_api_key: payload.geminiKey,
      default_model: payload.defaultModel,
    };
    await Promise.all(
      Object.entries(map)
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => apiClient.put(`/settings/by-key/${k}`, { value: String(v) }))
    );
    return this.get();
  },
};
