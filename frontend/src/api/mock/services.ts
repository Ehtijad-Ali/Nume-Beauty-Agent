import { apiClient } from "../client";
import type {
  Product,
  Campaign,
  KnowledgeDocument,
  UploadRecord,
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

const mapKnowledge = (k: any): KnowledgeDocument => ({
  id: k.id,
  title: k.title,
  type: k.doc_type,
  size: k.file_size,
  status: k.status,
  tags: k.tags ? k.tags.split(",").map((t: string) => t.trim()) : [],
  uploadedBy: k.uploaded_by_id ?? "Unknown",
  uploadedAt: k.created_at,
  excerpt: k.excerpt,
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
// Dashboard (mock — backend doesn't yet expose a dashboard endpoint)
// --------------------------------------------------------------------------- //
export const dashboardService = {
  async getActivity(): Promise<ActivityEvent[]> {
    await sleep(300);
    return [
      { id: "a_1", type: "upload", title: "Asset uploaded", description: "brand-voice.pdf is being processed", actor: "Mira Shah", timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString() },
      { id: "a_2", type: "campaign", title: "Campaign published", description: "Search — Skincare went live", actor: "Lea Roy", timestamp: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString() },
      { id: "a_3", type: "review", title: "Review flagged", description: "1-star review on Velvet Matte Lipstick flagged", actor: "System", timestamp: new Date(Date.now() - 1000 * 60 * 60 * 8).toISOString() },
      { id: "a_4", type: "product", title: "Product updated", description: "Aurora Serum price updated", actor: "Mira Shah", timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString() },
      { id: "a_5", type: "system", title: "Storage check passed", description: "Object storage health: OK", actor: "System", timestamp: new Date(Date.now() - 1000 * 60 * 60 * 30).toISOString() },
    ];
  },
  async getSystemStatus(): Promise<SystemService[]> {
    await sleep(300);
    return [
      { name: "API Gateway", status: "operational", latency: 42, uptime: 99.99 },
      { name: "Database", status: "operational", latency: 18, uptime: 99.97 },
      { name: "Redis Cache", status: "operational", latency: 4, uptime: 99.95 },
      { name: "Asset Storage", status: "operational", latency: 64, uptime: 99.95 },
      { name: "Email Pipeline", status: "operational", latency: 110, uptime: 99.91 },
    ];
  },
  async getStats() {
    await sleep(300);
    return {
      products: { total: 0, active: 0, revenue: 0 },
      campaigns: { total: 0, active: 0, budget: 0, spent: 0 },
      knowledge: { total: 0, ready: 0, sizeBytes: 0 },
      uploads: { total: 0, completed: 0, sizeBytes: 0 },
    };
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
  async list(params: { search?: string; type?: string; status?: string } = {}): Promise<KnowledgeDocument[]> {
    const res = await apiClient.get("/knowledge", {
      params: {
        page_size: 100,
        search: params.search || undefined,
        doc_type: params.type && params.type !== "all" ? params.type : undefined,
        status: params.status && params.status !== "all" ? params.status : undefined,
      },
    });
    return (res.data.items || []).map(mapKnowledge);
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/knowledge/${id}`);
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
  { id: "cp_001", name: "GlossAura", domain: "glossaura.com", shareOfVoice: 28, traffic: 1_240_000, keywords: 4820, ads: 124, trend: [22, 25, 24, 28, 30, 27, 28], change: 12.4 },
  { id: "cp_002", name: "Velvet Labs", domain: "velvetlabs.co", shareOfVoice: 22, traffic: 980_000, keywords: 3120, ads: 98, trend: [30, 28, 26, 24, 23, 22, 22], change: -8.1 },
  { id: "cp_003", name: "PureHue", domain: "purehue.io", shareOfVoice: 18, traffic: 760_000, keywords: 2840, ads: 76, trend: [14, 15, 16, 17, 17, 18, 18], change: 4.2 },
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
