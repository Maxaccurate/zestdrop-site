"""Refresh website images from the app itself, without changing the app repo.

Requires Pillow and PowerShell 7 (pwsh). Run with --app <ZestDrop.exe> --video <sample.mp4>
--image <sample.png/jpg> --render-dir <scratch folder>. Wheels and progress cards come from the app's
debug render modes; the combined Crop & rotate window is opened briefly and captured with
scripts/capture-window.ps1 (that window has no render mode of its own).
"""
import argparse
import os
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--app', type=Path, required=True)
parser.add_argument('--video', type=Path, required=True)
parser.add_argument('--image', type=Path, required=True)
parser.add_argument('--render-dir', type=Path, required=True)
args = parser.parse_args()
for path in (args.app, args.video, args.image):
    if not path.is_file():
        parser.error(f'Missing input: {path}')
args.render_dir.mkdir(parents=True, exist_ok=True)
out = Path(__file__).resolve().parents[1] / 'assets' / 'img'
# The format wheel depends on the extension: use a PNG for the 8-option screenshot.
photo = args.render_dir / 'holiday.png'
Image.open(args.image).convert('RGB').save(photo)


def render(lang, arguments):
    env = {**os.environ, 'ZESTDROP_LANG': lang}
    subprocess.run([str(args.app.resolve()), *map(str, arguments)],
                   cwd=args.app.resolve().parent, env=env, check=True, timeout=60)


def backdrop(size):
    # Neutral desktop-like backdrop; the wheel itself is the unmodified app render.
    w, h = size
    image = Image.new('RGBA', size)
    draw = ImageDraw.Draw(image)
    for y in range(h):
        shade = int(235 - 31 * y / max(1, h - 1))
        draw.line((0, y, w, y), fill=(shade, shade + 1, shade, 255))
    light = Image.new('RGBA', size)
    ImageDraw.Draw(light).ellipse((-w // 2, -h // 2, w, h // 2), fill=(255, 255, 255, 100))
    image.alpha_composite(light.filter(ImageFilter.GaussianBlur(w // 8)))
    return image


def compose_wheel(path):
    image = Image.open(path).convert('RGBA').resize((720, 720), Image.Resampling.LANCZOS)
    canvas = backdrop(image.size)
    canvas.alpha_composite(image)
    return canvas.convert('RGB')


def compose_jobs(path):
    image = Image.open(path).convert('RGBA')
    # Debug stack has a solid grey backdrop. Replace it with the same neutral backdrop as the wheels.
    pixels = image.load()
    bg = pixels[0, 0]
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2])) < 4:
                pixels[x, y] = (0, 0, 0, 0)
    image.thumbnail((512, 768), Image.Resampling.LANCZOS)
    canvas = backdrop((536, 792))
    canvas.alpha_composite(image, ((536 - image.width) // 2, (792 - image.height) // 2))
    return canvas.convert('RGB')


def capture_combined(lang, path):
    """Captures the Crop & rotate window and makes the area outside its rounded corners transparent."""
    script = Path(__file__).resolve().parent / 'capture-window.ps1'
    # PowerShell 7 is DPI-aware, so the capture is at the screen's real resolution (Windows PowerShell 5.1 is not).
    subprocess.run(['pwsh', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script),
                    '-App', str(args.app.resolve()), '-Tool', 'merge:cropRotate', '-File', str(photo.resolve()),
                    '-Lang', lang, '-Out', str(path)], check=True, timeout=120)
    image = Image.open(path).convert('RGBA')
    # PrintWindow paints black outside the window's rounded corners; measure the radius from the corner.
    px = image.load()
    radius = next(i for i in range(1, min(image.size) // 4) if sum(px[i, i][:3]) > 60) * 3.4
    mask = Image.new('L', image.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width - 1, image.height - 1), radius=round(radius), fill=255)
    image.putalpha(mask)
    # Keep about 2x the size it is shown at (1040 px wide) so it stays sharp on high-DPI screens.
    if image.width > 2080:
        image = image.resize((2080, round(image.height * 2080 / image.width)), Image.Resampling.LANCZOS)
    if image.width < 1600:
        raise SystemExit(f'Capture is only {image.width} px wide; run on a display scaled to 150% or more')
    return image


for lang in ('en', 'zh'):
    fmt = args.render_dir / f'wheel-formats-{lang}.png'
    tools = args.render_dir / f'wheel-tools-{lang}.png'
    combined = args.render_dir / f'tool-crop-{lang}.png'
    jobs = args.render_dir / f'jobs-{lang}'
    render(lang, ['--debug-wheel-render', 'formats', photo, 'convert:jpg', fmt])
    # A single video's tools are combined in v1.0; light the "Trim & split" entry.
    render(lang, ['--debug-wheel-render', 'tools', args.video.resolve(), 'merge:trimSplit', tools])
    render(lang, ['--debug-indicator', jobs])
    for name, image in (
        (f'wheel-formats-{lang}', compose_wheel(fmt)),
        (f'wheel-tools-{lang}', compose_wheel(tools)),
        (f'tool-crop-{lang}', capture_combined(lang, combined)),
        (f'jobs-{lang}', compose_jobs(Path(str(jobs) + '-expanded.png'))),
    ):
        image.save(out / f'{name}.webp', quality=90, method=6)
        print(f'{name}.webp: {image.size}')

# Share preview: same product copy and composition, but with the current app wheel.
canvas = Image.new('RGBA', (1200, 630), '#FAF8F5')
draw = ImageDraw.Draw(canvas)
fonts = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
bold = ImageFont.truetype(str(fonts / 'segoeuib.ttf'), 76)
regular = ImageFont.truetype(str(fonts / 'segoeui.ttf'), 30)
semibold = ImageFont.truetype(str(fonts / 'seguisb.ttf'), 34)
logo = Image.open(out / 'logo.png').convert('RGBA').resize((72, 72), Image.Resampling.LANCZOS)
canvas.alpha_composite(logo, (72, 70))
draw.text((160, 76), 'ZestDrop', font=semibold, fill='#1F2226')
draw.text((72, 200), 'Drag. Drop.', font=bold, fill='#1F2226')
draw.text((72, 290), 'Convert.', font=bold, fill='#D55418')
draw.text((72, 410), 'Free file converter for Windows.', font=regular, fill='#5F656D')
draw.text((72, 452), 'Hold Shift while dragging any file.', font=regular, fill='#5F656D')
draw.text((72, 540), 'zestdrop.org', font=semibold, fill='#D55418')
shot = Image.open(out / 'wheel-formats-en.webp').convert('RGBA').resize((520, 520), Image.Resampling.LANCZOS)
mask = Image.new('L', shot.size)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, 519, 519), radius=28, fill=255)
shadow = Image.new('RGBA', canvas.size)
ImageDraw.Draw(shadow).rounded_rectangle((630, 69, 1150, 589), radius=28, fill=(40, 30, 20, 55))
canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
canvas.paste(shot, (624, 55), mask)
canvas.convert('RGB').save(out / 'og-image.png', optimize=True)
print('og-image.png: (1200, 630)')
