"""Builds the Russian fundraising poster (src/assets/img/poster.jpg + poster-thumb.jpg).

Card numbers, Idram, bank names, the goal and the recipient come from the same files as the
website (src/_data/campaign.json, src/_data/i18n/ru.json), so the poster always matches the site.

    python tools/make-poster.py
    python tools/make-poster.py --photo src/assets/img/life/1.jpeg --url https://aghas-mh.github.io/Narek/ru/

Needs Pillow and qrcode (pip install pillow qrcode) and the Bahnschrift font that ships with Windows 10/11.
"""
import argparse
import json
from datetime import date
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = r"C:\Windows\Fonts\bahnschrift.ttf"

parser = argparse.ArgumentParser()
parser.add_argument("--photo", default="src/assets/img/life/1.jpeg")
parser.add_argument("--url", default="https://aghas-mh.github.io/Narek/ru/", help="where the QR code points")
parser.add_argument("--out", default="src/assets/img/poster.jpg")
parser.add_argument("--photo-top", type=float, default=0.0,
                    help="for tall photos: which part to keep, 0 = top, 0.5 = middle, 1 = bottom")
args = parser.parse_args()

campaign = json.loads((ROOT / "src/_data/campaign.json").read_text(encoding="utf-8"))
ru = json.loads((ROOT / "src/_data/i18n/ru.json").read_text(encoding="utf-8"))
payments = {p["id"]: p for p in campaign["payments"]}

# Same order as the original poster
CARDS = ["usd", "amd", "eur", "rub"]
BANK_NAMES_RU = {"Alfa-Bank": "Альфа-Банк"}
# SHOWN_URL = args.url.split("://", 1)[-1].rstrip("/").removesuffix("/ru")

W, M = 1200, 40                      # canvas width, side margin
BG = (244, 245, 249)
INK = (3, 22, 62)
NAVY = (16, 43, 86)
MUTED = (78, 90, 118)
LINE = (222, 226, 236)
WHITE = (255, 255, 255)


def font(size, style="Bold"):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_name(style)
    return f


def fit(text, style, size, width, draw):
    """Largest font size (down from `size`) at which `text` fits in `width`."""
    while size > 20 and draw.textlength(text, font=font(size, style)) > width:
        size -= 2
    return font(size, style)


def group(number):
    return " ".join(number[i:i + 4] for i in range(0, len(number), 4))


def age(born):
    b, t = date.fromisoformat(born), date.today()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


def money_ru(n):
    return f"{n:,}".replace(",", " ")


def card(img, box, radius=30, border=None):
    """White rounded card with a soft shadow (and an optional navy border, like the original price box)."""
    x0, y0, x1, y1 = box
    shadow = Image.new("L", img.size, 0)
    ImageDraw.Draw(shadow).rounded_rectangle((x0, y0 + 8, x1, y1 + 8), radius, fill=70)
    img.paste(Image.new("RGB", img.size, (150, 160, 190)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius, fill=WHITE, outline=border, width=4 if border else 0)


# ---------- measure everything first, then draw on a canvas of the right height ----------
scratch = ImageDraw.Draw(Image.new("RGB", (W, 100)))
inner = W - 2 * M - 2 * 48

photo = Image.open(ROOT / args.photo).convert("RGB")
PHOTO_H = round(photo.height * W / photo.width)
photo = photo.resize((W, PHOTO_H), Image.LANCZOS)
# Portrait photos would take half the poster: keep the head and shoulders only
MAX_PHOTO_H = 1000
if PHOTO_H > MAX_PHOTO_H:
    top = round((PHOTO_H - MAX_PHOTO_H) * args.photo_top)
    photo = photo.crop((0, top, W, top + MAX_PHOTO_H))
    PHOTO_H = MAX_PHOTO_H

goal = campaign["goal"]
head1 = "Мой шанс — препарат Elevidys."
head2a, head2b = "Его цена — ", f"{money_ru(goal['amount'])} рублей."
head3a = "Номера карт и счетов"
f_head1 = fit(head1, "Bold", 70, inner, scratch)
f_head2b = font(f_head1.size, "Bold")
f_head2a = font(round(f_head1.size * 0.8), "SemiBold")

ROW_H, ROWS_PAD, SUB_H = 108, 18, 40
labels = ru["donate"]


def sub_lines(p):
    """Smaller lines under the number: bank account and account holder, as on the website."""
    lines = []
    if p.get("accountNumber"):
        lines.append(f"{labels['account']} {p['accountNumber']}")
    if p.get("beneficiary") and not str(p["beneficiary"]).upper().startswith("TODO"):
        lines.append(f"{labels['beneficiary']} {p['beneficiary']}")
    return lines


row_heights = [ROW_H + SUB_H * len(sub_lines(payments[pid])) for pid in CARDS]
QR_MODULE, QR_PAD = 10, 46
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=QR_MODULE, border=0)
qr.add_data(args.url)
qr.make(fit=True)
qr_img = qr.make_image(fill_color=INK, back_color=WHITE).convert("RGB")
QR = qr_img.size[0]

y_head = PHOTO_H - 110                                   # headline card overlaps the photo
h_head = 48 + f_head1.size + 22 + f_head1.size + 44
y_cards = y_head + h_head + 86
h_cards = ROWS_PAD * 2 + sum(row_heights)
y_idram = y_cards + h_cards + 24
h_idram = 120
GOFUNDME = campaign.get("gofundme", "")
y_gfm = y_idram + h_idram + 20
h_gfm = 112 if GOFUNDME else 0
y_name = y_gfm + h_gfm + (34 if GOFUNDME else 14)
h_name = 66 + 12 + 34
y_qr = y_name + h_name + 34
h_qr = QR + 2 * QR_PAD
H = y_qr + h_qr + 48

# ---------- draw ----------
img = Image.new("RGB", (W, H), BG)
img.paste(photo, (0, 0))

# Fade the bottom of the photo into the background
fade_h = 220
fade = Image.linear_gradient("L").resize((W, fade_h))
img.paste(Image.new("RGB", (W, fade_h), BG), (0, PHOTO_H - fade_h), fade)
draw = ImageDraw.Draw(img)

# "Narek, 9" chip on the photo
chip = f"Нарек, {age(campaign['child']['birthDate'])} лет"
f_chip = font(34, "SemiBold")
cw = draw.textlength(chip, font=f_chip) + 48
draw.rounded_rectangle((M, y_head - 84, M + cw, y_head - 28), 28, fill=NAVY)
draw.text((M + 24, y_head - 56), chip, font=f_chip, fill=WHITE, anchor="lm")

# Headline card
card(img, (M, y_head, W - M, y_head + h_head), border=NAVY)
draw = ImageDraw.Draw(img)
x = M + 48
draw.text((x, y_head + 48), head1, font=f_head1, fill=INK, anchor="lt")
y2 = y_head + 48 + f_head1.size + 22
draw.text((x, y2 + f_head1.size), head2a, font=f_head2a, fill=MUTED, anchor="ls")
draw.text((x + draw.textlength(head2a, font=f_head2a), y2 + f_head1.size), head2b, font=f_head2b, fill=INK, anchor="ls")

f_head3a = font(64, "Bold")
draw.text((x, y_cards - 20), head3a, font=f_head3a, fill=INK, anchor="ls")

# Card numbers
card(img, (M, y_cards, W - M, y_cards + h_cards))
draw = ImageDraw.Draw(img)
f_num, f_cur, f_bank = font(64, "Bold"), font(56, "Bold"), font(26, "SemiBold")
f_sub = font(32, "SemiBold")
top = y_cards + ROWS_PAD
for i, pid in enumerate(CARDS):
    p = payments[pid]
    mid = top + ROW_H // 2
    if i:
        draw.line((M + 30, top, W - M - 30, top), fill=LINE, width=2)
    number = group(p["number"]) if p.get("type") == "card" else p["number"]
    nx = M + 48
    acc_label = ""
    if p.get("type") == "account":
        # A bank account number, not a card number: say so in front of it
        acc_label = labels["account"] + " "
    else:
        acc_label = "Карта: "

    f_acc = font(40, "SemiBold")
    draw.text((nx, mid + 4), acc_label, font=f_acc, fill=MUTED, anchor="lm")
    nx += draw.textlength(acc_label, font=f_acc)

    draw.text((nx, mid), number, font=fit(number, "Bold", 64, W - M - 230 - nx, draw), fill=INK, anchor="lm")
    for j, line in enumerate(sub_lines(p)):
        draw.text((M + 50, top + ROW_H - 14 + j * SUB_H), line, font=f_sub, fill=MUTED, anchor="lt")
    top += row_heights[i]
    bank = BANK_NAMES_RU.get(p.get("bank", ""), p.get("bank", ""))
    draw.text((W - M - 48, mid - 14), p["currency"], font=f_cur, fill=INK, anchor="rm")
    if bank:
        draw.text((W - M - 48, mid + 30), bank, font=f_bank, fill=MUTED, anchor="rm")

# Idram bar
draw.rounded_rectangle((M, y_idram, W - M, y_idram + h_idram), 28, fill=NAVY)
f_idram = font(70, "Bold")
idram = f"Idram   {payments['idram']['number']}"
draw.text((W // 2, y_idram + h_idram // 2), idram, font=f_idram, fill=WHITE, anchor="mm")

# GoFundMe: online card payment from any country
if GOFUNDME:
    GREEN = (2, 169, 92)
    card(img, (M, y_gfm, W - M, y_gfm + h_gfm), radius=28, border=GREEN)
    draw = ImageDraw.Draw(img)
    gx, gmid = M + 40, y_gfm + h_gfm // 2
    f_g = font(52, "Bold")
    draw.text((gx, gmid), "GoFundMe", font=f_g, fill=GREEN, anchor="lm")
    gx += draw.textlength("GoFundMe", font=f_g) + 30
    shown = GOFUNDME.split("://", 1)[-1].removeprefix("www.")
    draw.text((gx, gmid - 18), "онлайн-оплата картой из любой страны", font=font(28, "SemiLight"), fill=MUTED, anchor="lm")
    draw.text((gx, gmid + 20), shown, font=fit(shown, "SemiBold SemiCondensed", 38, W - M - 36 - gx, draw), fill=INK, anchor="lm")

# Recipient
donate = ru["donate"]
draw.text((W // 2, y_name), donate["recipientName"], font=font(66, "Bold"), fill=INK, anchor="mt")
draw.text((W // 2, y_name + 66 + 12), f"получатель, {donate['recipientRelation']}", font=font(32, "SemiLight"), fill=MUTED, anchor="mt")

# QR panel
card(img, (M, y_qr, W - M, y_qr + h_qr))
draw = ImageDraw.Draw(img)
qx, qy = M + QR_PAD, y_qr + QR_PAD
img.paste(qr_img, (qx, qy))
tx = qx + QR + 52
tw = W - M - QR_PAD - tx
f_t, f_b, f_u = font(62, "Bold SemiCondensed"), font(36, "SemiCondensed"), font(40, "Bold SemiCondensed")
body = ["История Нарека, медицинские", "документы и\u00a0все способы помощи"]
block = 62 + 18 + 46 * len(body) + 26 + 72
y = y_qr + (h_qr - block) // 2
draw.text((tx, y), "Отсканируйте QR-код", font=f_t, fill=INK)
y += 62 + 18
for line in body:
    draw.text((tx, y), line, font=f_b, fill=MUTED)
    y += 46
y += 26
# uw = draw.textlength(SHOWN_URL, font=f_u)
# draw.rounded_rectangle((tx, y, tx + uw + 56, y + 72), 36, fill=NAVY)
# draw.text((tx + 28, y + 36), SHOWN_URL, font=f_u, fill=WHITE, anchor="lm")

out = ROOT / args.out
img.save(out, quality=92, optimize=True)
thumb_h = round(480 * H / W)
img.resize((480, thumb_h), Image.LANCZOS).save(out.with_name(out.stem + "-thumb.jpg"), quality=85, optimize=True)
print(f"Saved {out} ({W}x{H}) and thumbnail 480x{thumb_h}; QR -> {args.url}")
