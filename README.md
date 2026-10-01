# Help Narek — fundraising website

A static website for Narek Grigoryan's Elevidys gene therapy fundraiser. It's built with [Eleventy](https://www.11ty.dev/), and the output in `_site/` is plain HTML, CSS and a little JavaScript, so it can be hosted anywhere for free.

The site is in three languages: English (`/en/`), Armenian (`/hy/`) and Russian (`/ru/`). See [Languages](#languages).

## Run it locally

```bash
npm install
npm start          # http://localhost:8080, rebuilds on every save
npm run build      # writes the finished site to _site/
```

## Filling in the missing information

All content lives in `src/_data/`. Anything still unknown is written as `"TODO: …"`:

- on the page it shows as a yellow **✎ chip** or a striped box, so gaps are easy to spot;
- every build prints a list of everything still marked TODO, and says **"No TODOs left — ready to publish"** when nothing is left.

| What is missing | Where |
| --- | --- |
| Site address (needed for link previews) | `site.json` → `url` |
| Amount raised + date | `campaign.json` → `raised` |
| Goal in US dollars | `campaign.json` → `goal.approx` |
| Cost breakdown + source document | `campaign.json` → `costs` |
| Planned treatment date | `campaign.json` → `treatment.targetDate` |
| Bank names for the AMD / USD / EUR cards | `campaign.json` → `payments` |
| SWIFT details for donors abroad | `campaign.json` → `payments` (the `swift` entry) |
| Family contacts | `campaign.json` → `contacts` |
| Video from the family | `campaign.json` → `video` (YouTube video ID) |
| Photos of Narek | `campaign.json` → `photos` (see below) |
| Hospital cost estimate scan | `documents.json` → the `invoice` entry |
| Launch date for the news list | `updates.json` → first entry |
| Narek today, parents' message, Tatevik's relation to Narek, surplus promise, organiser | `i18n/en.json` (search for `TODO`) |

**Optional things you don't need:** delete the line or entry. For example, remove `instagram` from `contacts`, remove `treatment.targetDate`, or remove the whole `swift` entry from `payments`. The page adapts.

### Updating the amount raised

In `src/_data/campaign.json`:

```json
"raised": { "amount": 12500000, "updated": "2026-10-15" }
```

`amount` is a plain number in the goal currency (RUB). The progress bar and percentage update automatically. For news, add an entry at the top of `src/_data/updates.json`.

### Photos and video

1. Save the photos, about 1200 px wide, as JPG in `src/assets/img/photos/`.
2. List them in `campaign.json`:

```json
"photos": [
  { "src": "/assets/img/photos/1.jpg", "alt": { "en": "Narek on his way to school" } },
  { "src": "/assets/img/photos/2.jpg", "alt": { "en": "Narek with his mother" } }
]
```

For the video, upload it to YouTube (as unlisted if you prefer) and put its ID in `campaign.json` → `video`. For example, the ID in `https://youtu.be/AbC123xyz` is `AbC123xyz`.

## Languages

All text lives in `src/_data/i18n/en.json`, `hy.json` and `ru.json`, and each file has the same keys.

- **Changing text:** edit the same key in all three files. Keep `{placeholders}` such as `{age}` and `{goal}` as they are. A key missing from `hy.json` or `ru.json` falls back to English.
- **News and photo descriptions:** these live in `updates.json` and `campaign.json` → `photos`, with `"en"`, `"hy"` and `"ru"` side by side.
- **Social preview images:** after changing the `og` texts or the goal, run the script once per language:

  ```bash
  powershell -ExecutionPolicy Bypass -File tools\make-og-image.ps1 -Lang hy
  ```

- **Which language opens first:** the bare domain `/` opens the language the visitor last chose, otherwise their browser's language, otherwise `defaultLanguage` from `src/_data/site.json` (currently English).
- **Turning a language off:** set `enabled: false` in `src/_data/languages.js`.
- **Adding another language:** copy `en.json` to `<code>.json`, translate it, and add the language to `languages.js`.

## Social preview image

`src/assets/img/og/og-en.jpg` is the picture WhatsApp, Telegram, Facebook and others show when the link is shared. It is built from the `og` texts in `i18n/<lang>.json` and the goal in `campaign.json`. Run `tools\make-og-image.ps1` again after changing either.

## Publishing on GitHub Pages (current setup)

The site is published by `.github/workflows/deploy.yml`. Every push to `main` builds it and deploys it to **https://aghas-mh.github.io/Narek/**, and the bare address sends visitors to `/en/`, `/hy/` or `/ru/`.

One-time setup on github.com:

1. **Repository visibility.** On a free GitHub plan, Pages only works for public repositories (**Settings → General → Danger zone → Change visibility**). With GitHub Pro the repository can stay private; the site is public either way.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
3. Open **Actions → Deploy to GitHub Pages → Run workflow**, or push any change.

The workflow sets the `/Narek/` path prefix and the full site address automatically, so links and social previews work without editing `site.json`. If you later add a custom domain (Settings → Pages → Custom domain), the next deploy picks it up on its own. GitHub Pages ignores the `_headers` security file.

## Publishing on Cloudflare Pages (alternative, free)

1. Put this folder in a GitHub repository (it can be private).
2. In Cloudflare, open **Workers & Pages → Create → Pages → Connect to Git**, pick the repository, and set:
   - Build command: `npm run build`
   - Build output directory: `_site`
3. Add your custom domain in Cloudflare, then set `site.json` → `url` to it (e.g. `https://helpnarek.org`). Link previews need the full address.
4. Share the link in WhatsApp or Telegram to check the preview. For Facebook, use the [Sharing Debugger](https://developers.facebook.com/tools/debug/).

After that, every change pushed to GitHub, including edits made directly on github.com, republishes the site in about a minute. Netlify works the same way.

## Before launch

- [ ] The build reports **no TODOs left**.
- [ ] The family has read every text and agreed to publishing the photos and documents.
- [ ] A doctor or the family has checked the medical statements (treatment, eligibility, risks, costs).
- [ ] Every card number and bank detail has been checked against the bank app. The four card numbers were copied from the poster and pass the card-number checksum.
- [ ] The link preview looks right in WhatsApp, Telegram and Facebook.

## Privacy notes

- On `src/assets/docs/recommendations.jpg`, the Moscow doctor's **personal phone number and Gmail address are blacked out**. The originals in `Documents\Narek` are not used by the site.
- The Medcare letter (image and PDF) keeps Dr Mundada's **work** email, because the letter invites questions. Remove the PDF from `documents.json` if you would rather not publish it.
- The site sets no cookies, has no trackers and loads nothing from other websites (except the YouTube video, once one is added).

## Project structure

```
src/
  _data/
    site.json          site address, default language
    campaign.json      goal, amount raised, payment details, contacts, photos, video
    documents.json     medical documents shown on the page
    updates.json       news list
    languages.js       which languages are published
    i18n/en.json       all English text (copy it to hy.json / ru.json to translate)
  _includes/           page layout, sections and icons (Nunjucks templates)
  assets/              CSS, JS, images, document scans
  campaign.njk         the main page, built once per language (/en/, /hy/, /ru/)
  index.njk            the bare domain: redirects to the visitor's language
  404.njk              "page not found"
  _headers             security headers for Cloudflare Pages / Netlify
lib/helpers.js         formatting helpers (money, dates, age, TODO detection)
tools/make-og-image.ps1  creates the social preview image
eleventy.config.js     build configuration and the TODO report
```
