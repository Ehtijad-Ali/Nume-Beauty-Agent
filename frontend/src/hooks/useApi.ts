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
} from "@/api";
import type { Product, KnowledgeDocument, CustomerReview, AppSettings } from "@/types";

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
export const useKnowledge = (params: { search: string; type: string; status: string }) =>
  useQuery({ queryKey: ["knowledge", params], queryFn: () => knowledgeService.list(params) });

export const useDeleteKnowledge = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => knowledgeService.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledge"] }),
  });
};

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
