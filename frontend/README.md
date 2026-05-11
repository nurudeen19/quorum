# Frontend

Web interface for generating pre-meeting intelligence briefs. Built with Vue 3 + TypeScript.

## Quick Start

**Prerequisites:** Node.js 16+

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. The dev server proxies `/api` to the backend at `http://127.0.0.1:8000`.

## Environment Variables

| Variable | Purpose | Required | Example |
|----------|---------|----------|---------|
| `VITE_API_BASE_URL` | API endpoint (production only) | — | `https://api.example.com/api/v1` |

For local development, no setup needed—the Vite proxy handles it. For production builds, set `VITE_API_BASE_URL` in `.env.production`.

See `.env.example` for reference.

## Common Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server (hot-reload, port 5173) |
| `npm run build` | Build for production (output in `dist/`) |
| `npm run preview` | Preview production build locally |

## Project Structure

```
src/
  components/     ← Reusable UI components
  views/          ← Full-page components (routes)
  stores/         ← Pinia state management
  api/            ← Backend API calls
  router/         ← Vue Router routes
  assets/         ← Stylesheets, images
  main.ts         ← App entry point
public/           ← Static files
```

## What's Going On

**Pre-Meeting Workflow**: Users enter basic info about an upcoming meeting (who's involved, what companies, what outcome they need). The backend researches and synthesizes a memo, which streams back in real-time.

**Real-Time Updates**: The browser subscribes to Server-Sent Events (SSE) from the backend. As each research agent step completes (planning → researching → writing → reviewing), the UI updates so users see progress and the emerging memo.

**State Management**: [Pinia](https://pinia.vuejs.org/) stores track user auth, conversation history, and current briefing status. See `src/stores/` to understand how state flows through the app.

**API Integration**: All backend calls live in `src/api/`. This layer handles auth headers, request formatting, and the SSE subscription for real-time memo generation.

## Troubleshooting

**Dev server can't reach the backend**
- Ensure backend is running on `http://127.0.0.1:8000`
- Check `vite.config.ts` proxy configuration
- Look for errors in the browser console (F12)

**SSE stream not connecting**
- Check browser DevTools → Network tab
- Verify the `/api/v1/chat/stream` endpoint exists on the backend
- Ensure you're authenticated (JWT token in headers)

**Build fails or compiled output is huge**
- Run `npm run build` and check the terminal output for specific errors
- Check browser console for missing assets
- Verify all imports use correct paths (case-sensitive on Linux/Mac)

**TypeScript errors in editor**
- Run `npm run typecheck` if available (check `package.json`)
- Ensure `node_modules` is not corrupted: delete and run `npm install` again
