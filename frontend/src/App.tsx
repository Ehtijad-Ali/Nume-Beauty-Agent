import { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoadingState } from "@/components/common/LoadingState";

// Lazy-loaded pages — keeps initial bundle small.
const Login = lazy(() => import("@/pages/Login"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Products = lazy(() => import("@/pages/Products"));
const KnowledgeBase = lazy(() => import("@/pages/KnowledgeBase"));
const Assistant = lazy(() => import("@/pages/Assistant"));
const Campaigns = lazy(() => import("@/pages/Campaigns"));
const Uploads = lazy(() => import("@/pages/Uploads"));
const Competitors = lazy(() => import("@/pages/Competitors"));
const CustomerReviews = lazy(() => import("@/pages/CustomerReviews"));
const Users = lazy(() => import("@/pages/Users"));
const Settings = lazy(() => import("@/pages/Settings"));
const Profile = lazy(() => import("@/pages/Profile"));
const NotFound = lazy(() => import("@/pages/NotFound"));

export default function App() {
  return (
    <Suspense fallback={<LoadingState message="Loading workspace…" className="min-h-screen" />}>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="products" element={<Products />} />
          <Route path="knowledge" element={<KnowledgeBase />} />
          <Route path="assistant" element={<Assistant />} />
          <Route path="campaigns" element={<Campaigns />} />
          <Route path="uploads" element={<Uploads />} />
          <Route path="competitors" element={<Competitors />} />
          <Route path="reviews" element={<CustomerReviews />} />
          <Route path="users" element={<Users />} />
          <Route path="settings" element={<Settings />} />
          <Route path="profile" element={<Profile />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
