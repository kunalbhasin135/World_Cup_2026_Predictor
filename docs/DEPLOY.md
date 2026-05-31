# Deployment (free tier)

Host the **API on Render** and the **React app on Vercel**. Total cost: $0 for a personal portfolio.

## Prerequisites

- Code on GitHub: [World_Cup_2026_Predictor](https://github.com/kunalbhasin135/World_Cup_2026_Predictor)
- No credit card required on either platform (optional on Render; skip to avoid overage charges)

## 1. Backend — Render

1. Sign in at [render.com](https://render.com) → **New** → **Blueprint** (or **Web Service**).
2. Connect the GitHub repo `World_Cup_2026_Predictor`.
3. Use the repo’s `render.yaml`, or configure manually:
   - **Root directory:** `backend`
   - **Build command:**  
     `pip install -r requirements.txt && python scripts/build_features.py && python scripts/train_model.py`  
     (downloads match history on first build — do **not** use `--skip-download` in production.)
   - **Start command:**  
     `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
4. **Environment variables:**

   | Key | Value |
   | ----- | ----- |
   | `USE_HISTORICAL_FEATURES` | `true` |
   | `PYTHON_VERSION` | `3.13` |
   | `CORS_ORIGINS` | `["https://YOUR_VERCEL_APP.vercel.app","http://localhost:5173"]` |

5. Deploy. First build may take **10–20+ minutes** (download + feature build + training).
6. Note your API URL, e.g. `https://wc2026-api.onrender.com`.
7. Verify: `https://YOUR_API.onrender.com/health` → `{"status":"ok",...}`

**Free tier behavior:** the service sleeps after ~15 minutes idle; the first request after sleep can take ~30–60s.

## 2. Frontend — Vercel

1. Sign in at [vercel.com](https://vercel.com) → **Add New** → **Project** → import the same repo.
2. **Root directory:** `frontend`
3. Framework: **Vite** (auto-detected). Build: `npm run build`, output: `dist`.
4. **Environment variable:**

   | Key | Value |
   | ----- | ----- |
   | `VITE_API_URL` | `https://YOUR_API.onrender.com` (no trailing slash) |

5. Deploy. Open the `*.vercel.app` URL and test a prediction.

**Alternative:** set `frontend/vercel.json` rewrite `destination` to your Render URL and leave `VITE_API_URL` unset (client uses `/api`).

## 3. Finish README links

Update the root `README.md`:

- **Live demo** → your Vercel URL
- **API** → your Render `/docs` URL

## Troubleshooting

| Issue | Fix |
| ----- | --- |
| CORS error in browser | Add exact Vercel origin to `CORS_ORIGINS` on Render, redeploy API |
| Build fails: `results.csv` not found | Remove `--skip-download` from build (see `render.yaml`) |
| API very slow first load | Render free tier cold start — normal |
| 404 on API routes from frontend | Check `VITE_API_URL` or `vercel.json` backend URL |
