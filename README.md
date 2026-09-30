# Help Narek — fundraising website

A static website for Narek Grigoryan's Elevidys gene therapy fundraiser. It's built with [Eleventy](https://www.11ty.dev/), and the output in `_site/` is plain HTML, CSS and a little JavaScript, so it can be hosted anywhere for free.

English is live. Armenian and Russian are ready to add (see [Adding Armenian or Russian](#adding-armenian-or-russian)).

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

## Adding Armenian or Russian

1. Copy `src/_data/i18n/en.json` to `hy.json` (Armenian) or `ru.json` (Russian) and translate the **values**. Keep the keys and the `{placeholders}` such as `{age}` and `{goal}`. Anything left untranslated falls back to English.
2. In `src/_data/languages.js`, set `enabled: true` for that language.
3. In `src/_data/updates.json`, add the translated news next to `"en"`, e.g. `"hy": "…"`.
4. Create the social preview image for the new language:

   ```bash
   powershell -ExecutionPolicy Bypass -File tools\make-og-image.ps1 -Lang hy
   ```

The page appears at `/hy/` or `/ru/` and the language switcher shows up in the header. The bare domain `/` sends each visitor to their browser's language. To make Armenian the fallback language, set `defaultLanguage` in `src/_data/site.json`.

## Social preview image

`src/assets/img/og/og-en.jpg` is the picture WhatsApp, Telegram, Facebook and others show when the link is shared. It is built from the `og` texts in `i18n/<lang>.json` and the goal in `campaign.json`. Run `tools\make-og-image.ps1` again after changing either.

## Publishing (Cloudflare Pages, free)

1. Put this folder in a GitHub repository (it can be private).
2. In Cloudflare, open **Workers & Pages → Create → Pages → Connect to Git**, pick the repository, and set:
   - Build command: `npm run build`
   - Build output directory: `_site`
3. Add your custom domain in Cloudflare, then set `site.json` → `url` to it (e.g. `https://helpnarek.org`). Link previews need the full address.
4. Share the link in WhatsApp or Telegram to check the preview. For Facebook, use the [Sharing Debugger](https://developers.facebook.com/tools/debug/).

After that, every change pushed to GitHub, including edits made directly on github.com, republishes the site in about a minute. Netlify works the same way. GitHub Pages also works but ignores the `_headers` security file.

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
