# Google Slides & Drive API Setup Guide

This guide walks you through setting up Google Cloud OAuth 2.0 credentials so the script can automatically copy the master presentation template and generate live Google Slides decks.

---

## 1. Prerequisites
* A Google Cloud account with access to the Google Cloud Console (`https://console.cloud.google.com`).
* A Google account (Google Workspace or personal) that will own the generated Google Slides presentations.

---

## 2. Step-by-Step Setup

### Step 1: Create a Google Cloud Project
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown in the top bar and click **New Project**.
3. Name it `Wiz-Health-Deck-Builder` and click **Create**.

### Step 2: Enable Google Drive and Google Slides APIs
1. In the search bar, search for **Google Drive API** and click **Enable**.
2. Search for **Google Slides API** and click **Enable**.

### Step 3: Configure the OAuth Consent Screen
1. Navigate to **APIs & Services > OAuth consent screen**.
2. Choose **Internal** (if within a Google Workspace organization) or **External**.
3. Fill in the App Name (e.g. `Wiz Deck Builder`) and your user support email.
4. Under **Scopes**, add:
   * `https://www.googleapis.com/auth/presentations`
   * `https://www.googleapis.com/auth/drive`
5. Save and continue.

### Step 4: Create OAuth 2.0 Client ID
1. Navigate to **APIs & Services > Credentials**.
2. Click **+ Create Credentials > OAuth client ID**.
3. Application Type: Select **Desktop App** (or **Web Application** with redirect URI `https://developers.google.com/oauthplayground`).
4. Name: `Wiz Deck CLI`.
5. Click **Create** and copy your **Client ID** and **Client Secret**.

### Step 5: Obtain a Refresh Token
You can obtain a refresh token using the [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground):
1. In OAuth Playground, click the **Settings (Gear Icon)** in the top right.
2. Check **Use your own OAuth credentials** and enter your **Client ID** and **Client Secret**.
3. Under **Step 1**, enter the scopes:
   * `https://www.googleapis.com/auth/presentations`
   * `https://www.googleapis.com/auth/drive`
4. Click **Authorize APIs** and sign in with your Google account.
5. In **Step 2**, click **Exchange authorization code for tokens**.
6. Copy the **Refresh Token**.

---

## 3. Configure Your `.env` File

Add the Google credentials to `.env`:

```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token
QBR_TEMPLATE_ID=1ga4sflsBPZS2lsXi6k6fUY1jU5dOrqQ9bQ1JEp3B5GM
GOOGLE_FOLDER_ID=your_target_google_drive_folder_id
```

---

## 4. Master Template Access

Ensure the Google account associated with your refresh token has **Viewer** or **Editor** access to the master presentation template:
* Master Template ID: `1ga4sflsBPZS2lsXi6k6fUY1jU5dOrqQ9bQ1JEp3B5GM`
