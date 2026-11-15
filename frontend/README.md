# ATLAS AI Engineer Web

Next.js browser workspace for the Personal AI Software Engineer.

## Development
```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api/*` to `ATLAS_BACKEND_INTERNAL_URL` (default `http://127.0.0.1:8000`). It reuses ATLAS agency registration and login, and stores the short-lived bearer token in browser local storage. Use HTTPS for any hosted deployment and configure the backend URL as a private server-side environment variable.

The initial screen supports account registration/login, workspace prompt submission, run history, and result inspection. Actual model execution requires the backend's `LLM_API_KEY` and `LLM_MODEL`.
