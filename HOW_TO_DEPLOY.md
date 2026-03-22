# ReelSave – Deployment Guide
### GitHub Pages (Frontend) + Render.com (Backend)

---

## PART 1 — Deploy the Backend on Render.com

### Step 1 – Create a GitHub repo for the backend
1. Go to https://github.com and sign in (or create a free account).
2. Click **New repository** → name it `reelsave-backend` → click **Create**.
3. Upload everything inside the **`backend/`** folder to this repo:
   - `app.py`
   - `requirements.txt`
   - `render.yaml`
   - `Procfile`
   - `.gitignore`

   *(You can drag-and-drop files right on the GitHub page.)*

### Step 2 – Deploy on Render.com
1. Go to https://render.com and sign in with GitHub.
2. Click **New → Web Service**.
3. Connect your `reelsave-backend` GitHub repo.
4. Render will auto-detect the settings from `render.yaml`. Confirm:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --workers 2 --timeout 180 --bind 0.0.0.0:$PORT`
5. Choose the **Free** plan → click **Create Web Service**.
6. Wait 2–3 minutes for the first deploy.
7. Copy your backend URL — it looks like:
   ```
   https://reelsave-backend.onrender.com
   ```
   **Save this URL — you'll need it in Part 2.**

---

## PART 2 — Deploy the Frontend on GitHub Pages

### Step 1 – Edit the frontend file
1. Open the **`frontend/index.html`** file in any text editor (Notepad, VS Code, etc.).
2. Find this line near the top:
   ```javascript
   const API_BASE = "https://YOUR-APP-NAME.onrender.com";
   ```
3. Replace `YOUR-APP-NAME` with your actual Render URL from Part 1. Example:
   ```javascript
   const API_BASE = "https://reelsave-backend.onrender.com";
   ```
4. Save the file.

### Step 2 – Create a GitHub repo for the frontend
1. Go to https://github.com → **New repository** → name it `reelsave` (or anything you like).
2. Make sure it is set to **Public**.
3. Upload the edited `index.html` file to this repo.

### Step 3 – Enable GitHub Pages
1. In the repo, go to **Settings** → scroll to **Pages** (left sidebar).
2. Under **Source**, select **Deploy from a branch**.
3. Choose **main** branch and **/ (root)** folder → click **Save**.
4. Wait ~1 minute. GitHub will show your live URL:
   ```
   https://YOUR-USERNAME.github.io/reelsave/
   ```

🎉 **Your website is now live!**

---

## Notes

- **First visit after inactivity:** Render's free tier "spins down" after 15 minutes of no traffic. The first download after a break may take 30–60 seconds while the server wakes up. This is normal.
- **Storage:** Downloaded videos are stored temporarily on the server and deleted after 10 minutes automatically.
- **Custom domain:** You can point any domain you own to GitHub Pages in the Pages settings.
- **Personal use only:** Only download content you own or have the right to download.
