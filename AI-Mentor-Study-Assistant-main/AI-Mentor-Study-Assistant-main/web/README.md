AI Mentor — Static Landing Page

This `web/` folder contains a lightweight responsive landing page (`index.html`) you can serve locally.

How to serve locally (simple):

1. From the project root run:

```powershell
python -m http.server 8000
```

2. Open the site at:

```
http://localhost:8000/web/
```

Quick workflow:
- Start your Streamlit app first:

```powershell
C:/Python313/python.exe -m streamlit run "app.py"
```

- Then open the landing page and click "Open App (Local)".

Deployment:
- You can host `web/` on GitHub Pages or any static hosting provider.
 - You can host `web/` on GitHub Pages or any static hosting provider.

Authentication Integration
- The landing page includes a simple client-side Login / Sign up modal that simulates accounts using `localStorage`.
- To integrate with a real backend, implement two endpoints (examples):
	- `POST /api/signup` -> accepts `{username,email,password}` and returns `{username}` on success.
	- `POST /api/login` -> accepts `{email,password}` and returns `{username}` and a session token.
- Update the client-side calls in `web/index.html` (search for `fetch('/api/login'`) and uncomment/adjust to post to your API. The UI will store the returned username in `localStorage` and show it in the top-right.

Security note
- The current client-side simulation is for convenience only. Do NOT use client-side-only auth in production. Implement server-side password hashing, sessions or JWT, and HTTPS.

Customization:
- Edit `index.html` and `style.css` to change colors, text, or add your logo.

Notes:
- This is a static front page that links to your Streamlit instance. If you want a single-page app that embeds Streamlit, we can add an `iframe` but note some browsers or Streamlit configurations may block embedding (X-Frame-Options).