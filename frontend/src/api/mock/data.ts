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
} from "@/types";

// ============================================================
// MOCK DATA — NUMÉ AI Marketing Assistant
// Replace these with real API responses once a backend exists.
// ============================================================

const today = new Date();
const iso = (daysAgo: number) =>
  new Date(today.getTime() - daysAgo * 86400000).toISOString();

export const mockProducts: Product[] = [
  { id: "p_001", name: "Aurora Serum", sku: "NUM-SRM-001", category: "Skincare", price: 7800, stock: 1240, status: "active", sales: 18420, createdAt: iso(124) },
  { id: "p_002", name: "Velvet Lip Tint — Strawberry", sku: "NUM-LIP-014", category: "Cosmetics", price: 2400, stock: 3820, status: "active", sales: 92110, createdAt: iso(98), thumbnail: "/brand/shade-strawberry.jpg" },
  { id: "p_003", name: "Hydra Glow Toner", sku: "NUM-TON-007", category: "Skincare", price: 4200, stock: 540, status: "active", sales: 22810, createdAt: iso(82) },
  { id: "p_004", name: "Cloud Foundation", sku: "NUM-FND-022", category: "Cosmetics", price: 5600, stock: 0, status: "draft", sales: 0, createdAt: iso(45) },
  { id: "p_005", name: "Silk Hair Mask", sku: "NUM-HAR-009", category: "Haircare", price: 3800, stock: 1820, status: "active", sales: 13420, createdAt: iso(210) },
  { id: "p_006", name: "Petal Blush Compact", sku: "NUM-BLU-031", category: "Cosmetics", price: 3200, stock: 980, status: "active", sales: 18760, createdAt: iso(67) },
  { id: "p_007", name: "Radiance Eye Cream", sku: "NUM-EYE-002", category: "Skincare", price: 6400, stock: 640, status: "active", sales: 9820, createdAt: iso(180) },
  { id: "p_008", name: "Sun Veil SPF 50", sku: "NUM-SUN-018", category: "Skincare", price: 4400, stock: 2240, status: "active", sales: 27310, createdAt: iso(154) },
  { id: "p_009", name: "Velour Eyeshadow Kit", sku: "NUM-EYE-045", category: "Cosmetics", price: 8800, stock: 410, status: "paused", sales: 4120, createdAt: iso(40) },
  { id: "p_010", name: "Bloom Body Lotion", sku: "NUM-BDY-011", category: "Body", price: 2800, stock: 3120, status: "active", sales: 15200, createdAt: iso(120) },
  { id: "p_011", name: "Pure Cleansing Gel", sku: "NUM-CLN-003", category: "Skincare", price: 3200, stock: 2810, status: "active", sales: 21340, createdAt: iso(200) },
  { id: "p_012", name: "Lush Brow Pomade", sku: "NUM-BRW-007", category: "Cosmetics", price: 2200, stock: 0, status: "archived", sales: 5400, createdAt: iso(300) },
  { id: "p_013", name: "Crystal Facial Mist", sku: "NUM-MST-002", category: "Skincare", price: 3600, stock: 1190, status: "active", sales: 11200, createdAt: iso(35) },
  { id: "p_014", name: "Moonlight Hand Cream", sku: "NUM-HND-004", category: "Body", price: 1800, stock: 4280, status: "active", sales: 8900, createdAt: iso(75) },
  { id: "p_015", name: "Opal Highlighter", sku: "NUM-HLT-012", category: "Cosmetics", price: 3400, stock: 510, status: "draft", sales: 0, createdAt: iso(12) },
  { id: "p_016", name: "Velvet Matte Lipstick", sku: "NUM-LIP-019", category: "Cosmetics", price: 2600, stock: 2980, status: "active", sales: 41020, createdAt: iso(140), thumbnail: "/brand/shade-cherry.jpg" },
  { id: "p_017", name: "Mist Hydrating Mask", sku: "NUM-MST-009", category: "Skincare", price: 4800, stock: 720, status: "active", sales: 7620, createdAt: iso(95) },
  { id: "p_018", name: "Pure Glow Exfoliator", sku: "NUM-EXF-001", category: "Skincare", price: 4000, stock: 1450, status: "active", sales: 13210, createdAt: iso(160) },
  { id: "p_019", name: "Bloom Hair Serum", sku: "NUM-HAR-021", category: "Haircare", price: 4600, stock: 920, status: "active", sales: 6310, createdAt: iso(58) },
  { id: "p_020", name: "Petal Cream Shadow", sku: "NUM-EYE-058", category: "Cosmetics", price: 2800, stock: 0, status: "paused", sales: 0, createdAt: iso(8) },
  { id: "p_021", name: "Velvet Lip Tint — Chocolat", sku: "NUM-LIP-021", category: "Cosmetics", price: 2400, stock: 2140, status: "active", sales: 18930, createdAt: iso(22), thumbnail: "/brand/shade-chocolate.jpg" },
  { id: "p_022", name: "Velvet Lip Tint — Peach", sku: "NUM-LIP-022", category: "Cosmetics", price: 2400, stock: 2760, status: "active", sales: 24410, createdAt: iso(22), thumbnail: "/brand/shade-peach.jpg" },
];

export const mockCampaigns: Campaign[] = [
  { id: "c_001", name: "Spring Glow Launch", channel: "Email", status: "active", budget: 24000, spent: 18230, impressions: 482000, clicks: 21800, conversions: 3120, startDate: iso(30), endDate: iso(-30) },
  { id: "c_002", name: "Velvet Lip Series", channel: "Social", status: "active", budget: 38000, spent: 31200, impressions: 1240000, clicks: 68400, conversions: 8910, startDate: iso(45), endDate: iso(-15) },
  { id: "c_003", name: "Aurora Retargeting", channel: "Display", status: "active", budget: 18000, spent: 16400, impressions: 920000, clicks: 18200, conversions: 1980, startDate: iso(60), endDate: iso(-5) },
  { id: "c_004", name: "Search — Skincare", channel: "Search", status: "active", budget: 42000, spent: 39800, impressions: 612000, clicks: 42100, conversions: 7340, startDate: iso(90), endDate: iso(0) },
  { id: "c_005", name: "Holiday Bundle Push", channel: "Email", status: "draft", budget: 30000, spent: 0, impressions: 0, clicks: 0, conversions: 0, startDate: iso(-10), endDate: iso(-50) },
  { id: "c_006", name: "Affiliate Influencer Q2", channel: "Affiliate", status: "paused", budget: 22000, spent: 9800, impressions: 320000, clicks: 12400, conversions: 980, startDate: iso(70), endDate: iso(-10) },
  { id: "c_007", name: "Mother's Day Promo", channel: "Social", status: "archived", budget: 16000, spent: 15900, impressions: 540000, clicks: 28100, conversions: 4120, startDate: iso(120), endDate: iso(80) },
  { id: "c_008", name: "Hydra Toner Awareness", channel: "Display", status: "active", budget: 14000, spent: 8200, impressions: 240000, clicks: 9800, conversions: 1240, startDate: iso(20), endDate: iso(-20) },
];

export const mockKnowledge: KnowledgeDocument[] = [
  { id: "k_001", title: "Brand Voice Guidelines 2025.pdf", type: "pdf", size: 1_840_000, status: "ready", tags: ["brand", "guidelines"], version: 1, chunkCount: 0, embeddingStatus: "none", vectorCount: 0, uploadedBy: "Mira Shah", uploadedAt: iso(8), excerpt: "Defines the NUMÉ tone of voice, vocabulary do's and don'ts, and writing principles across channels." },
  { id: "k_002", title: "Product Catalogue Q2.xlsx", type: "xlsx", size: 920_000, status: "ready", tags: ["catalog", "products"], version: 1, chunkCount: 0, embeddingStatus: "none", vectorCount: 0, uploadedBy: "Arman Khan", uploadedAt: iso(14), excerpt: "Master spreadsheet of SKUs, pricing, inventory and category metadata for Q2 2025." },
  { id: "k_003", title: "Competitor Audit Notes.docx", type: "docx", size: 410_000, status: "ready", tags: ["competitive", "research"], version: 1, chunkCount: 0, embeddingStatus: "none", vectorCount: 0, uploadedBy: "Lea Roy", uploadedAt: iso(22), excerpt: "Qualitative analysis of 6 direct competitors: positioning, packaging, pricing, and reviews." },
  { id: "k_004", title: "Customer Personas.md", type: "md", size: 28_000, status: "ready", tags: ["audience", "personas"], version: 1, chunkCount: 0, embeddingStatus: "none", vectorCount: 0, uploadedBy: "Mira Shah", uploadedAt: iso(30), excerpt: "Five primary personas mapped to lifecycle stages, pain points, and messaging angles." },
  { id: "k_005", title: "Seasonal Trend Report.csv", type: "csv", size: 184_000, status: "processing", tags: ["trends", "data"], version: 1, chunkCount: 0, embeddingStatus: "none", vectorCount: 0, uploadedBy: "Diego Marin", uploadedAt: iso(1), excerpt: "Aggregated 12-month search trend data across 38 keywords." },
  { id: "k_006", title: "Influencer Brief — Aurora Serum.pdf", type: "pdf", size: 680_000, status: "ready", tags: ["influencer", "campaign"], version: 1, chunkCount: 0, embeddingStatus: "none", vectorCount: 0, uploadedBy: "Arman Khan", uploadedAt: iso(12), excerpt: "Brief and talking points sent to 14 creators for the Aurora Serum launch." },
  { id: "k_007", title: "Pricing Strategy Memo.txt", type: "txt", size: 12_000, status: "ready", tags: ["pricing", "strategy"], version: 1, chunkCount: 0, embeddingStatus: "none", vectorCount: 0, uploadedBy: "Lea Roy", uploadedAt: iso(45), excerpt: "Internal memo on premiumisation ladder and bundle pricing architecture." },
  { id: "k_008", title: "Newsletter Archive URL", type: "url", size: 0, status: "ready", tags: ["email", "archive"], version: 1, chunkCount: 0, embeddingStatus: "none", vectorCount: 0, uploadedBy: "Mira Shah", uploadedAt: iso(5), excerpt: "Crawled archive of the last 24 monthly newsletters, indexed for retrieval." },
  { id: "k_009", title: "Patent Filings Review.pdf", type: "pdf", size: 2_400_000, status: "failed", tags: ["legal", "ip"], version: 1, chunkCount: 0, embeddingStatus: "none", vectorCount: 0, uploadedBy: "Diego Marin", uploadedAt: iso(2), excerpt: "Document could not be parsed due to encrypted sections." },
  { id: "k_010", title: "Retail Partner Onboarding.docx", type: "docx", size: 320_000, status: "queued", tags: ["retail", "ops"], version: 1, chunkCount: 0, embeddingStatus: "none", vectorCount: 0, uploadedBy: "Arman Khan", uploadedAt: iso(0), excerpt: "Standard operating procedures for onboarding new retail partners." },
];

export const mockUploads: UploadRecord[] = [
  { id: "u_001", filename: "aurora-campaign-creative.zip", mimeType: "application/zip", size: 24_800_000, progress: 100, status: "completed", category: "Asset", uploadedAt: iso(2) },
  { id: "u_002", filename: "competitor-pricing-q2.xlsx", mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", size: 920_000, progress: 100, status: "completed", category: "Report", uploadedAt: iso(4) },
  { id: "u_003", filename: "brand-voice-2025.pdf", mimeType: "application/pdf", size: 1_840_000, progress: 100, status: "completed", category: "Knowledge", uploadedAt: iso(8) },
  { id: "u_004", filename: "influencer-batch-2.csv", mimeType: "text/csv", size: 84_000, progress: 100, status: "completed", category: "Report", uploadedAt: iso(11) },
  { id: "u_005", filename: "spring-shoot-raws.zip", mimeType: "application/zip", size: 188_000_000, progress: 64, status: "uploading", category: "Asset", uploadedAt: iso(0) },
  { id: "u_006", filename: "previous-asset-batch.zip", mimeType: "application/zip", size: 56_000_000, progress: 0, status: "failed", category: "Asset", uploadedAt: iso(0) },
];

export const mockCompetitors: Competitor[] = [
  { id: "cp_001", name: "GlossAura", domain: "glossaura.com", shareOfVoice: 28, organicTraffic: 1_240_000, paidTraffic: 0, organicKeywords: 4820, paidKeywords: 124, trend: [22, 25, 24, 28, 30, 27, 28], change: 12.4 },
  { id: "cp_002", name: "Velvet Labs", domain: "velvetlabs.co", shareOfVoice: 22, organicTraffic: 980_000, paidTraffic: 0, organicKeywords: 3120, paidKeywords: 98, trend: [30, 28, 26, 24, 23, 22, 22], change: -8.1 },
  { id: "cp_003", name: "PureHue", domain: "purehue.io", shareOfVoice: 18, organicTraffic: 760_000, paidTraffic: 0, organicKeywords: 2840, paidKeywords: 76, trend: [14, 15, 16, 17, 17, 18, 18], change: 4.2 },
  { id: "cp_004", name: "Bloom & Co", domain: "bloomandco.com", shareOfVoice: 14, organicTraffic: 540_000, paidTraffic: 0, organicKeywords: 1980, paidKeywords: 62, trend: [18, 17, 17, 16, 15, 14, 14], change: -3.6 },
  { id: "cp_005", name: "Miraé", domain: "mirae.beauty", shareOfVoice: 10, organicTraffic: 410_000, paidTraffic: 0, organicKeywords: 1240, paidKeywords: 48, trend: [6, 7, 8, 9, 9, 10, 10], change: 6.8 },
  { id: "cp_006", name: "Aether Skin", domain: "aetherskin.com", shareOfVoice: 8, organicTraffic: 320_000, paidTraffic: 0, organicKeywords: 980, paidKeywords: 32, trend: [10, 9, 9, 8, 8, 8, 8], change: -1.2 },
];

export const mockReviews: CustomerReview[] = [
  { id: "r_001", author: "Priya M.", source: "Amazon", rating: 5, title: "Best serum I've used", body: "After 3 weeks my skin looks visibly brighter. Will repurchase.", product: "Aurora Serum", sentiment: "positive", status: "new", date: iso(1) },
  { id: "r_002", author: "Sara L.", source: "Trustpilot", rating: 4, title: "Lovely texture", body: "Goes on smooth and lasts all day. Slightly pricey but worth it.", product: "Velvet Lip Tint", sentiment: "positive", status: "responded", date: iso(2) },
  { id: "r_003", author: "Tomás G.", source: "Google", rating: 2, title: "Broke me out", body: "Wanted to love it but my skin reacted after a few uses. Returning.", product: "Hydra Glow Toner", sentiment: "negative", status: "flagged", date: iso(3) },
  { id: "r_004", author: "Naomi K.", source: "Amazon", rating: 5, title: "Holy grail", body: "This is the only SPF that doesn't leave a white cast on me.", product: "Sun Veil SPF 50", sentiment: "positive", status: "new", date: iso(4) },
  { id: "r_005", author: "Hana W.", source: "Yelp", rating: 3, title: "Just okay", body: "Does the job but nothing special for the price point.", product: "Silk Hair Mask", sentiment: "neutral", status: "new", date: iso(5) },
  { id: "r_006", author: "Eli R.", source: "Site", rating: 5, title: "Repeat buyer", body: "On my 4th bottle. Cannot recommend enough.", product: "Pure Cleansing Gel", sentiment: "positive", status: "responded", date: iso(6) },
  { id: "r_007", author: "Carla D.", source: "Amazon", rating: 1, title: "Damaged packaging", body: "Product arrived leaking. Reached out twice with no response.", product: "Velvet Matte Lipstick", sentiment: "negative", status: "flagged", date: iso(7) },
  { id: "r_008", author: "Maya S.", source: "Trustpilot", rating: 4, title: "Great everyday blush", body: "Pigmented but buildable. Lasts all day at the office.", product: "Petal Blush Compact", sentiment: "positive", status: "new", date: iso(8) },
  { id: "r_009", author: "Ren T.", source: "Google", rating: 5, title: "Miracle eye cream", body: "Saw reduction in dark circles in 2 weeks. Unbelievable.", product: "Radiance Eye Cream", sentiment: "positive", status: "responded", date: iso(9) },
  { id: "r_010", author: "Lina B.", source: "Site", rating: 2, title: "Too drying", body: "Loved the shade but it clings to dry patches. Not for me.", product: "Velour Eyeshadow Kit", sentiment: "negative", status: "new", date: iso(10) },
];

export const mockUsers: User[] = [
  { id: "u_001", name: "Mira Shah", email: "mira@nume.ai", role: "Owner", status: "active", lastActive: iso(0), createdAt: iso(420) },
  { id: "u_002", name: "Arman Khan", email: "arman@nume.ai", role: "Admin", status: "active", lastActive: iso(0), createdAt: iso(380) },
  { id: "u_003", name: "Lea Roy", email: "lea@nume.ai", role: "Editor", status: "active", lastActive: iso(1), createdAt: iso(260) },
  { id: "u_004", name: "Diego Marin", email: "diego@nume.ai", role: "Editor", status: "active", lastActive: iso(2), createdAt: iso(180) },
  { id: "u_005", name: "Sofia Chen", email: "sofia@nume.ai", role: "Viewer", status: "invited", lastActive: iso(0), createdAt: iso(4) },
  { id: "u_006", name: "Jonah Pierce", email: "jonah@nume.ai", role: "Viewer", status: "suspended", lastActive: iso(45), createdAt: iso(120) },
];

export const mockActivity: ActivityEvent[] = [
  { id: "a_001", type: "upload", title: "New asset uploaded", description: "spring-shoot-raws.zip is being processed", actor: "Arman Khan", timestamp: iso(0) },
  { id: "a_002", type: "campaign", title: "Campaign published", description: "Search — Skincare went live", actor: "Lea Roy", timestamp: iso(0) },
  { id: "a_003", type: "review", title: "Review flagged", description: "1-star review on Velvet Matte Lipstick flagged for response", actor: "System", timestamp: iso(1) },
  { id: "a_004", type: "product", title: "Product updated", description: "Aurora Serum price updated to $78", actor: "Mira Shah", timestamp: iso(2) },
  { id: "a_005", type: "knowledge", title: "Document ready", description: "Brand Voice Guidelines 2025.pdf is now indexed", actor: "System", timestamp: iso(3) },
  { id: "a_006", type: "user", title: "User invited", description: "Sofia Chen was invited as Viewer", actor: "Mira Shah", timestamp: iso(4) },
  { id: "a_007", type: "system", title: "Storage check passed", description: "Object storage health: OK", actor: "System", timestamp: iso(5) },
];

export const mockSystemStatus: SystemService[] = [
  { name: "API Gateway", status: "operational", latency: 42, uptime: 99.99 },
  { name: "Search Index", status: "operational", latency: 88, uptime: 99.97 },
  { name: "Vector Store", status: "degraded", latency: 320, uptime: 99.42 },
  { name: "Asset Storage", status: "operational", latency: 64, uptime: 99.95 },
  { name: "Email Pipeline", status: "operational", latency: 110, uptime: 99.91 },
  { name: "Analytics Engine", status: "operational", latency: 220, uptime: 99.88 },
];

export const defaultSettings: AppSettings = {
  companyName: "NUMÉ Beauty Labs Inc.",
  brandName: "NUMÉ",
  timezone: "Asia/Karachi",
  language: "English",
  theme: "light",
  llmProvider: "openai",
  openaiKey: "sk-proj-9kQ2mN8pL3vR7tY1",
  anthropicKey: "sk-ant-03xQ7vB2nP5mL8k",
  geminiKey: "AIzaSyB9-3kQ8mN2pL5",
  defaultModel: "gpt-4o",
};
