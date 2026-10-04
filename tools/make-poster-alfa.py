"""Poster for donors in Russia: only the Alfa-Bank rouble card, the phone number for transfers /
contact with the account holder, GoFundMe, and two QR codes (GoFundMe and the website).

    python tools/make-poster-alfa.py
    python tools/make-poster-alfa.py --photo src/assets/img/narek-900.jpg --out src/assets/img/poster-alfa.jpg

Data comes from src/_data/campaign.json (payment "rub": number, bank, beneficiary, phone; "gofundme").
Needs Pillow and qrcode, and the Bahnschrift font that ships with Windows 10/11.
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
parser.add_argument("--site", default="https://aghas-mh.github.io/Narek/ru/")
parser.add_argument("--out", default="src/assets/img/poster-alfa.jpg")
parser.add_argument("--photo-top", type=float, default=0.0, help="for tall photos: 0 = keep top, 1 = keep bottom")
args = parser.parse_args()

campaign = json.loads((ROOT / "src/_data/campaign.json").read_text(encoding="utf-8"))
rub = next(p for p in campaign["payments"] if p["id"] == "rub")
GOFUNDME = campaign["gofundme"]

W, M = 1200, 40
BG, INK, NAVY, MUTED = (244, 245, 249), (3, 22, 62), (16, 43, 86), (78, 90, 118)
WHITE, GREEN, RED = (255, 255, 255), (2, 169, 92), (239, 49, 36)   # RED: Alfa-Bank brand


def font(size, style="Bold"):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_name(style)
    return f


def fit(text, style, size, width, draw):
    while size > 20 and draw.textlength(text, font=font(size, style)) > width:
        size -= 2
    return font(size, style)


def card(img, box, radius=30, border=None, width=4):
    x0, y0, x1, y1 = box
    shadow = Image.new("L", img.size, 0)
    ImageDraw.Draw(shadow).rounded_rectangle((x0, y0 + 8, x1, y1 + 8), radius, fill=70)
    img.paste(Image.new("RGB", img.size, (150, 160, 190)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(16)))
    ImageDraw.Draw(img).rounded_rectangle(box, radius, fill=WHITE, outline=border, width=width if border else 0)


def qr_image(url, module):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=module, border=0)
    q.add_data(url)
    q.make(fit=True)
    return q.make_image(fill_color=INK, back_color=WHITE).convert("RGB")


def age(born):
    b, t = date.fromisoformat(born), date.today()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


# ---------- layout ----------
photo = Image.open(ROOT / args.photo).convert("RGB")
PHOTO_H = round(photo.height * W / photo.width)
photo = photo.resize((W, PHOTO_H), Image.LANCZOS)
if PHOTO_H > 1000:
    top = round((PHOTO_H - 1000) * args.photo_top)
    photo, PHOTO_H = photo.crop((0, top, W, top + 1000)), 1000

y_head = PHOTO_H - 110
h_head = 48 + 70 + 22 + 70 + 52   # top pad + two lines + bottom pad
y_bank = y_head + h_head + 30
h_bank = 470
y_gfm = y_bank + h_bank + 28
h_gfm = 150
qr_site, qr_gfm = qr_image(args.site, 8), qr_image(GOFUNDME, 7)
QR_BOX = max(qr_site.size[0], qr_gfm.size[0])
y_qr = y_gfm + h_gfm + 28
h_qr = QR_BOX + 175
H = y_qr + h_qr + 48

img = Image.new("RGB", (W, H), BG)
img.paste(photo, (0, 0))
fade = Image.linear_gradient("L").resize((W, 220))
img.paste(Image.new("RGB", (W, 220), BG), (0, PHOTO_H - 220), fade)
draw = ImageDraw.Draw(img)

chip = f"Нарек, {age(campaign['child']['birthDate'])} лет"
f_chip = font(34, "SemiBold")
draw.rounded_rectangle((M, y_head - 84, M + draw.textlength(chip, font=f_chip) + 48, y_head - 28), 28, fill=NAVY)
draw.text((M + 24, y_head - 56), chip, font=f_chip, fill=WHITE, anchor="lm")

# Headline
card(img, (M, y_head, W - M, y_head + h_head), border=NAVY)
draw = ImageDraw.Draw(img)
x = M + 48
amount = f"{campaign['goal']['amount']:,}".replace(",", " ")
f1 = fit("Мой шанс — препарат Elevidys.", "Bold", 70, W - 2 * x, draw)
draw.text((x, y_head + 48), "Мой шанс — препарат Elevidys.", font=f1, fill=INK, anchor="lt")
f2a, f2b = font(round(f1.size * 0.8), "SemiBold"), font(f1.size, "Bold")
base = y_head + 48 + f1.size + 22 + f1.size
draw.text((x, base), "Его цена — ", font=f2a, fill=MUTED, anchor="ls")
draw.text((x + draw.textlength("Его цена — ", font=f2a), base), f"{amount} рублей.", font=f2b, fill=INK, anchor="ls")

# Alfa-Bank card: number, account holder, phone
card(img, (M, y_bank, W - M, y_bank + h_bank), border=RED)
draw = ImageDraw.Draw(img)
draw.rounded_rectangle((M + 36, y_bank + 36, M + 36 + 300, y_bank + 96), 18, fill=RED)
draw.text((M + 36 + 150, y_bank + 66), "Альфа-Банк", font=font(38, "Bold"), fill=WHITE, anchor="mm")
draw.text((W - M - 48, y_bank + 66), "Перевод в рублях", font=font(36, "SemiBold"), fill=MUTED, anchor="rm")

label = "Карта: " if rub.get("type") == "card" else "Счёт: "
number = " ".join(rub["number"][i:i + 4] for i in range(0, len(rub["number"]), 4)) if rub.get("type") == "card" else rub["number"]
f_lab = font(44, "SemiBold")
draw.text((x, y_bank + 175), label, font=f_lab, fill=MUTED, anchor="lm")
nx = x + draw.textlength(label, font=f_lab)
draw.text((nx, y_bank + 172), number, font=fit(number, "Bold", 84, W - M - 48 - nx, draw), fill=INK, anchor="lm")
draw.text((x, y_bank + 255), f"Получатель: {rub['beneficiary']}", font=font(42, "SemiBold"), fill=INK, anchor="lm")

draw.line((M + 30, y_bank + 315, W - M - 30, y_bank + 315), fill=(232, 222, 222), width=2)
draw.text((x, y_bank + 362), "Перевод по номеру телефона и связь с получателем:", font=font(32, "SemiLight"), fill=MUTED, anchor="lm")
draw.text((x, y_bank + 418), rub["phone"], font=font(66, "Bold"), fill=RED, anchor="lm")

# GoFundMe
card(img, (M, y_gfm, W - M, y_gfm + h_gfm), radius=28, border=GREEN)
draw = ImageDraw.Draw(img)
draw.text((x, y_gfm + h_gfm // 2), "GoFundMe", font=font(60, "Bold"), fill=GREEN, anchor="lm")
gx = x + draw.textlength("GoFundMe", font=font(60, "Bold")) + 34
shown = GOFUNDME.split("://", 1)[-1].removeprefix("www.")
draw.text((gx, y_gfm + h_gfm // 2 - 24), "онлайн-оплата картой из любой страны", font=font(30, "SemiLight"), fill=MUTED, anchor="lm")
draw.text((gx, y_gfm + h_gfm // 2 + 22), shown, font=fit(shown, "SemiBold SemiCondensed", 40, W - M - 36 - gx, draw), fill=INK, anchor="lm")

# Two QR codes: GoFundMe and the website
card(img, (M, y_qr, W - M, y_qr + h_qr))
draw = ImageDraw.Draw(img)
col_w = (W - 2 * M) // 2
for i, (q, title, sub, color) in enumerate([
    (qr_gfm, "GoFundMe", "оплата картой онлайн", GREEN),
    (qr_site, "Сайт Нарека", "история, документы, реквизиты", NAVY),
]):
    cx = M + col_w * i + col_w // 2
    qy = y_qr + 40 + (QR_BOX - q.size[1]) // 2
    img.paste(q, (cx - q.size[0] // 2, qy))
    draw.text((cx, y_qr + 40 + QR_BOX + 30), title, font=font(42, "Bold"), fill=color, anchor="mt")
    draw.text((cx, y_qr + 40 + QR_BOX + 80), sub, font=font(28, "SemiLight"), fill=MUTED, anchor="mt")
draw.line((W // 2, y_qr + 40, W // 2, y_qr + h_qr - 40), fill=(226, 230, 238), width=2)

out = ROOT / args.out
img.save(out, quality=92, optimize=True)
thumb_h = round(480 * H / W)
img.resize((480, thumb_h), Image.LANCZOS).save(out.with_name(out.stem + "-thumb.jpg"), quality=85, optimize=True)
print(f"Saved {out} ({W}x{H}) and thumbnail 480x{thumb_h}")
