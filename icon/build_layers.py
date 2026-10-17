"""Разрезает source.jpg на слои для анимации нажатия.

Слои (все 1024x1024, RGBA, лежат в assets/):
    frame.webp      - рамка; на месте диска тёмное углубление
    ring.webp       - внешнее кольцо с рунами (вращается); под свитком/значком дорисовано
    core.webp       - центральный диск с эмблемой (только проседает)
    ring-glow.webp  - свечение рун (для вспышки, mix-blend-mode: screen)
    core-glow.webp  - свечение золотой эмблемы (для вспышки)
    overlay.webp    - свиток слева и значок-шестерёнка справа (неподвижны, поверх диска)

Запуск: python icon/build_layers.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).parent
OUT = HERE / "assets"

CX, CY = 507, 509  # центр диска (найден перебором по симметрии внешнего кольца)
R_DISC = 388  # внешний край серебряного кольца
R_CORE = 305  # тёмная канавка между центральным диском и кольцом рун
BADGE = (802, 801, 93)  # значок-шестерёнка: центр и радиус
SCROLL = [
    (158, 238), (178, 203), (250, 196), (314, 204), (324, 270), (344, 395),
    (366, 465), (377, 530), (380, 565), (390, 612), (422, 710), (444, 780),
    (460, 830), (455, 872), (392, 894), (330, 888), (312, 840), (300, 780),
    (288, 690), (272, 620), (262, 600), (240, 690), (225, 770), (198, 775),
    (200, 720), (220, 640), (232, 600), (205, 605), (165, 655), (148, 670),
    (138, 650), (148, 625), (195, 585), (222, 555), (215, 470), (190, 360),
    (160, 255),
]
EMBLEM_BOX = (395, 335, 715, 685)


def supersampled_mask(draw_fn, scale=4):
    big = Image.new("L", (1024 * scale, 1024 * scale), 0)
    draw_fn(ImageDraw.Draw(big), scale)
    return big.resize((1024, 1024), Image.LANCZOS)


def circle(cx, cy, r):
    return lambda d, s: d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=255)


def emblem_alpha(rgb):
    """Золото/оранжевое свечение: сильный перевес красного над синим."""
    r, g, b = (rgb[..., i].astype(float) for i in range(3))
    warm = np.clip((r - b - 25) / 110.0, 0, 1) * np.clip((r - 70) / 120.0, 0, 1)
    box = np.zeros_like(warm)
    x0, y0, x1, y1 = EMBLEM_BOX
    box[y0:y1, x0:x1] = 1
    return warm * box


def rune_alpha(rgb):
    """Светящиеся голубые руны."""
    r, g, b = (rgb[..., i].astype(float) for i in range(3))
    return np.clip((b - 120) / 90.0, 0, 1) * np.clip((b - r - 5) / 40.0, 0, 1)


def rotate_arr(arr, angle):
    return np.asarray(Image.fromarray(arr).rotate(angle, center=(CX, CY), resample=Image.BICUBIC))


def inpaint_ring(rgb, hole):
    """Кольцо почти концентрично: берём пиксели того же радиуса с другого угла."""
    out = rgb.copy()
    todo = hole.copy()
    valid = (~hole).astype(np.uint8) * 255
    for ang in range(15, 360, 15):
        if not todo.any():
            break
        take = todo & (rotate_arr(valid, ang) > 250)
        out[take] = rotate_arr(rgb, ang)[take]
        todo &= ~take
    return out


def inpaint_rows(rgb, hole):
    """Зеркалим пиксели справа от дыры (под свитком центральный диск почти не виден)."""
    out = rgb.copy()
    for y in np.where(hole.any(1))[0]:
        xs = np.where(hole[y])[0]
        for run in np.split(xs, np.where(np.diff(xs) > 1)[0] + 1):
            out[y, run] = rgb[y, np.clip(2 * run[-1] + 1 - run, 0, 1023)]
    return out


def save(arr, alpha, name):
    Image.fromarray(np.dstack([arr, alpha]).astype(np.uint8), "RGBA").save(OUT / name, quality=92)


def main():
    OUT.mkdir(exist_ok=True)
    rgb = np.asarray(Image.open(HERE / "source.jpg").convert("RGB")).copy()
    yy, xx = np.mgrid[0:1024, 0:1024]
    rr = np.hypot(xx - CX, yy - CY)

    disc_a = np.asarray(supersampled_mask(circle(CX, CY, R_DISC))).astype(float)
    core_a = np.asarray(supersampled_mask(circle(CX, CY, R_CORE))).astype(float)
    ring_a = np.clip(disc_a - core_a, 0, 255)
    scroll_m = supersampled_mask(lambda d, s: d.polygon([(x * s, y * s) for x, y in SCROLL], fill=255))
    badge_m = supersampled_mask(circle(*BADGE))
    overlay_m = Image.fromarray(np.maximum(np.asarray(scroll_m), np.asarray(badge_m)))
    overlay_a = np.asarray(overlay_m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.5)))
    hidden = np.asarray(overlay_m.filter(ImageFilter.MaxFilter(9))) > 0

    # --- кольцо рун: дыры под свитком и значком
    ring = inpaint_ring(rgb, hidden & (rr > R_CORE - 6) & (rr < R_DISC + 3))
    save(ring, ring_a, "ring.webp")
    rg = rune_alpha(ring)
    save(ring * rg[..., None], ring_a * rg, "ring-glow.webp")

    # --- центральный диск
    core = inpaint_rows(rgb, hidden & (rr < R_CORE + 6))
    save(core, core_a, "core.webp")
    eg = emblem_alpha(core)
    save(core * eg[..., None], 255 * eg, "core-glow.webp")

    # --- неподвижные свиток и значок
    save(rgb, overlay_a, "overlay.webp")

    # --- рамка: углубление вместо диска
    pit = np.clip((rr - R_DISC + 40) / 40, 0, 1)[..., None]
    pit_col = np.array([8, 9, 11]) + pit * np.array([22, 22, 24])
    frame = np.where((disc_a > 0)[..., None], pit_col, rgb)
    Image.fromarray(frame.astype(np.uint8)).save(OUT / "frame.webp", quality=92)


if __name__ == "__main__":
    main()
