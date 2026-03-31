# ARTSY – Youth Art Gallery Prototypey

- Web gallery for African art
- Accounts as **Artist** or **Viewer**
- Artists can upload artworks (single image per artwork)
- Viewers can browse gallery
- In-app **chat space** between users (similar idea to Facebook / IG DMs)
- **No payment / transaction / delivery features** (removed on purpose)
- Demo video Link : https://drive.google.com/file/d/13b0OCJBJV7GmMg2iBt4uS_gcDfRkJ_2h/view?usp=drive_link
- Live URL:

## Structure

- `backend/` – Flask API (auth, artworks, chat)
- `frontend/` – React + Vite single-page app (gallery, auth, chat UI)

## Run locally

### Backend (Flask)

From the `ARTSY` folder:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
export $(cat .env | xargs)

python app.py
```

Backend runs at `http://localhost:4000`.

### Frontend (React + Vite)

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### Quick test flow

- Register an **Artist** account and login
- Upload an artwork (file upload from your computer)
- Go to **Gallery** and confirm the image appears
- Register a **Viewer** account and login
- Open an artwork and click **Chat with artist about this piece**
- Send messages in the **Chat** page (purchase discussion happens in chat; no transactions in-app)

