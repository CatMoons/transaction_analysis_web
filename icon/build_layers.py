"""Разрезает source.jpg на слои для анимации нажатия.

Слои (все 1024x1024, RGBA, лежат в assets/):
    frame.webp      - рамка; на месте диска тёмное углубление
    ring.webp       - внешнее кольцо с рунами (вращается); под свитком/значком дорисовано
    ring-rest.webp  - оригинальные пиксели кольца возле свитка (видны только в покое)
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
# свиток: корпус и две свисающие ленты (координаты исходника 1024px)
SCROLL = [
    [(157, 235), (180, 202), (255, 195), (262, 200), (295, 225), (315, 330), (330, 430),
     (342, 462), (368, 500), (372, 540), (380, 565), (400, 645), (425, 720), (445, 785),
     (462, 822), (466, 846), (432, 872), (360, 872), (333, 852), (323, 812), (313, 780),
     (300, 720), (292, 620), (298, 552), (255, 560), (217, 482), (195, 420), (175, 345),
     (160, 280)],
    [(285, 535), (240, 548), (195, 573), (150, 617), (143, 640), (155, 648), (200, 617),
     (255, 582), (290, 568)],
    [(290, 550), (255, 563), (220, 660), (208, 745), (214, 830), (226, 832), (230, 735),
     (247, 670), (272, 588), (300, 565)],
]
GLOW = np.array([125, 205, 245])  # голубой ореол вокруг свитка
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
    """Повторяем узкую полоску камня справа от дыры.

    Центральный диск только проседает на несколько процентов, поэтому из-под свитка
    выглядывает лишь край дыры; полоска узкая, чтобы не дотянуться до эмблемы.
    """
    out = rgb.copy()
    strip = 10
    for y in np.where(hole.any(1))[0]:
        xs = np.where(hole[y])[0]
        for run in np.split(xs, np.where(np.diff(xs) > 1)[0] + 1):
            out[y, run] = rgb[y, np.clip(run[-1] + 1 + (run[-1] - run) % strip, 0, 1023)]
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
    scroll_m = supersampled_mask(lambda d, s: [d.polygon([(x * s, y * s) for x, y in poly], fill=255) for poly in SCROLL])
    badge_m = supersampled_mask(circle(*BADGE))
    overlay_m = Image.fromarray(np.maximum(np.asarray(scroll_m), np.asarray(badge_m)))
    overlay_a = np.asarray(overlay_m.filter(ImageFilter.GaussianBlur(0.8))).astype(float)
    # исходный ореол свитка нарисован на диске: убираем его из подвижных слоёв
    # и рисуем такой же ореол в неподвижном слое
    halo = np.asarray(scroll_m.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(9))).astype(float)
    halo_a = np.clip(halo * 0.6 - overlay_a, 0, 255)
    hidden = (np.asarray(scroll_m.filter(ImageFilter.MaxFilter(41))) > 0) | \
             (np.asarray(badge_m.filter(ImageFilter.MaxFilter(9))) > 0)
    # центральный диск не вращается: его собственный ореол остаётся на месте
    hidden_core = np.asarray(overlay_m.filter(ImageFilter.MaxFilter(9))) > 0

    # --- кольцо рун: дыры под свитком и значком
    ring = inpaint_ring(rgb, hidden & (rr > R_CORE - 6) & (rr < R_DISC + 3))
    save(ring, ring_a, "ring.webp")
    zone = np.asarray(Image.fromarray(hidden.astype(np.uint8) * 255).filter(ImageFilter.GaussianBlur(4))) / 255
    save(rgb, ring_a * zone, "ring-rest.webp")
    rg = rune_alpha(ring)
    save(ring * rg[..., None], ring_a * rg, "ring-glow.webp")

    # --- центральный диск
    core = inpaint_rows(rgb, hidden_core & (rr < R_CORE + 6))
    save(core, core_a, "core.webp")
    eg = emblem_alpha(core)
    save(core * eg[..., None], 255 * eg, "core-glow.webp")

    # --- неподвижные свиток и значок
    k = (overlay_a / np.maximum(overlay_a + halo_a, 1))[..., None]
    save(rgb * k + GLOW * (1 - k), overlay_a + halo_a, "overlay.webp")

    # --- рамка: углубление вместо диска
    pit = np.clip((rr - R_DISC + 40) / 40, 0, 1)[..., None]
    pit_col = np.array([8, 9, 11]) + pit * np.array([22, 22, 24])
    frame = np.where((disc_a > 0)[..., None], pit_col, rgb)
    Image.fromarray(frame.astype(np.uint8)).save(OUT / "frame.webp", quality=92)


if __name__ == "__main__":
    main()
