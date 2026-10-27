"""Square 1080x1080 posts for Instagram / Facebook / WhatsApp (Russian or Armenian), in four styles:

  qr-right  photo on the left; headline, price and two QR codes (GoFundMe + website) on the right
  progress  "update" post: photo, amount raised so far with a progress bar, two QR codes
            (rerun whenever "raised" in campaign.json changes)
  alfa      for donors in Russia: Alfa-Bank card, phone for transfers / contact, two QR codes
  details   everything: all cards with account numbers and holders, SWIFT, Idram, GoFundMe, QR codes

    python tools/make-square.py                      # all styles, Russian
    python tools/make-square.py --lang hy            # all styles, Armenian (banner on top, amounts in USD)
    python tools/make-square.py --style qr-right --photo src/assets/img/narek-900.jpg

Writes src/assets/img/square-<style>.jpg (Russian) or square-<style>-hy.jpg (Armenian).
Data comes from src/_data/campaign.json.
Needs Pillow and qrcode, and the Bahnschrift and Segoe UI fonts that ship with Windows 10/11
(Bahnschrift has no Armenian letters, so the Armenian posts use Segoe UI).
"""
import argparse
import json
from datetime import date
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = r"C:\Windows\Fonts\bahnschrift.ttf"
STYLES = ["qr-right", "progress", "alfa", "details"]

parser = argparse.ArgumentParser()
parser.add_argument("--style", choices=STYLES + ["all"], default="all")
parser.add_argument("--photo", default="src/assets/img/life/narek-600.jpg")
parser.add_argument("--focus", type=float, default=0.5, help="horizontal centre of the face in the photo, 0..1")
parser.add_argument("--lang", choices=["ru", "hy"], default="ru")
parser.add_argument("--site", help="defaults to the site page in --lang")
args = parser.parse_args()
args.site = args.site or f"https://aghas-mh.github.io/Narek/{args.lang}/"
HY = args.lang == "hy"

campaign = json.loads((ROOT / "src/_data/campaign.json").read_text(encoding="utf-8"))
payments = {p["id"]: p for p in campaign["payments"]}
GOFUNDME = campaign.get("gofundme", "")

T = {
    "ru": {
        "chip": "Нарек, {age} лет", "kicker": "ПОМОГИТЕ НАРЕКУ", "kicker_age": "ПОМОГИТЕ НАРЕКУ · {age} ЛЕТ",
        "title": "Мой шанс — препарат Elevidys.", "price": "Его цена —",
        "gfm_sub": "оплата картой онлайн", "site": "Сайт Нарека", "site_sub": "реквизиты и документы",
        "raised": "Уже собрано на лечение", "of_goal": "из {goal}", "updated": "обновлено {date}",
        "motto": "Каждый перевод приближает Нарека к лечению",
        "alfa": "Альфа-Банк", "in_rub": "в рублях", "card": "Карта", "account": "Счёт",
        "beneficiary": "Получатель: ", "phone_lead": "Перевод по номеру и связь:", "tel": "Тел.: ",
        "account_sub": "Счёт: ", "swift": "Международный перевод (SWIFT): {bank} · {swift} · получатель {ben}",
        "gfm_short": "онлайн картой",
        "purpose": f"Назначение платежа: {campaign.get('purposeRu', 'На лечение Нарека')}",
        "rows": ["usd", "amd", "eur", "rub"],
    },
    "hy": {
        "banner": ["Օգնեք ինձ", "Նարեկ Գրիգորյան {age} տարեկան", "Դյուշենի մկանային դիստրոֆիա"],
        "title": "Իմ հնարավորությունը՝ Elevidys դեղամիջոցը։", "price": "Դրա արժեքը՝",
        "gfm_sub": "առցանց վճարում քարտով", "site": "Նարեկի կայքը", "site_sub": "վավերապայմաններ և փաստաթղթեր",
        "raised": "Բուժման համար արդեն հավաքվել է", "of_goal": "{goal} նպատակային գումարից", "updated": "թարմացվել է՝ {date}",
        "alfa": "Alfa-Bank", "in_rub": "ռուբլով", "card": "Քարտ", "account": "Հաշիվ",
        "beneficiary": "Ստացող՝ ", "phone_lead": "Փոխանցում հեռախոսահամարով և կապ՝", "tel": "Հեռ.՝ ",
        "account_sub": "Հաշիվ՝ ", "swift": "Միջազգային փոխանցում (SWIFT)՝ {bank} · {swift} · ստացող՝ {ben}",
        "gfm_short": "առցանց քարտով",
        "purpose": "Վճարման նպատակ՝ Նարեկի բուժման համար",
        "rows": ["amd", "usd", "eur", "rub"],
    },
}
L = T[args.lang]
PURPOSE = L["purpose"]

S = 1080
BG, INK, NAVY, MUTED = (244, 245, 249), (3, 22, 62), (16, 43, 86), (78, 90, 118)
WHITE, GREEN, RED, AMBER = (255, 255, 255), (2, 169, 92), (239, 49, 36), (245, 181, 61)
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
          "сентября", "октября", "ноября", "декабря"]
MONTHS_HY = ["հունվարի", "փետրվարի", "մարտի", "ապրիլի", "մայիսի", "հունիսի", "հուլիսի", "օգոստոսի",
             "սեպտեմբերի", "հոկտեմբերի", "նոյեմբերի", "դեկտեմբերի"]
TOP = 150 if HY else 0   # height of the Armenian banner; everything else starts below it
SEGOE = {"Bold": "segoeuib", "SemiBold": "seguisb", "SemiLight": "segoeuisl", "SemiBold SemiCondensed": "seguisb"}


# ---------- helpers ----------
def font(size, style="Bold"):
    if HY:
        return ImageFont.truetype(rf"C:\Windows\Fonts\{SEGOE[style]}.ttf", size)
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_name(style)
    return f


def fit(draw, text, style, size, width):
    while size > 16 and draw.textlength(text, font=font(size, style)) > width:
        size -= 2
    return font(size, style)


def wrap(draw, text, f, width):
    lines, line = [], ""
    for word in text.split(" "):
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=f) <= width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    return lines + [line]


def card(img, box, radius=26, border=None, width=3):
    x0, y0, x1, y1 = box
    shadow = Image.new("L", img.size, 0)
    ImageDraw.Draw(shadow).rounded_rectangle((x0, y0 + 6, x1, y1 + 6), radius, fill=60)
    img.paste(Image.new("RGB", img.size, (150, 160, 190)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(img).rounded_rectangle(box, radius, fill=WHITE, outline=border, width=width if border else 0)


def qr(url, module):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=module, border=0)
    q.add_data(url)
    q.make(fit=True)
    return q.make_image(fill_color=INK, back_color=WHITE).convert("RGB")


def rub(n):
    return f"{n:,}".replace(",", " ") + " ₽"


def money(n):
    """Roubles on Russian posts; on Armenian posts converted to USD with the goal's approx ratio, like the site."""
    if not HY:
        return rub(n)
    usd = next(a["amount"] for a in campaign["goal"]["approx"] if a["currency"] == "USD")
    return "$" + f"{round(n * usd / campaign['goal']['amount']):,}".replace(",", " ")


def when(d):
    return f"{d.year} թ. {MONTHS_HY[d.month - 1]} {d.day}" if HY else f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def age():
    b, t = date.fromisoformat(campaign["child"]["birthDate"]), date.today()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


def cover(path, w, h, focus=0.5, top=0.0):
    """Crop + scale a photo to exactly w x h, keeping the face (focus = its horizontal position)."""
    im = Image.open(ROOT / path).convert("RGB")
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    x = min(max(round(im.width * focus - w / 2), 0), im.width - w)
    y = round((im.height - h) * top)
    return im.crop((x, y, x + w, y + h))


def chip(draw, x, y, text, size=30):
    f = font(size, "SemiBold")
    w = draw.textlength(text, font=f) + 2 * 20
    draw.rounded_rectangle((x, y, x + w, y + size + 22), (size + 22) // 2, fill=NAVY)
    draw.text((x + 20, y + (size + 22) // 2), text, font=f, fill=WHITE, anchor="lm")


def qr_codes(module=6):
    """[(image, title, subtitle, colour)] — GoFundMe first if there is one, then the website."""
    codes = [(qr(GOFUNDME, module), "GoFundMe", L["gfm_sub"], GREEN)] if GOFUNDME else []
    return codes + [(qr(args.site, module), L["site"], L["site_sub"], NAVY)]


def qr_row(img, x0, y0, x1, codes):
    """QR codes side by side inside a white card sized to fit, captions underneath. Returns the card height."""
    side = max(q.size[0] for q, *_ in codes)
    y1 = y0 + 26 + side + 52 + 21 + 30
    card(img, (x0, y0, x1, y1))
    draw = ImageDraw.Draw(img)
    col = (x1 - x0) // len(codes)
    for i, (q, title, sub, color) in enumerate(codes):
        cx = x0 + col * i + col // 2
        img.paste(q, (cx - q.size[0] // 2, y0 + 26 + (side - q.size[1]) // 2))
        draw.text((cx, y0 + 26 + side + 16), title, font=fit(draw, title, "Bold", 30, col - 20), fill=color, anchor="mt")
        draw.text((cx, y0 + 26 + side + 52), sub, font=fit(draw, sub, "SemiLight", 21, col - 20), fill=MUTED, anchor="mt")
    if len(codes) == 2:
        draw.line(((x0 + x1) // 2, y0 + 26, (x0 + x1) // 2, y1 - 26), fill=(226, 230, 238), width=2)
    return y1 - y0


def photo_left(img, width):
    """Photo on the left, fading into the background on its right edge."""
    img.paste(cover(args.photo, width, S - TOP, args.focus), (0, TOP))
    fade = Image.linear_gradient("L").rotate(90, expand=True).resize((160, S - TOP))   # 0 on the left -> 255 on the right
    img.paste(Image.new("RGB", (160, S - TOP), BG), (width - 160, TOP), fade)
    draw = ImageDraw.Draw(img)
    if not HY:   # the Armenian banner already gives name and age
        chip(draw, 36, S - 92, L["chip"].format(age=age()))
    return draw


def banner(img):
    """Armenian posts: navy band across the top: "Help me" on the left, name, age and diagnosis on the right."""
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, S, TOP), fill=NAVY)
    help_me, name, diagnosis = L["banner"]
    f = font(66, "Bold")
    draw.text((44, TOP // 2), help_me, font=f, fill=AMBER, anchor="lm")
    dx = 44 + draw.textlength(help_me, font=f) + 34
    draw.line((dx, 34, dx, TOP - 34), fill=(70, 96, 140), width=3)
    tx = dx + 34
    name = name.format(age=age())
    draw.text((tx, TOP // 2 - 4), name, font=fit(draw, name, "Bold", 42, S - 44 - tx), fill=WHITE, anchor="ls")
    draw.text((tx, TOP // 2 + 12), diagnosis, font=fit(draw, diagnosis, "SemiBold", 34, S - 44 - tx), fill=(196, 210, 235), anchor="lt")


# ---------- styles ----------
def style_qr_right():
    img = Image.new("RGB", (S, S), BG)
    PW = 560
    draw = photo_left(img, PW)
    x, w = PW + 10, S - PW - 10 - 44
    codes = qr_codes(module=7)
    f_t, lh = (font(40, "Bold"), 50) if HY else (font(54, "Bold"), 62)
    title = wrap(draw, L["title"], f_t, w)
    kicker = 0 if HY else 50
    col_h = kicker + lh * len(title) + 16 + 46 + 92 + sum(q.size[1] + 40 + 22 for q, *_ in codes) - 22
    y = TOP + (S - TOP - col_h) // 2
    if not HY:
        draw.text((x, y), L["kicker"], font=font(26, "Bold"), fill=AMBER)
    y += kicker
    for line in title:
        draw.text((x, y), line, font=f_t, fill=INK)
        y += lh
    y += 16
    draw.text((x, y), L["price"], font=font(34, "SemiBold"), fill=MUTED)
    y += 46
    price = money(campaign["goal"]["amount"])
    draw.text((x, y), price, font=fit(draw, price, "Bold", 60, w), fill=INK)
    y += 92

    # QR codes stacked, each in its own card with the caption beside it
    for q, title, sub, color in codes:
        h = q.size[1] + 40
        card(img, (x, y, x + w, y + h), border=color, width=3)
        draw = ImageDraw.Draw(img)
        img.paste(q, (x + 20, y + 20))
        tx = x + 20 + q.size[0] + 22
        draw.text((tx, y + h // 2 - 22), title, font=fit(draw, title, "Bold", 34, x + w - 16 - tx), fill=color, anchor="lm")
        for k, line in enumerate(wrap(draw, sub, font(22, "SemiLight"), x + w - 16 - tx)):
            draw.text((tx, y + h // 2 + 14 + k * 26), line, font=font(22, "SemiLight"), fill=MUTED, anchor="lm")
        y += h + 22
    return img


def style_progress():
    img = Image.new("RGB", (S, S), BG)
    PH = TOP + 330 if HY else 400
    img.paste(cover(args.photo, S, PH - TOP, args.focus, top=0.3 if HY else 0.15), (0, TOP))
    fade = Image.linear_gradient("L").resize((S, 180))
    img.paste(Image.new("RGB", (S, 180), BG), (0, PH - 180), fade)
    draw = ImageDraw.Draw(img)
    if not HY:
        chip(draw, 40, PH - 150, L["chip"].format(age=age()))

    goal, raised = campaign["goal"], campaign["raised"]
    amount = raised["amount"] if isinstance(raised["amount"], (int, float)) else 0
    pct = amount / goal["amount"] * 100

    box = (40, PH - 80, S - 40, PH + 220)
    card(img, box, border=NAVY)
    draw = ImageDraw.Draw(img)
    x = 80
    draw.text((x, PH - 50), L["raised"], font=font(30, "SemiBold"), fill=MUTED)
    draw.text((x, PH - 6), money(amount), font=font(76, "Bold"), fill=INK)
    goal_txt = L["of_goal"].format(goal=money(goal["amount"]))
    draw.text((S - 80, PH + 46), goal_txt, font=fit(draw, goal_txt, "SemiBold", 32, 470), fill=MUTED, anchor="rs")
    # progress bar
    by, bw = PH + 104, S - 160
    draw.rounded_rectangle((x, by, x + bw, by + 26), 13, fill=(232, 235, 242))
    draw.rounded_rectangle((x, by, x + max(26, round(bw * pct / 100)), by + 26), 13, fill=AMBER)
    pct_txt = f"{pct:.1f}".replace(".", ",") + " %"
    d = date.fromisoformat(raised["updated"]) if raised.get("updated", "")[:2] == "20" else None
    updated = L["updated"].format(date=when(d)) if d else ""
    draw.text((x, by + 50), pct_txt, font=font(34, "Bold"), fill=INK)
    draw.text((S - 80, by + 56), updated, font=font(26, "SemiLight"), fill=MUTED, anchor="ra")

    if HY:   # no room for the motto under the banner
        qr_row(img, 40, PH + 252, S - 40, qr_codes(module=5))
    else:
        draw.text((S // 2, PH + 252), L["motto"], font=font(32, "SemiBold"), fill=INK, anchor="mt")
        qr_row(img, 40, PH + 304, S - 40, qr_codes(module=5))
    return img


def style_alfa():
    img = Image.new("RGB", (S, S), BG)
    PW = 470
    draw = photo_left(img, PW)
    x, w = PW + 10, S - PW - 10 - 40
    p = payments["rub"]

    y = TOP + (26 if HY else 44)
    f_t = font(36 if HY else 42, "Bold")
    for line in wrap(draw, L["title"], f_t, w):
        draw.text((x, y), line, font=f_t, fill=INK)
        y += 46 if HY else 50
    price = f"{L['price']} {money(campaign['goal']['amount'])}" if HY else f"Его цена — {rub(campaign['goal']['amount'])}"
    draw.text((x, y + 6), price, font=fit(draw, price, "SemiBold", 32, w), fill=MUTED)
    y += 62 if HY else 70

    # Alfa-Bank card
    h = 400
    card(img, (x, y, x + w, y + h), border=RED)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((x + 24, y + 24, x + 24 + 220, y + 72), 14, fill=RED)
    draw.text((x + 24 + 110, y + 48), L["alfa"], font=fit(draw, L["alfa"], "Bold", 30, 196), fill=WHITE, anchor="mm")
    draw.text((x + w - 24, y + 48), L["in_rub"], font=font(26, "SemiBold"), fill=MUTED, anchor="rm")
    label = L["card"] if p.get("type") == "card" else L["account"]
    num = " ".join(p["number"][i:i + 4] for i in range(0, len(p["number"]), 4)) if p.get("type") == "card" else p["number"]
    draw.text((x + 24, y + 100), label, font=font(26, "SemiBold"), fill=MUTED)
    draw.text((x + 24, y + 132), num, font=fit(draw, num, "Bold", 58, w - 48), fill=INK)
    ben = f"{L['beneficiary']}{p.get('beneficiary', '')}"
    draw.text((x + 24, y + 206), ben, font=fit(draw, ben, "SemiBold", 28, w - 48), fill=INK)
    draw.line((x + 20, y + 252, x + w - 20, y + 252), fill=(232, 222, 222), width=2)
    if p.get("phone"):
        draw.text((x + 24, y + 266), L["phone_lead"], font=fit(draw, L["phone_lead"], "SemiLight", 22, w - 48), fill=MUTED)
        draw.text((x + 24, y + 292), p["phone"], font=fit(draw, p["phone"], "Bold", 40, w - 48), fill=RED)
    draw.text((x + 24, y + 352), PURPOSE, font=fit(draw, PURPOSE, "SemiBold", 26, w - 48), fill=INK)
    y += h + (20 if HY else 24)

    qr_row(img, x, y, x + w, qr_codes(module=5 if HY else 6))
    return img


def style_details():
    """Everything in one square: all cards with account numbers and holders, SWIFT, Idram, GoFundMe, QR codes."""
    img = Image.new("RGB", (S, S), BG)
    draw = ImageDraw.Draw(img)
    M = 36

    # Header: round photo + headline
    D = 200
    face = cover(args.photo, D, D, args.focus, top=0.1)
    mask = Image.new("L", (D, D), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, D - 1, D - 1), fill=255)
    draw.ellipse((M - 6, 22 - 6, M + D + 6, 22 + D + 6), fill=NAVY)
    img.paste(face, (M, 22), mask)
    hx, hw = M + D + 34, S - (M + D + 34) - M
    if HY:   # the banner text lives in the header here, next to the photo
        help_me, name, diagnosis = L["banner"]
        name = name.format(age=age())
        draw.text((hx, 26), help_me, font=font(40, "Bold"), fill=AMBER)
        draw.text((hx, 80), name, font=fit(draw, name, "Bold", 46, hw), fill=INK)
        draw.text((hx, 140), diagnosis, font=fit(draw, diagnosis, "SemiBold", 34, hw), fill=NAVY)
        price = f"Elevidys · {L['price']} {money(campaign['goal']['amount'])}"
        draw.text((hx, 190), price, font=fit(draw, price, "SemiBold", 28, hw), fill=MUTED)
    else:
        draw.text((hx, 34), L["kicker_age"].format(age=age()), font=font(24, "Bold"), fill=AMBER)
        y = 70
        for line in wrap(draw, L["title"], font(46, "Bold"), hw):
            draw.text((hx, y), line, font=font(46, "Bold"), fill=INK)
            y += 52
        price = f"Его цена — {rub(campaign['goal']['amount'])}"
        draw.text((hx, y + 6), price, font=fit(draw, price, "SemiBold", 34, hw), fill=MUTED)

    # All cards / accounts
    rows = L["rows"]
    ROW = 104
    swift = payments.get("swift", {})
    top = 252
    h = 18 + ROW * len(rows) + (46 if swift.get("swift") else 0) + 40 + 10
    card(img, (M, top, S - M, top + h))
    draw = ImageDraw.Draw(img)
    y = top + 18
    for i, pid in enumerate(rows):
        p = payments[pid]
        if i:
            draw.line((M + 22, y, S - M - 22, y), fill=(226, 230, 238), width=2)
        is_card = p.get("type") == "card"
        num = " ".join(p["number"][k:k + 4] for k in range(0, len(p["number"]), 4)) if is_card else p["number"]
        label = f"{L['card']} " if is_card else f"{L['account']} "
        x = M + 26
        draw.text((x, y + 36), label, font=font(24, "SemiBold"), fill=MUTED, anchor="lm")
        x += draw.textlength(label, font=font(24, "SemiBold"))
        draw.text((x, y + 34), num, font=fit(draw, num, "Bold", 44, S - M - 210 - x), fill=INK, anchor="lm")
        sub = []
        if p.get("accountNumber"):
            sub.append(f"{L['account_sub']}{p['accountNumber']}")
        if p.get("beneficiary"):
            sub.append(f"{L['beneficiary']}{p['beneficiary']}")
        if p.get("phone"):
            sub.append(f"{L['tel']}{p['phone']}")
        line = "  ·  ".join(sub)
        draw.text((M + 26, y + 76), line, font=fit(draw, line, "SemiBold", 22, S - 2 * M - 52), fill=MUTED, anchor="lm")
        bank = {"Alfa-Bank": L["alfa"]}.get(p.get("bank", ""), p.get("bank", ""))
        draw.text((S - M - 26, y + 26), p["currency"], font=font(40, "Bold"), fill=RED if pid == "rub" else INK, anchor="rm")
        draw.text((S - M - 26, y + 56), bank, font=font(20, "SemiBold"), fill=MUTED, anchor="rm")
        y += ROW
    if swift.get("swift"):
        draw.line((M + 22, y, S - M - 22, y), fill=(226, 230, 238), width=2)
        sw = L["swift"].format(bank=swift.get("bank", ""), swift=swift["swift"], ben=swift.get("beneficiary", ""))
        draw.text((S // 2, y + 26), sw, font=fit(draw, sw, "SemiBold", 22, S - 2 * M - 40), fill=NAVY, anchor="mm")

    # Payment purpose, last line of the cards block
    py = top + h - 10 - 40
    draw.text((S // 2, py + 18), PURPOSE, font=fit(draw, PURPOSE, "Bold", 26, S - 2 * M - 40), fill=INK, anchor="mm")

    # Idram + GoFundMe
    y = top + h + 16
    half = (S - 2 * M - 16) // 2
    draw.rounded_rectangle((M, y, M + half, y + 74), 22, fill=NAVY)
    idram = f"Idram  {payments['idram']['number']}"
    draw.text((M + half // 2, y + 37), idram, font=fit(draw, idram, "Bold", 40, half - 40), fill=WHITE, anchor="mm")
    if GOFUNDME:
        gx = M + half + 16
        card(img, (gx, y, S - M, y + 74), radius=22, border=GREEN)
        draw = ImageDraw.Draw(img)
        draw.text((gx + 22, y + 37), "GoFundMe", font=font(36, "Bold"), fill=GREEN, anchor="lm")
        draw.text((S - M - 22, y + 37), L["gfm_short"], font=font(24, "SemiLight"), fill=MUTED, anchor="rm")

    # QR codes: code on the left of each half, caption beside it
    y += 74 + 16
    codes = qr_codes(module=4)
    card(img, (M, y, S - M, S - 24))
    draw = ImageDraw.Draw(img)
    col = (S - 2 * M) // len(codes)
    for i, (q, title, sub, color) in enumerate(codes):
        x0 = M + col * i + 20
        qy = y + (S - 24 - y - q.size[1]) // 2
        img.paste(q, (x0, qy))
        tx = x0 + q.size[0] + 18
        draw.text((tx, qy + q.size[1] // 2 - 16), title, font=fit(draw, title, "Bold", 30, M + col * (i + 1) - 12 - tx), fill=color, anchor="lm")
        draw.text((tx, qy + q.size[1] // 2 + 18), sub, font=fit(draw, sub, "SemiLight", 21, M + col * (i + 1) - 12 - tx), fill=MUTED, anchor="lm")
    if len(codes) == 2:
        draw.line((S // 2, y + 18, S // 2, S - 42), fill=(226, 230, 238), width=2)
    return img


BUILD = {"qr-right": style_qr_right, "progress": style_progress, "alfa": style_alfa, "details": style_details}
for name in (STYLES if args.style == "all" else [args.style]):
    out = ROOT / f"src/assets/img/square-{name}{'-hy' if HY else ''}.jpg"
    img = BUILD[name]()
    if HY and name != "details":   # "details" puts this text in its own header
        banner(img)
    img.save(out, quality=92, optimize=True)
    print(f"Saved {out}")
