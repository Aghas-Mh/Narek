<#
.SYNOPSIS
  Creates the 1200x630 social-preview image shown when the page is shared
  (WhatsApp, Telegram, Facebook, Viber, VK...). Texts come from the "og" block
  of src/_data/i18n/<Lang>.json, the goal from src/_data/campaign.json.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\make-og-image.ps1 -Lang en
  powershell -ExecutionPolicy Bypass -File tools\make-og-image.ps1 -Lang ru
  powershell -ExecutionPolicy Bypass -File tools\make-og-image.ps1 -Lang hy
  (The default font, Segoe UI, covers Latin, Cyrillic and Armenian.)
#>
param(
  [string]$Lang = "en",
  [string]$Font = "Segoe UI",
  [string]$Locale = ""
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$root = Split-Path $PSScriptRoot -Parent
$data = Join-Path $root "src\_data"
$readJson = { param($p) Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json }

$en = & $readJson (Join-Path $data "i18n\en.json")
$langFile = Join-Path $data "i18n\$Lang.json"
$t = if (Test-Path $langFile) { & $readJson $langFile } else { $en }
function Pick($key) { if ($t.og -and $t.og.$key) { $t.og.$key } else { $en.og.$key } }

$campaign = & $readJson (Join-Path $data "campaign.json")
if (-not $Locale) { $Locale = @{ en = "en-GB"; hy = "hy-AM"; ru = "ru-RU" }[$Lang] }
if (-not $Locale) { $Locale = "en-GB" }
$culture = [System.Globalization.CultureInfo]::GetCultureInfo($Locale)
$symbols = @{ RUB = [string][char]0x20BD; USD = '$'; EUR = [string][char]0x20AC; AMD = [string][char]0x058F }
$numberFormat = $culture.NumberFormat.Clone()
# Match the website (browser/ICU formatting): Armenian groups digits with spaces, .NET uses commas
if ($Lang -eq "hy") { $numberFormat.NumberGroupSeparator = [string][char]0x00A0 }
$goal = ([double]$campaign.goal.amount).ToString("N0", $numberFormat) + " " + $symbols[$campaign.goal.currency]

$W = 1200; $H = 630
$navy = [System.Drawing.Color]::FromArgb(20, 33, 61)
$amber = [System.Drawing.Color]::FromArgb(245, 181, 61)
$soft = [System.Drawing.Color]::FromArgb(207, 214, 228)
$px = [System.Drawing.GraphicsUnit]::Pixel
$bold = [System.Drawing.FontStyle]::Bold
$regular = [System.Drawing.FontStyle]::Regular

$bmp = New-Object System.Drawing.Bitmap $W, $H
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = "AntiAlias"
$g.InterpolationMode = "HighQualityBicubic"
$g.PixelOffsetMode = "HighQuality"
$g.TextRenderingHint = "AntiAliasGridFit"
$g.Clear($navy)
$tf = [System.Drawing.StringFormat]::GenericTypographic

# Photo on the right, cropped to fill the column
$photo = [System.Drawing.Image]::FromFile((Join-Path $root "src\assets\img\narek-900.jpg"))
$pw = 470
$srcW = $photo.Width; $srcH = [int]($photo.Width * $H / $pw)
if ($srcH -gt $photo.Height) { $srcH = $photo.Height; $srcW = [int]($photo.Height * $pw / $H) }
$srcX = [int](($photo.Width - $srcW) / 2); $srcY = [int](($photo.Height - $srcH) * 0.25)
$g.DrawImage($photo, (New-Object System.Drawing.Rectangle ($W - $pw), 0, $pw, $H), (New-Object System.Drawing.Rectangle $srcX, $srcY, $srcW, $srcH), $px)
$photo.Dispose()

# Fade the photo's left edge into the background
$fadeRect = New-Object System.Drawing.Rectangle ($W - $pw - 2), 0, 160, $H
$fade = New-Object System.Drawing.Drawing2D.LinearGradientBrush $fadeRect, $navy, ([System.Drawing.Color]::FromArgb(0, $navy)), 0.0
$g.FillRectangle($fade, $fadeRect)

# Text column
$x = 64; $textW = $W - $pw - $x - 30; $y = 64
$g.DrawString((Pick "eyebrow"), (New-Object System.Drawing.Font $Font, 21, $bold, $px), (New-Object System.Drawing.SolidBrush $amber), $x, $y, $tf)
$y += 54

$title = Pick "title"
$size = 60
do {
  $fTitle = New-Object System.Drawing.Font $Font, $size, $bold, $px
  $m = $g.MeasureString($title, $fTitle, $textW, $tf)
  $size -= 2
} while ($m.Height -gt 250 -and $size -gt 30)
$g.DrawString($title, $fTitle, [System.Drawing.Brushes]::White, (New-Object System.Drawing.RectangleF $x, $y, $textW, ($m.Height + 8)), $tf)
$y += $m.Height + 26

$sub = Pick "subtitle"
$fSub = New-Object System.Drawing.Font $Font, 25, $regular, $px
$ms = $g.MeasureString($sub, $fSub, $textW, $tf)
$g.DrawString($sub, $fSub, (New-Object System.Drawing.SolidBrush $soft), (New-Object System.Drawing.RectangleF $x, $y, $textW, ($ms.Height + 8)), $tf)

# Goal badge
$badge = (Pick "badge") -replace "\{goal\}", $goal
$fBadge = New-Object System.Drawing.Font $Font, 27, $bold, $px
$mb = $g.MeasureString($badge, $fBadge, 2000, $tf)
$bw = [int]$mb.Width + 48; $bh = 60; $bx = $x; $by = $H - 64 - $bh; $r = $bh
$path = New-Object System.Drawing.Drawing2D.GraphicsPath
$path.AddArc($bx, $by, $r, $r, 90, 180)
$path.AddArc($bx + $bw - $r, $by, $r, $r, 270, 180)
$path.CloseFigure()
$g.FillPath((New-Object System.Drawing.SolidBrush $amber), $path)
$g.DrawString($badge, $fBadge, (New-Object System.Drawing.SolidBrush $navy), ($bx + 24), ($by + ($bh - $mb.Height) / 2), $tf)

# Save
$outDir = Join-Path $root "src\assets\img\og"
New-Item -ItemType Directory -Force $outDir | Out-Null
$out = Join-Path $outDir "og-$Lang.jpg"
$jpeg = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
$params = New-Object System.Drawing.Imaging.EncoderParameters 1
$params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality), ([long]88)
$bmp.Save($out, $jpeg, $params)
$g.Dispose(); $bmp.Dispose()
Write-Output "Saved $out"

