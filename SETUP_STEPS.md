# Complete Setup — Click by Click (Roman Urdu)

## ⚡ Sabse aasan tarika (GitHub ke bina)

Aapke phone (Termux) se hi chal sakta hai. Sirf 3 commands:

```bash
cd ~/yt-auto
./setup_env.sh      # 4 values bharein (nano khul jayega)
./run_now.sh        # abhi test video upload
```

Roz auto ke liye:
```bash
nohup ./termux_daily.sh >/dev/null 2>&1 &
```
(Phone 24/7 on ho to hi reliable — warna neeche GitHub wala tarika best hai.)

**4 values kahan se layein:**

| Value | Link / jagah |
|---|---|
| `GEMINI_API_KEY` (free, recommended) | https://aistudio.google.com/app/apikey → **Create API key** |
| `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` | Google Cloud → **Credentials → OAuth client (Web application)** |
| `GOOGLE_REFRESH_TOKEN` | https://developers.google.com/oauthplayground/ → Authorize → Exchange (neeche Step 4) |

> `LLM_PROVIDER=gemini` rakhein — to OpenAI key ki zarurat nahi.

---

## 🔄 GitHub wala tarika (24/7 reliable, phone band ho to bhi)

Sirf 4 kaam hain. Ek-ek karke karein. ⏱️ ~20 minute.

---

## STEP 1 — Google Cloud project banana

1. Browser me kholein: **https://console.cloud.google.com**
2. Upar **Select a project** → **New Project**
   - Project name: `yt-auto` (koi bhi naam)
   - **Create** dabayein
3. Left menu ☰ → **APIs & Services** → **Library**
4. Search karein: **YouTube Data API v3** → result par click → **Enable**

---

## STEP 2 — OAuth consent screen (ye "Production" wala hai)

1. **APIs & Services** → **OAuth consent screen**
2. User Type: **External** → **Create**
3. Form bharein:
   - App name: `YT Auto Uploader`
   - User support email: aapka Gmail
   - Developer contact information: aapka Gmail
   - **Save and Continue**
4. **Add or remove scopes** → search `youtube.upload` → `https://www.googleapis.com/auth/youtube.upload` ko select karein → **Update** → **Save and Continue**
5. **Test users** → **Add users** → apna Gmail daalein → **Save and Continue**
6. Ab upar **Publishing status** me **Testing** likha hoga → uske paas **Publish App** / **Switch to Production** click karein → confirm.
   - ⚠️ Ye **token ko public nahi karta**. Sirf consent screen publish hoti hai. Token private rahega.
   - Unverified warning aaye to "Advanced → Continue (unsafe)" — khud ka account hai, theek hai.

---

## STEP 3 — OAuth client ID banana

1. **APIs & Services** → **Credentials** → **+ Create Credentials** → **OAuth client ID**
2. Application type: **Web application** 👈 (Desktop mat chunna, playground ke liye Web chahiye)
3. Name: `yt-auto-web`
4. **Authorized redirect URIs** → **Add URI** → ye **doonon** daalein:
   ```
   https://developers.google.com/oauthplayground
   http://localhost:8080
   ```
5. **Create** → ek box aayega jisme **Client ID** aur **Client secret** hote hain. Inhe copy kar ke kahin save karein (notepad me).
6. **Download JSON** bhi kar lein → file ko `~/yt-auto/secrets/client_secret.json` me save karein (`secrets` folder pehle se banana padega: `mkdir -p ~/yt-auto/secrets`).

---

## STEP 4 — Refresh token banana (browser se, 2 minute)

1. Kholein: **https://developers.google.com/oauthplayground/**
2. Upar right me **⚙️ (Settings)** click karein → ✅ **Use your own OAuth credentials** par tick → STEP 3 wali **Client ID** aur **Client secret** paste karein → **Close**
3. Left panel **Step 1: Select & authorize APIs**
   - List me **YouTube Data API v3** expand karein
   - `https://www.googleapis.com/auth/youtube.upload` par click karein
   - **Authorize APIs** dabayein
4. Google sign-in page aayega → apna account chunein → **Allow** karein
5. Ab **Step 2: Exchange authorization code for tokens** → **Exchange authorization code for tokens** click karein
6. **Refresh Token** wali value copy karein 👈 yahi `GOOGLE_REFRESH_TOKEN` hai.

> Alternate (Python se): `cd ~/yt-auto && python -m src.auth_setup` — isme local google libraries chahiye. Browser wala tarika aasan hai.

---

## STEP 5 — OpenAI API key

1. **https://platform.openai.com/api-keys** kholein
2. **Create new secret key** → name `yt-auto` → key copy karein.
3. ⚠️ Key sirf ek dafa dikhti hai — abhi save kar lein.

---

## STEP 6 — GitHub repo aur Secrets

### 6a. Repo banana
1. **https://github.com/new** kholein
2. Repository name: `yt-auto` → **Private** ✅ recommended → **Create repository**

### 6b. Code upload karein (Termux me)
```bash
cd ~/yt-auto
git init
git add .
git commit -m "setup"
git remote add origin https://github.com/<AAPKA_USERNAME>/yt-auto.git
git push -u origin main
```
> GitHub kabhi-kabhi `master` default banata hai. Error aaye to: `git branch -M main` phir dobara push.

### 6c. 4 Secrets daalein
Repo me: **Settings** → left me **Secrets and variables** → **Actions** → **New repository secret**

| Name | Value (kahan se mili) |
|---|---|
| `OPENAI_API_KEY` | STEP 5 |
| `GOOGLE_CLIENT_ID` | STEP 3 |
| `GOOGLE_CLIENT_SECRET` | STEP 3 |
| `GOOGLE_REFRESH_TOKEN` | STEP 4 |

Exact same naam — spelling/g-case matter karta hai.

---

## STEP 7 — Pehla test (manual)

1. Repo me **Actions** tab → left me **Daily YouTube Video** → right me **Run workflow** → **Run workflow**
2. 2-4 minute wait karein. Dot/check mark aayega.
   - ❌ Red cross aaye → workflow par click karke log dekhein, error niche STEP 9 me.
   - ✅ Green check → apne channel par jayein → **Videos → Unlisted** me video milega.
3. Video dekhein: awaaz, text, timing theek hai?

---

## STEP 8 — Public karna (viral ke liye zaroori)

`config.yaml` me👇 change karein:

```yaml
privacy_status: "public"   # pehle "unlisted" tha
```

GitHub par change karne ke do tarike:
- GitHub web me `config.yaml` kholein → pencil ✏️ → line badlein → **Commit changes**
- Ya Termux me: `nano ~/yt-auto/config.yaml` → badlein → `git add config.yaml && git commit -m "go public" && git push`

Uske baad har video **public** aayega.

---

## STEP 9 — Common errors

| Error | Fix |
|---|---|
| `invalid_grant` / token expire | Consent screen **Production** me hai? Nahi to STEP 2 dobara. Phir STEP 4 se naya token. |
| `quotaExceeded` | Default 10,000/day, 1 video ~1,600 — roz 1 safe hai. 6+ video na karein. |
| `403: insufficient permissions` | Scope `youtube.upload` add kiya? Consent screen me scope check karein. |
| OpenAI `401` | Secret me key galat/expires. Nayi key banayein. |
| Workflow red | Actions → click → log me exact error dekhein. |
| Video na dikhe | `privacy_status` dekhein — `unlisted` hai to sirf link se chalega. |

---

## 🕐 Timing

`daily.yml` me cron: `30 1 * * *` = **01:30 UTC = 06:30 PKT** (Pakistan).

Badalna ho to UTC me likhein:
- 08:00 PKT = `03:00 UTC` → cron `0 3 * * *`
- 20:00 PKT = `15:00 UTC` → cron `0 15 * * *`

---

## ✅ Final checklist

- [ ] YouTube Data API v3 enabled
- [ ] Consent screen **In Production**
- [ ] Web client + 2 redirect URIs
- [ ] Refresh token mil gaya
- [ ] OpenAI key mil gayi
- [ ] GitHub repo (private) + 4 Secrets
- [ ] Manual Run workflow → green ✅
- [ ] Video unlisted me dekha
- [ ] `privacy_status: "public"` kiya

Bas. Uske baad system **khud** roz video banayega aur upload karega. 🎬
