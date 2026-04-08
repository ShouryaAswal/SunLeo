# Firebase Authentication Setup Guide for SunLeo

## Step 1: Create a Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Click **"Create a project"** (or select an existing one)
3. Enter a project name (e.g., `SunLeo`) and click **Continue**
4. Optionally enable Google Analytics, then click **Create Project**
5. Wait for creation to complete, then click **Continue**

## Step 2: Enable Google Sign-In

1. In the Firebase Console sidebar, click **Build → Authentication**
2. Click **"Get started"**
3. Go to the **Sign-in method** tab
4. Click **Google** from the providers list
5. Toggle **Enable** to ON
6. Select a project support email from the dropdown
7. Click **Save**
8. (Optional) Also enable **Email/Password** if you want email login too

## Step 3: Register a Web App

1. In your Firebase project, click the **gear icon** → **Project settings**
2. Scroll down to **"Your apps"** and click the **Web icon** (`</>`)
3. Enter an app nickname (e.g., `SunLeo Web`) and click **Register app**
4. Firebase will show you a config object like this:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "sunleo-xxxxx.firebaseapp.com",
  projectId: "sunleo-xxxxx",
  storageBucket: "sunleo-xxxxx.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123def456"
};
```

5. **Copy these values** — you'll need them for the `.env` file

## Step 4: Configure Your `.env` File

Open (or create) the `.env` file in the **root** of the SunLeo project and add:

```env
# Firebase Auth Configuration
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=sunleo-xxxxx.firebaseapp.com
FIREBASE_PROJECT_ID=sunleo-xxxxx
FIREBASE_STORAGE_BUCKET=sunleo-xxxxx.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abc123def456
```

Replace each value with the ones you copied from the Firebase console.

## Step 5: Add Authorized Domains

1. In Firebase Console → **Authentication → Settings**
2. Under **Authorized domains**, make sure `localhost` is listed
3. If deploying, add your production domain here too

## Step 6: Run the App

```powershell
.\run_app.ps1
```

Click **Login** on the home page → a dialog popup will appear with Google Sign-In → authenticate → you're logged in!

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Auth domain not authorized" | Add `localhost` to Firebase → Authentication → Settings → Authorized domains |
| Login popup doesn't appear | Ensure FIREBASE_API_KEY is set correctly in `.env` |
| Google sign-in button missing | Verify Google provider is enabled in Firebase Console |
| `streamlit-firebase-auth` import error | Run `pip install streamlit-firebase-auth` |
