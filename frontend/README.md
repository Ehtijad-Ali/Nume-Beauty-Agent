# NUMÉ — AI Marketing Assistant

A premium, production-ready **React 19 + Vite + TypeScript** dashboard for marketing teams.
Built with Tailwind CSS, shadcn/ui patterns, React Query, React Hook Form, Zod, Framer Motion
and Recharts. Ships with light/dark mode, responsive layout, mock API services, loading
skeletons, empty states and toast notifications.

---

## ✨ Features

- **Authentication** — premium split-screen login page (demo credentials pre-filled)
- **Collapsible sidebar** — desktop collapse + mobile drawer, with active link animations
- **Topbar** — global search, notifications dropdown, theme toggle, profile menu
- **Dark / Light / System** theme with persistence
- **Dashboard** — stat cards, area & bar charts (Recharts), recent activity feed, system status, quick links
- **Products** — professional data table, search, status filter, pagination, full CRUD with form validation
- **Knowledge Base** — filters (type, status), search, document table, preview dialog
- **Uploads** — drag & drop dropzone, live progress bars, preview, delete, download
- **Campaigns** — summary cards, conversion bar chart, channel cards with budget utilisation
- **Competitors** — share-of-voice pie chart, top movers list, competitor cards with sparklines
- **Customer Reviews** — sentiment & status filters, star ratings, respond action
- **Users** — team roster, invite dialog, role badges, remove user
- **Settings** — tabbed (Company / Localisation / Appearance / AI Provider) with masked API keys
- **Profile** — gradient banner, avatar, personal info, security panel
- **404 page** — animated, on-brand

## 🧱 Tech Stack

| Concern        | Library                                   |
| -------------- | ----------------------------------------- |
| Framework      | React 19                                  |
| Build tool     | Vite 6                                    |
| Language       | TypeScript 5.7                            |
| Styling        | Tailwind CSS 3.4 + CSS variables          |
| UI primitives  | Radix UI (shadcn/ui pattern)              |
| Routing        | React Router 7                            |
| Data fetching  | @tanstack/react-query 5                   |
| HTTP client    | axios                                     |
| Forms          | react-hook-form + zod                     |
| Animations     | framer-motion                             |
| Charts         | recharts                                  |
| Icons          | lucide-react                              |
| Toasts         | sonner                                    |

## 📂 Project Structure

```
src/
├── api/                  # axios client + mock services & data
│   ├── client.ts
│   ├── index.ts
│   └── mock/
│       ├── data.ts       # in-memory mock dataset
│       └── services.ts   # simulated async API services
├── components/
│   ├── ui/               # shadcn/ui primitives (button, card, dialog, etc.)
│   ├── layout/           # AppLayout, Sidebar, Topbar
│   ├── common/           # PageHeader, EmptyState, StatusBadge, Logo…
│   └── dashboard/        # StatCard
├── context/              # ThemeProvider, AuthContext, SidebarContext
├── hooks/                # useApi (React Query hooks)
├── lib/                  # utils (cn, format helpers) + queryClient + nav
├── pages/                # 12 pages (Login, Dashboard, … 404)
├── types/                # shared domain types
├── App.tsx               # routes
├── main.tsx              # providers + router
└── index.css             # tailwind + design tokens
```

## 🚀 Getting Started

```bash
# 1. Install dependencies
npm install      # or: pnpm install / yarn install

# 2. Start the dev server
npm run dev

# 3. Open the app
# → http://localhost:5173
```

### Demo Login

The login form is pre-filled with demo credentials. Just click **Sign in** — any
email/password will work since the app uses mock authentication.

## 📜 Scripts

| Script              | Purpose                                |
| ------------------- | -------------------------------------- |
| `npm run dev`       | Start Vite dev server                  |
| `npm run build`     | Type-check + production build          |
| `npm run preview`   | Preview the production build locally   |
| `npm run typecheck` | Run TypeScript without emitting files  |

## 🔌 Wiring a real backend

The app is structured so that swapping the mock services for a real API is a 5-minute job:

1. Set `VITE_API_BASE_URL` in a `.env` file (e.g. `https://api.your-backend.com`).
2. Open `src/api/mock/services.ts` and replace each function body with a call to
   `apiClient.get/post/put/delete(...)` (the client is already configured in
   `src/api/client.ts` with an Authorization header interceptor).
3. Remove the `sleep()` latency wrappers.

All hooks in `src/hooks/useApi.ts` will continue to work unchanged.

## 🎨 Design System

The design uses CSS variables for both light and dark themes — see `src/index.css`
for the full token list. Brand gradient: `violet-600 → indigo-600 → blue-600`.

## 📦 Notes

- This build is **frontend-only** — no AI, chat or RAG is implemented.
- All data is held in memory and resets on reload.
- API keys entered in Settings are stored in `localStorage` for the demo only.

---

© 2025 NUMÉ Beauty Labs — built for demonstration purposes.
