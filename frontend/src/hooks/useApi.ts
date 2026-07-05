import { useQuery, useMutation, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import {
  productService,
  campaignService,
  knowledgeService,
  uploadService,
  competitorService,
  reviewService,
  userService,
  dashboardService,
  settingsService,
  ragService,
} from "@/api";
import type { Product, CustomerReview, AppSettings, SemanticSearchParams, RagQueryParams } from "@/types";

// ---------- Dashboard ----------
export const useDashboardStats = () =>
  useQuery({ queryKey: ["dashboard", "stats"], queryFn: dashboardService.getStats });

export const useActivity = () =>
  useQuery({ queryKey: ["dashboard", "activity"], queryFn: dashboardService.getActivity });

export const useSystemStatus = () =>
  useQuery({ queryKey: ["dashboard", "system"], queryFn: dashboardService.getSystemStatus });

// ---------- Products ----------
export const useProducts = (params: { page: number; pageSize: number; search: string; status: string }) =>
  useQuery({
    queryKey: ["products", params],
    queryFn: () => productService.list(params),
    placeholderData: keepPreviousData,
  });

export const useCreateProduct = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Product>) => productService.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
};

export const useUpdateProduct = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<Product> }) =>
      productService.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
};

export const useDeleteProduct = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => productService.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
};

// ---------- Campaigns ----------
export const useCampaigns = () =>
  useQuery({ queryKey: ["campaigns"], queryFn: campaignService.list });

// ---------- Knowledge ----------
export const useKnowledge = (params: { search: string; type: string; status: string; categoryId?: string }) =>
  useQuery({
    queryKey: ["knowledge", params],
    queryFn: () => knowledgeService.list(params),
    // Poll while any document is still being embedded in the background
    refetchInterval: (query) =>
      query.state.data?.some((d) => d.embeddingStatus === "pending" || d.embeddingStatus === "processing")
        ? 3000
        : false,
  });

export const useDeleteKnowledge = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => knowledgeService.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["knowledge"] });
      qc.invalidateQueries({ queryKey: ["knowledge-categories"] });
    },
  });
};

export const useUploadKnowledge = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      file,
      title,
      categoryId,
      brand,
      tags,
      onProgress,
    }: {
      file: File;
      title?: string;
      categoryId?: string;
      brand?: string;
      tags?: string;
      onProgress?: (e: { loaded: number; total: number; percent: number }) => void;
    }) => knowledgeService.upload({ file, title, categoryId, brand, tags }, onProgress),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["knowledge"] });
      qc.invalidateQueries({ queryKey: ["knowledge-categories"] });
    },
  });
};

export const useReplaceKnowledge = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      file,
      changeNote,
      onProgress,
    }: {
      id: string;
      file: File;
      changeNote?: string;
      onProgress?: (e: { loaded: number; total: number; percent: number }) => void;
    }) => knowledgeService.replace(id, file, changeNote, onProgress),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledge"] }),
  });
};

export const useReindexKnowledge = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => knowledgeService.reindex(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledge"] }),
  });
};

export const useKnowledgeChunks = (id: string | null) =>
  useQuery({
    queryKey: ["knowledge", id, "chunks"],
    queryFn: () => knowledgeService.chunks(id!),
    enabled: !!id,
  });

export const useKnowledgeVersions = (id: string | null) =>
  useQuery({
    queryKey: ["knowledge", id, "versions"],
    queryFn: () => knowledgeService.versions(id!),
    enabled: !!id,
  });

export const useKnowledgeCategories = () =>
  useQuery({ queryKey: ["knowledge-categories"], queryFn: () => knowledgeService.categories() });

export const useIndexStats = () =>
  useQuery({
    queryKey: ["knowledge-index-stats"],
    queryFn: () => knowledgeService.indexStats(),
    refetchInterval: 15_000,
  });

export const useSemanticSearch = () =>
  useMutation({
    mutationFn: (params: SemanticSearchParams) => knowledgeService.search(params),
  });

export const useDeleteIndex = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => knowledgeService.deleteIndex(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["knowledge"] });
      qc.invalidateQueries({ queryKey: ["knowledge-index-stats"] });
    },
  });
};

export const useCreateKnowledgeCategory = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; description?: string; color?: string }) =>
      knowledgeService.createCategory(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledge-categories"] }),
  });
};

// ---------- RAG assistant ----------
export const useRagQuery = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: RagQueryParams) => ragService.query(params),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["rag-conversations"] });
      qc.invalidateQueries({ queryKey: ["rag-messages", data.conversationId] });
      qc.invalidateQueries({ queryKey: ["rag-stats"] });
    },
  });
};

export const useRagConversations = () =>
  useQuery({ queryKey: ["rag-conversations"], queryFn: () => ragService.conversations() });

export const useRagMessages = (conversationId: string | null) =>
  useQuery({
    queryKey: ["rag-messages", conversationId],
    queryFn: () => ragService.messages(conversationId!),
    enabled: !!conversationId,
  });

export const useDeleteRagConversation = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ragService.removeConversation(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["rag-conversations"] });
      qc.invalidateQueries({ queryKey: ["rag-stats"] });
    },
  });
};

export const useRagMessageDebug = (messageId: string | null) =>
  useQuery({
    queryKey: ["rag-message-debug", messageId],
    queryFn: () => ragService.messageDebug(messageId!),
    enabled: !!messageId,
  });

export const useRagStats = () =>
  useQuery({ queryKey: ["rag-stats"], queryFn: () => ragService.stats() });

export const useRagConfig = () =>
  useQuery({ queryKey: ["rag-config"], queryFn: () => ragService.config() });

// ---------- Uploads ----------
export const useUploads = (params: { search?: string; category?: string; status?: string } = {}) =>
  useQuery({ queryKey: ["uploads", params], queryFn: () => uploadService.list(params) });

export const useDeleteUpload = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => uploadService.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["uploads"] }),
  });
};

export const useUploadFile = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      file,
      category,
      description,
      onProgress,
    }: {
      file: File;
      category: string;
      description?: string;
      onProgress?: (e: { loaded: number; total: number; percent: number }) => void;
    }) => uploadService.uploadFile(file, category, description, onProgress),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["uploads"] }),
  });
};

export const useReplaceFile = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      file,
      category,
      description,
      onProgress,
    }: {
      id: string;
      file: File;
      category: string;
      description?: string;
      onProgress?: (e: { loaded: number; total: number; percent: number }) => void;
    }) => uploadService.replaceFile(id, file, category, description, onProgress),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["uploads"] }),
  });
};

// ---------- Competitors ----------
export const useCompetitors = () =>
  useQuery({ queryKey: ["competitors"], queryFn: competitorService.list });

// ---------- Reviews ----------
export const useReviews = (params: { search: string; sentiment: string; status: string }) =>
  useQuery({ queryKey: ["reviews", params], queryFn: () => reviewService.list(params) });

export const useRespondReview = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => reviewService.respond(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reviews"] }),
  });
};

// ---------- Users ----------
export const useUsers = (params: { search?: string } = {}) =>
  useQuery({ queryKey: ["users", params], queryFn: () => userService.list(params) });

export const useCreateUser = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; email: string; role: string; password: string }) =>
      userService.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
};

export const useDeleteUser = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => userService.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
};

// ---------- Settings ----------
export const useSettings = () =>
  useQuery({ queryKey: ["settings"], queryFn: settingsService.get });

export const useUpdateSettings = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<AppSettings>) => settingsService.update(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings"] }),
  });
};
