Run the app:

```bash
cd src/frontend
npm run dev
```

In a second terminal, expose it with ngrok:

```bash
cd src/frontend
npm run share
```

Share the HTTPS forwarding URL that ngrok prints.

Notes:

- The frontend public URL tunnels the whole app.
- Backend `/run`, `/health`, `/output`, and `/docs` still work through Vite's local proxy to `127.0.0.1:8000`.
- If the backend is still loading models, the shared app will show the same API errors as your local app.
