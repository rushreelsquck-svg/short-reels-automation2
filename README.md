# Daily Trending Shorts Bot

Automatically builds a short, original news-recap video based on a real trending
story each day, and uploads it to your YouTube channel — running for free on
GitHub Actions.

**Read this whole file before turning it on.** A few things below (privacy
status, OAuth publishing) directly affect whether this works at all.

---

## What this actually does (and doesn't do)

- ✅ Picks a real trending headline each day (Google News), writes an original
  ~50-second script about it with Claude, generates a voiceover, builds a
  vertical video with captions, and uploads it to YouTube via the official API.
- ✅ Uses only royalty-free assets (a synthetic animated background by default,
  or optional Pexels stock footage; music you supply from royalty-free sources).
- ❌ Does **not** guarantee views. No automation can. What gets a video watched
  is whether people find it useful/interesting in the first 2 seconds — tags
  and hashtags help discovery, they don't manufacture demand.
- ❌ Does **not** scrape or re-upload anyone else's video/footage. It writes an
  original script about a news event, which is what keeps it copyright-clean.
- ⚠️ Runs unattended once set up, but **start with `YT_PRIVACY_STATUS=unlisted`**
  (already the default) and watch a few outputs before flipping it to `public`.
  YouTube has also tightened policy on mass-produced/repetitive "faceless"
  channels — keep an eye on your channel's monetization status if that matters
  to you, and consider occasionally customizing the format so it doesn't look
  like a pure bot feed.

---

> **Already have a working repo for another channel?** You can skip almost
> all of this. Reuse your existing `ANTHROPIC_API_KEY`, `YT_CLIENT_ID`,
> `YT_CLIENT_SECRET`, `YT_API_KEY`, and `PEXELS_API_KEY` exactly as they are —
> none of those are tied to a specific channel or repo. The only new thing you
> need is a fresh `YT_REFRESH_TOKEN` authorized by *this* channel's Google
> account — jump straight to **Step 2**, just log into the new channel when
> the browser opens instead of the original one. Then skip to **Step 4** to
> push this as its own new repo and add the secrets (all six, even the
> reused ones — secrets don't carry over between repos).

---

## Step 1: Google Cloud setup (YouTube API access)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a new project.
2. **APIs & Services → Library** → search "YouTube Data API v3" → Enable.
3. Open **Google Auth Platform** (search for it in the console's top search bar,
   or find it in the left menu — Google moved this out of the old single-page
   "OAuth consent screen" into a few separate tabs):
   - **Branding** tab: fill in app name, your email, etc.
   - **Audience** tab: set User type to **External**, and add yourself under "Test users."
   - **Data Access** tab: click **"Add or remove scopes"**, search "youtube",
     check the box for `.../auth/youtube.upload` (it'll only show up if you
     already enabled the YouTube Data API in step 2), click **Update**, then **Save**.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Desktop app**
   - Save the Client ID and Client Secret.
5. **(Optional but recommended) Create a separate API key** (Credentials →
   Create Credentials → API key) for read-only trending lookups — this becomes
   `YT_API_KEY`, separate from the OAuth Client ID/Secret used for uploads.

### The 7-day token trap

If your app is left in **"Testing"** status, your refresh token **expires
every 7 days** and the bot will silently fail after a week. Fix: go to
**Google Auth Platform → Audience** tab and click **"Publish App"** to move
it to **Production**.

This is separate from the "unverified app" warning below — that one shows up
later, during Step 2, when you (the actual human) log in through the browser
to authorize the app for the first time. `youtube.upload` is classified by
Google as a *sensitive* scope rather than a *restricted* one, which is why a
single personal-use account can click past that warning without needing
Google's full verification review (that's really meant for public apps with
many users).

---

## Step 2: Get your refresh token (run locally, once)

Use the folder you already have from unzipping `trend-shorts-bot.zip` —
no need to clone anything yet, since you already have the files.

**Windows — Command Prompt:**
```bat
cd path\to\trend-shorts-bot
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt

set YT_CLIENT_ID=your-client-id
set YT_CLIENT_SECRET=your-client-secret
venv\Scripts\python.exe scripts\get_oauth_token.py
```

**Windows — PowerShell:**
```powershell
cd path\to\trend-shorts-bot
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt

$env:YT_CLIENT_ID = "your-client-id"
$env:YT_CLIENT_SECRET = "your-client-secret"
venv\Scripts\python.exe scripts\get_oauth_token.py
```

> Both of these call the venv's `python.exe` directly instead of "activating"
> it first. It does the same thing for a one-off script like this, and skips
> the cmd-vs-PowerShell activation differences entirely (PowerShell in
> particular often blocks `Activate.ps1` with an execution-policy error).

**Mac / Linux / Git Bash:**
```bash
cd path/to/trend-shorts-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export YT_CLIENT_ID="your-client-id"
export YT_CLIENT_SECRET="your-client-secret"
python3 scripts/get_oauth_token.py
```

A browser window opens — log in with the Google account that owns your
YouTube channel. You'll likely hit a **"Google hasn't verified this app"**
screen here — that's expected for an app only you use. Click the small
**"Advanced"** link, then **"Go to [your app name] (unsafe)"**, then approve
access on the next screen. The script then prints a refresh token. Copy it;
you'll need it in Step 4.

---

## Step 3: Get an Anthropic API key

Create one at [console.anthropic.com](https://console.anthropic.com) →
Settings → API Keys. This is billed separately from any Claude.ai
subscription — each video costs roughly a fraction of a cent in API usage.

---

## Step 4: Push this to GitHub and add your secrets

1. On [github.com](https://github.com), click **New repository**. Give it any
   name, set it to **Private**, and leave it **empty** — don't check "Add a
   README" (that creates a conflict with the files you already have locally).
2. GitHub will show you a URL like `https://github.com/yourname/your-repo.git`.
   From inside your local `trend-shorts-bot` folder (the same one from Step 2):

   ```bat
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourname/your-repo.git
   git push -u origin main
   ```

   Git will prompt you to log in to GitHub the first time — follow whatever
   prompt it gives you (browser popup or a personal access token).
3. In that repo on GitHub: **Settings → Secrets and variables → Actions →
   New repository secret**. Add each of these:

   | Secret name | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | from Step 3 |
   | `YT_CLIENT_ID` | from Step 1 |
   | `YT_CLIENT_SECRET` | from Step 1 |
   | `YT_REFRESH_TOKEN` | from Step 2 |
   | `YT_API_KEY` | from Step 1 (optional — enables trending-tag enrichment) |
   | `PEXELS_API_KEY` | recommended — turns on real stock footage instead of the gradient background (see "Real visuals" below) |

3. (Optional) Drop 2-5 royalty-free mp3s into `assets/music/` and commit them
   — see `assets/music/README.txt` for where to get them legally.

---

## Step 5: Test it manually before trusting the schedule

Go to your repo's **Actions** tab → "Daily Trending Short" → **Run workflow**.
Watch the log. If it succeeds, check the unlisted video on your channel
before changing anything to public. Common first-run issues:

- `gTTSError` → usually a transient rate limit from the free TTS endpoint; rerun.
- `invalid_grant` on upload → refresh token expired (see the 7-day trap above) or wasn't copied correctly.
- Pexels step silently skipped → fine, it just falls back to the gradient background if no key/clip is found.

Once you're happy with the output, go back to repo Secrets and you can leave
`YT_PRIVACY_STATUS` as `unlisted` permanently, or change the default in the
workflow file to `public` once you trust it.

---

## Real visuals (instead of the gradient background)

By default, the background is a fully synthetic animated gradient — zero
licensing risk, always works, but plain. To get real stock footage instead:

1. Sign up free at [pexels.com/api](https://www.pexels.com/api/) and grab an API key.
2. Add it as the `PEXELS_API_KEY` repo secret (see Step 4 above).

That's it — nothing else to configure. Once that key is set, Claude picks 3-4
short, concrete visual phrases for each story (e.g. "oil refinery", "diplomats
shaking hands") as part of writing the script, and the video cuts between a
real clip for each one instead of looping a single background for the whole
thing. If a specific clip can't be found for a given phrase, that one segment
quietly falls back to the gradient — the run never breaks because of it.

Pexels' free tier is generous enough that you won't need to think about rate
limits for a once-a-day video.

---

## Customizing

- **Topic source**: `scripts/fetch_trend.py` uses Google News RSS. Swap the
  feed URL for a specific topic (e.g. `/rss/headlines/section/topic/TECHNOLOGY`)
  if you want a niche instead of general news.
- **Voice quality**: `scripts/generate_audio.py` uses free gTTS. For a much
  better voice, swap in ElevenLabs or Azure TTS (both are simple REST calls) —
  keep the same function signature so nothing else needs to change.
- **Visual style**: `scripts/build_video.py`'s `_make_gradient_background()`
  and `_render_caption_png()` control the look — colors, font, caption box
  styling are all editable there. The number of background clips per video
  follows however many `visual_queries` Claude returns (3-4 by default) —
  adjust the count in `generate_script.py`'s system prompt if you want more
  or fewer cuts.
- **Schedule**: edit the cron line in `.github/workflows/daily-short.yml`.
  [crontab.guru](https://crontab.guru) helps build the expression.

---

## Costs

- GitHub Actions: free for this (well under the free-tier minutes for a public
  or personal private repo on a daily schedule).
- Anthropic API: a few hundred tokens per video — a fraction of a cent each.
- Everything else (Google News, YouTube Data API, gTTS, Pexels free tier) is free.
