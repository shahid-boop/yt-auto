# yt-auto — roz ka automatic YouTube video

Har din ek short faceless video banata hai (script → Urdu voiceover → slides → MP4).

## ⚠️ Abhi mode: MANUAL UPLOAD (aap upload karte hain)

Upload ke liye Google OAuth setup abhi pending hai — isliye system **sirf video banata hai**, upload nahi karta. Aap bas `out/` folder se video utha kar YouTube Studio me upload kar dein.

### Abhi video chahiye?
```bash
cd ~/yt-auto && ./daily_local.sh --now
```

### Roz apne aap 06:30 par video banayein
```bash
cd ~/yt-auto
nohup ./daily_local.sh >/dev/null 2>&1 &
```

- Videos: `~/yt-auto/out/`
- **Phone Download folder:** `/storage/emulated/0/Download/YouTubeAuto/` (video + thumbnail PNG dono)
- Har video ke saath 1280x720 thumbnail banti hai aur MP4 me cover art ke tor par embed hoti hai
- Log: `~/yt-auto/logs/daily.log`
- Rokne ke liye: `pkill -f daily_local.sh`

### Baad me auto-upload chalana ho
Google OAuth se refresh token milte hi `.env` me daalein aur:
```bash
python -m src.pipeline --upload
```
Ya GitHub Actions wala workflow（`--upload` wala）dobara enable kar dein.

## Channel (verify ho gaya)

- **Naam:** Mind Secrets Urdu
- **Handle:** [@MindSecrets-Urdu](https://www.youtube.com/@MindSecrets-Urdu)
- **Channel ID:** `UCc4vGXpDG_b4ssVYa2-X1hQ`
- **Subscribers:** 67 | **Total views:** 1,097 | **Joined:** May 2020
- **Public videos:** 0 (bilkul fresh start — spam risk nahi, lekin 30 din consistency zaroori)

`config.yaml` me channel name pehle se isi ke hisaab se hai.

## Local test (already pass ✅)

```bash
python -m src.doctor
python -m src.pipeline --offline --topic "Koi topic"
```
Sample output: `out/video_20261121_095357.mp4` — 1280x720, 24fps, H.264 + AAC, ~25 sec, 0.3 MB.
Slide rendering **ffmpeg drawtext** se hoti hai — Pillow ki zarurat nahi. Subtitle isliye nahi jalate kyunki slide text hi on-screen caption hai (duplicate text aur Urdu font issue dono khatam).

## 1. Setup (ek dafa)

### A. Google Cloud / YouTube API
👉 **Poori click-by-click guide: [SETUP_STEPS.md](SETUP_STEPS.md)** — pehle wahan se Step 1-4 karein.

Summary:
1. https://console.cloud.google.com par project → `YouTube Data API v3` enable.
2. OAuth consent screen: **External**, scope `youtube.upload`, test user = aapka Gmail, phir **In Production**.
3. OAuth client type: **Web application** + redirect URIs:
   - `https://developers.google.com/oauthplayground`
   - `http://localhost:8080`
4. JSON download → `secrets/client_secret.json`.

> ⚠️ **Zaroori — token ko "lifetime" banane ka tarika:**
> OAuth consent screen ko **"In Production"** par publish karein. **Dhyan dein: yeh token ko public nahi karta** — token sirf aapke GitHub Secrets me rehta hai. "Production" ka matlab sirf itna hai ke consent screen dusre users ke liye bhi available ho jata hai.
>
> | App status | Refresh token life |
> |---|---|
> | External + Testing | **7 din** (auto expire) |
> | External + Production | Long-lived (6 mahine tak unused na ho) |
> | Internal (Workspace) | Long-lived |
>
> Khud hi verify karne ki zarurat nahi — sirf apna account use kar rahe ho to "unverified app" warning par **Advanced → Continue** karke access de sakte ho. Testing mode me rakhna hai to har 7 din me `python -m src.auth_setup` dobara chalana padega.
>
> Channel ke liye: pehle 2-3 videos **unlisted** rakhein review ke liye (`config.yaml` me `privacy_status: "unlisted"`), uske baad **public** kar dein — viral hone ke liye public zaroori hai.

### B. Refresh token
**Aasan tarika (browser):** https://developers.google.com/oauthplayground/ → settings ⚙️ me apni Client ID/Secret daalein → scope `youtube.upload` select → Authorize → Exchange → **Refresh Token** copy. (Detail: `SETUP_STEPS.md` Step 4)

**Python tarika:**
```bash
cd ~/yt-auto && python -m src.auth_setup
```
- URL print hoga → browser me kholein → access dein → `localhost:8080` pe redirect.
- Refresh token print hoga → GitHub Secret `GOOGLE_REFRESH_TOKEN` me daalein.

### C. OpenAI key
https://platform.openai.com/api-keys se key banayein → GitHub Secret `OPENAI_API_KEY`.

### D. GitHub repo
```bash
git init
git add .
git commit -m "initial"
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```
Repo → **Settings → Secrets and variables → Actions** me 4 secrets daalein:

| Secret | Value |
|---|---|
| `OPENAI_API_KEY` | OpenAI key |
| `GOOGLE_CLIENT_ID` | OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret |
| `GOOGLE_REFRESH_TOKEN` | auth_setup se mila token |

## 2. Apna niche set karein

`config.yaml` me:
- `content.niche`, `content.audience`, `content.tone` — apne channel ke hisaab se badlein.
- `tts.voice` — `ur-PK-AsadNeural` (Urdu male), `ur-PK-UzmaNeural` (Urdu female), `hi-IN-SwaraNeural` (Hindi), `en-US-AriaNeural` (English). `edge-tts --list-voices` se poori list dekhein.
- `channel.category_id` — 22 People & Blogs, 27 Education, 28 Science & Tech.
- `.github/workflows/daily.yml` me cron time UTC me hota hai.

`data/topics.json` me topics list hai — system inme se roz ek chunta hai (repeat se bachta hai). Naye topics wahin add karein.

## 3. Test (upload ke bina)

```bash
python -m src.pipeline --offline --topic "AI tips"   # API key ke bina
python -m src.pipeline --topic "AI tips"              # OpenAI se script
python -m src.pipeline --upload                       # upload bhi karega
```

Output MP4 `out/` me save hota hai. Har run ki entry `data/history.json` me jaati hai.

## 4. Auto run

GitHub Actions har din UTC 01:30 (`= 06:30 PKT`) par chalega. Manual test ke liye repo ke **Actions → Daily YouTube Video → Run workflow**.

## Important notes

- **Voiceover ke liye Urdu/Hindi script** use hoti hai (LLM khud generate karta hai), aur **onscreen text Roman Urdu** me hota hai — isliye font issue nahi aata.
- YouTube default quota 10,000 units/day; ek video upload ~1,600 units → roz 1 video bilkul safe.
- Fully auto upload allowed hai, lekin **low-quality / repetitive content** YouTube ki spam policy ke khilaf ho sakta hai. Pehle 10 videos manually review karein, phir 100% auto karein.
- Kabhi bhi API keys ya token chat me ya code me na likhein — sirf GitHub Secrets / env vars me rakhein.
- `secrets/` aur `out/` gitignore me hain — kabhi commit na karein.
