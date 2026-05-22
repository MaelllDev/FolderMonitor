import math
from PIL import Image, ImageDraw


def create_tray_icon(size: int = 64, state: str = "active") -> Image.Image:
    """
    Cria o ícone da bandeja do sistema.

    Args:
        size:  Tamanho em pixels (quadrado).
        state: "active" | "paused" | "stopped"

    Returns:
        Imagem PIL RGBA.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size

    # ── Paleta de cores por estado ──────────────────────────────────────────
    palettes = {
        "active": {
            "bg":     (15,  23,  42, 230),   # slate-900
            "folder": (14, 165, 233),         # sky-500
            "tab":    (56, 189, 248),          # sky-400
            "dot":    (34, 197,  94),          # green-500
            "glass":  (255, 255, 255, 210),
        },
        "paused": {
            "bg":     (15,  23,  42, 230),
            "folder": (100, 116, 139),         # slate-500
            "tab":    (148, 163, 184),          # slate-400
            "dot":    (234, 179,   8),          # yellow-500
            "glass":  (200, 200, 200, 180),
        },
        "stopped": {
            "bg":     (15,  23,  42, 200),
            "folder": (71,  85, 105),           # slate-600
            "tab":    (100, 116, 139),
            "dot":    (239,  68,  68),           # red-500
            "glass":  (160, 160, 160, 160),
        },
    }
    p = palettes.get(state, palettes["active"])

    # ── Fundo (quadrado arredondado) ────────────────────────────────────────
    radius = max(8, s // 8)
    d.rounded_rectangle([1, 1, s - 2, s - 2], radius=radius, fill=p["bg"])

    # ── Pasta (folder) ──────────────────────────────────────────────────────
    fl  = int(s * 0.09)   # left
    fr  = int(s * 0.86)   # right
    ft  = int(s * 0.30)   # top corpo
    fb  = int(s * 0.80)   # bottom
    tw  = int(s * 0.36)   # largura da aba
    th  = int(s * 0.10)   # altura da aba

    # Aba superior
    d.polygon([
        (fl, ft),
        (fl + tw,      ft),
        (fl + tw + 4,  ft - th),
        (fl,           ft - th),
    ], fill=p["tab"])

    # Corpo da pasta
    d.rounded_rectangle([fl, ft, fr, fb], radius=3, fill=p["folder"])

    # Linhas decorativas dentro da pasta (representam arquivos)
    line_color = (*p["bg"][:3], 100)
    line_x1 = fl + int(s * 0.08)
    line_x2 = fr - int(s * 0.08)
    for i, frac in enumerate([0.45, 0.57, 0.67]):
        ly = int(s * frac)
        wd = max(1, s // 40)
        d.rectangle([line_x1, ly - wd, line_x2, ly + wd], fill=line_color)

    # ── Lupa (magnifying glass) ─────────────────────────────────────────────
    gcx = int(s * 0.645)
    gcy = int(s * 0.595)
    gr  = int(s * 0.165)
    lw  = max(2, s // 30)
    gl  = p["glass"]

    # Círculo da lupa
    d.ellipse([gcx - gr, gcy - gr, gcx + gr, gcy + gr],
              outline=gl, width=lw)

    # Cabo da lupa
    angle = math.radians(135)
    hx1 = int(gcx + gr * math.cos(angle))
    hy1 = int(gcy + gr * math.sin(angle))
    hx2 = int(hx1 + gr * 0.85 * math.cos(angle))
    hy2 = int(hy1 + gr * 0.85 * math.sin(angle))
    d.line([hx1, hy1, hx2, hy2], fill=gl, width=lw + 1)

    # ── Indicador de estado (ponto colorido, canto superior direito) ────────
    ds = max(7, s // 9)
    dx = s - ds - 3
    dy = 3
    # Sombra suave
    d.ellipse([dx - 1, dy - 1, dx + ds + 1, dy + ds + 1],
              fill=(*p["bg"][:3], 200))
    d.ellipse([dx, dy, dx + ds, dy + ds], fill=p["dot"])

    return img


def create_icon_set(base_size: int = 256) -> dict:
    """Retorna dicionário com ícones para todos os estados e tamanhos."""
    states  = ["active", "paused", "stopped"]
    sizes   = [16, 32, 48, 64, 128, base_size]
    result  = {}
    for state in states:
        result[state] = {sz: create_tray_icon(sz, state) for sz in sizes}
    return result


def save_ico_file(path: str, size: int = 256) -> None:
    """
    Salva um arquivo .ico multi-resolução para uso no executável.
    Inclui tamanhos 16, 32, 48, 64, 128 e 256 px.
    """
    base = create_tray_icon(size, "active")
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = [base.resize(sz, Image.LANCZOS) for sz in sizes]
    images[0].save(
        path,
        format="ICO",
        sizes=[(im.width, im.height) for im in images],
        append_images=images[1:],
    )