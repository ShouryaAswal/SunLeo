# SunLeo

Free and opensource music downloader and recommender website

## Project Overview

SunLeo is a unified web application utilizing **Streamlit** for the frontend and **FastAPI** for the backend, allowing users to download music via YouTube URL links. It also features a Discovery page that is securely gated behind a **Google OAuth** login system.

## Setup Instructions

Want to run this project locally? Follow the steps below:

### 1. Prerequisites

- **Python 3.9+** installed on your system.
- **Git** to clone the repository.
- A **Google Cloud Platform (GCP)** account to generate OAuth Client credentials.

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/SunLeo.git
cd SunLeo
```

### 3. Set Up the Virtual Environment

We recommend using a virtual environment to manage dependencies securely.

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies

Install the required packages for both the frontend and backend.

```bash
pip install -r requirements.txt
pip install -r backend/ytconverter/requirements.txt
```

### 5. Environment Variables & Authentication

You will need to set up Google OAuth for the login and discovery features to work.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project and configure the OAuth consent screen.
3. Generate **OAuth 2.0 Client IDs**.
4. Add the redirect URI: `http://localhost:8501/`
5. Place your keys in local environment variables (`.env`) or generate the required `google_secret.json` structure inside `frontend/app/`.

### 6. Run the Backend (FastAPI)

The backend handles the music downloading (`yt-dlp`) and API serving. From the root of the project, run:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend/ytconverter
```

### 7. Run the Frontend (Streamlit)

To start the User Interface, open a new terminal window, activate your `.venv` again, and run:

```bash
streamlit run frontend/app/home.py
```

The app will become available in your browser at `http://localhost:8501`.
