from hmac import new
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from xcd.core.XCD_kits import KITS
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import  Paragraph, KeepInFrame
from collections import Counter
import pandas as pd
import re
import math
# ----------------------
# Font (Calibri Light → fallback Helvetica)
# ----------------------
try:
    pdfmetrics.registerFont(TTFont("CalibriLight", "calibril.ttf"))
    pdfmetrics.registerFont(TTFont("Calibri", "calibri.ttf"))
    pdfmetrics.registerFont(TTFont("CalibriItalic", "calibrii.ttf"))
    pdfmetrics.registerFont(TTFont("CalibriLightItalic", "calibrili.ttf"))
    DEFAULT_FONT = "CalibriLight"
except Exception:
    DEFAULT_FONT = "Helvetica"

# ----------------------
# Parametry
# ----------------------
HEIGHT_THRESHOLD = 50
SIZE_TOLERANCE = 0.25
FONT_MIN, FONT_MAX = 5.0, 16.0
ROW_HEIGHT_MARKER = 24   # markerové řádky
ROW_HEIGHT_QUANT = 16    # kvantifikační řádky
COL_WIDTHS = [60] + [120, 120, 120, 120]

# Barvy lokusů (Y → black pro čitelnost)
DYE_COLORS = {
    "B": colors.blue,
    "G": colors.green,
    "Y": colors.black,   # žlutý kanál tiskneme černě
    "R": colors.red,
    "P": colors.purple
}

def format_locus_for_log(locus: str, dye: str) -> Paragraph:
    """Vrátí Paragraph pro lokus v logu, barevně podle dye."""
    style = ParagraphStyle(
        name="LogLocus",
        fontName="Calibri",
        fontSize=9,
        textColor=DYE_COLORS.get(str(dye), colors.black),
        alignment=0
    )
    return Paragraph(locus, style)

def merged_kit_order(kit_name: str):
    """Vrátí pořadí lokusů dle zvoleného kitu; QS1 a QS2 sloučí na QS1|QS2, pokud existují."""
    base = KITS[kit_name]
    out = []
    skip = set()
    for loc in base:
        if loc in skip:
            continue
        if loc == "QS1":
            out.append("QS1|QS2")
            skip.add("QS2")
        elif loc == "QS2":
            if "QS1|QS2" not in out:
                out.append("QS1|QS2")

        elif loc == "IQCS":
            out.append("IQCS|IQCL")
            skip.add("IQCL")
        elif loc == "IQCL":
            if "IQCS|IQCL" not in out:
                out.append("IQCS|IQCL")

        else:
            out.append(loc)
    return out

# ----------------------
# Pomocné funkce
# ----------------------
def font_size_from_height(height, local_max):
    if not height or height <= 0 or not local_max:
        return FONT_MIN
    if height <= 50:
        return FONT_MIN
    scale = (height - 50) / (local_max - 50) if local_max > 50 else 1
    scale = max(0, min(scale, 1))
    size = FONT_MIN + (FONT_MAX - FONT_MIN) * scale
    return round(size * 2) / 2

def measure_alleles_width(alleles, font_sizes, bold_indices, highlight_major):
    width = 0.0
    for idx, ((allele, _), fs) in enumerate(zip(alleles, font_sizes)):
        font = "Calibri" if (highlight_major and idx in bold_indices) else "CalibriLight"
        width += pdfmetrics.stringWidth(str(allele), font, fs)
        if idx < len(alleles) - 1:
            width += pdfmetrics.stringWidth("|", font, fs)
    return width

def format_alleles_for_cell(
    alleles,
    local_max,
    is_fu,
    highlight_major=False,
    cell_width=120,
    bold_indices=None,
    safe_width=None,
    allow_wrap=False,
):
    """
    Varianta A:
    - zalamuje pouze za '|'
    - nejdřív rozdělení do řádků, pak shrink jen pro přetékající řádky
    - zachovává rozdíly výšek (škálování je jednotným koeficientem v rámci řádku)
    """

    if not alleles:
        return ""

    if bold_indices is None:
        bold_indices = []

    # --- vyber šířku buňky ---
    if isinstance(safe_width, (list, tuple)):
        # když někdo omylem pošle list, vezmi minimum čísel
        safe_w = min([w for w in safe_width if isinstance(w, (int, float))] or [cell_width or 120])
    elif isinstance(safe_width, (int, float)):
        safe_w = float(safe_width)
    else:
        safe_w = float(cell_width or 120)

    col_w = min(float(cell_width or 120), safe_w)

    # !!! Tohle je zásadní: rezerva byla moc velká -> shrink i když není potřeba
    PAD = 4.0  # zkus klidně 2.0
    inner_width = col_w - PAD
    if inner_width < 30:
        inner_width = 30.0

    # --- font limity ---
    try:
        _FONT_MIN = float(FONT_MIN)
    except Exception:
        _FONT_MIN = 5.0
    try:
        _FONT_MAX = float(FONT_MAX)
    except Exception:
        _FONT_MAX = 16.0

    FONT_MAJOR = "Calibri"
    FONT_MINOR = "CalibriLight"

    def _w(txt: str, font_name: str, size: float) -> float:
        try:
            return pdfmetrics.stringWidth(str(txt), font_name, float(size))
        except Exception:
            # fallback – když font není registrovaný
            return pdfmetrics.stringWidth(str(txt), DEFAULT_FONT, float(size))

    # --- základní velikosti alel (bez shrinku) ---
    base_sizes = []
    for allele, height in alleles:
        if is_fu:
            fs = font_size_from_height(height, local_max)
        else:
            fs = _FONT_MAX
        try:
            fs = float(fs)
        except Exception:
            fs = _FONT_MAX
        fs = max(_FONT_MIN, min(_FONT_MAX, fs))
        base_sizes.append(fs)

    def _sep_fs(sizes_in_line):
        # separátor drž spíš menší, aby to nehonilo šířku
        return max(_FONT_MIN, min(sizes_in_line) if sizes_in_line else _FONT_MIN)

    # --- 1) rozdělení do řádků (bez shrinku) ---

    if not allow_wrap:
        lines = [list(range(len(alleles)))]
    else:
        lines = []
        cur = []
        cur_w = 0.0

        for i, ((allele, _h), fs) in enumerate(zip(alleles, base_sizes)):
            is_bold = (highlight_major and i in bold_indices)
            fnt = FONT_MAJOR if is_bold else FONT_MINOR

            piece_w = _w(str(allele), fnt, fs)

            if cur:
                # šířka separátoru se počítá stejným stylem jako se bude renderovat
                sep_size = _sep_fs([base_sizes[k] for k in cur + [i]])
                piece_w += _w("|", FONT_MINOR, sep_size)

            if cur and (cur_w + piece_w) > inner_width:
                lines.append(cur)
                cur = [i]
                cur_w = _w(str(allele), fnt, fs)
            else:
                cur.append(i)
                cur_w += piece_w

        if cur:
            lines.append(cur)

    # --- 2) shrink jen pro řádky, které přetékají (multiplikativně!) ---
    final_sizes = list(base_sizes)

    # dovol menší minimum pouze pro nouzový shrink – ale NIKDY "odečítáním"
    ABS_MIN = max(3.0, _FONT_MIN - 2.0)

    def _line_width(line_indices, sizes):
        total = 0.0
        sep_fs = _sep_fs([sizes[k] for k in line_indices])
        for j, idx in enumerate(line_indices):
            allele, _h = alleles[idx]
            fs = sizes[idx]
            is_bold = (highlight_major and idx in bold_indices)
            fnt = FONT_MAJOR if is_bold else FONT_MINOR
            total += _w(str(allele), fnt, fs)
            if j < len(line_indices) - 1:
                total += _w("|", FONT_MINOR, sep_fs)
        return total

    for line in lines:
        lw = _line_width(line, final_sizes)
        if lw <= inner_width:
            continue

        # základní scale podle poměru šířek
        s = (inner_width / lw) if lw > 0 else 0.9
        s *= 0.995  # malá rezerva

        # aplikuj jednotný scale na celý řádek => zachová poměry
        for idx in line:
            final_sizes[idx] = max(ABS_MIN, base_sizes[idx] * s)

        # když pořád přetéká (kvůli odhadu fontů/padding), dotahuj *multiplikací*
        # -> zachová rozdíly výšek
        for _ in range(40):
            lw2 = _line_width(line, final_sizes)
            if lw2 <= inner_width:
                break
            for idx in line:
                final_sizes[idx] = max(ABS_MIN, final_sizes[idx] * 0.98)

    # --- 3) render: více řádků + zvláštní leading jen pro multiline ---
    rendered_lines = []
    for line in lines:
        parts = []
        sizes_in_line = [final_sizes[k] for k in line]
        sep_size = _sep_fs(sizes_in_line)

        for j, idx in enumerate(line):
            allele, _h = alleles[idx]
            fs = final_sizes[idx]
            is_bold = (highlight_major and idx in bold_indices)
            fnt = FONT_MAJOR if is_bold else FONT_MINOR
            parts.append(f'<font name="{fnt}" size="{fs:.2f}">{allele}</font>')
            if j < len(line) - 1:
                parts.append(f'<font name="{FONT_MINOR}" size="{sep_size:.2f}">|</font>')

        rendered_lines.append("".join(parts))

    text = "<br/>".join(rendered_lines)

    max_fs = max(final_sizes) if final_sizes else 10.0
    
    leading = max_fs + 4.0
    text = rendered_lines[0]

    style = ParagraphStyle(
        name="Alela",
        fontName=DEFAULT_FONT,
        fontSize=max_fs,
        leading=leading,
        textColor=colors.black,
        alignment=0,
        spaceBefore=0,
        spaceAfter=0,
        splitLongWords=0,
    )

    return Paragraph(text, style)

def sort_alleles_numeric(alleles):
    """
    Seřadí alely číselně podle jejich hodnoty (pokud to jde).
    """
    def parse_val(a):
        try:
            return float(a[0])  # hodnota alely jako číslo
        except Exception:
            return a[0]         # fallback na text (např. 'OL')
    return sorted(alleles, key=parse_val)

HEIGHT_THRESHOLD = 50
SIZE_TOLERANCE = 0.25  # tolerance ve velikosti (bp) pro porovnání s ladderem

# ----------------------
# Povolené mikrovarianty dle motivu
# ----------------------

def infer_motif_from_ladder(ladder_alleles):
    """
    Odhad délky motivu z ladderu:
    - vezme pouze CELÉ alely (8, 9, 10, ...)
    - seřadí je podle čísla alely
    - spočítá rozdíly bp jen mezi SOUSEDNÍMI celými alelami (8->9, 9->10, ...)
    - vrátí nejpravděpodobnější motiv (typicky 3/4/5/6)
    """
    if not ladder_alleles:
        return None

    # sjednotit na iterable položek (může být dict nebo list)
    if hasattr(ladder_alleles, "items"):
        items = list(ladder_alleles.items())  # (allele, bp)
    else:
        items = list(ladder_alleles)

    ints = []
    for it in items:
        # podporuj (a,bp), (a,bp,a_num) i delší tuple
        if len(it) < 2:
            continue
        a = it[0]
        bp = it[1]

        # získej numerickou alelu
        a_num = None
        if len(it) >= 3:
            a_num = it[2]
        if a_num is None:
            try:
                a_num = float(str(a).replace(",", "."))
            except Exception:
                a_num = None

        try:
            if a_num is None or bp is None:
                continue
            a_num_f = float(a_num)
            if not a_num_f.is_integer():
                continue
            ints.append((int(a_num_f), float(bp)))
        except Exception:
            continue

    # pro sousední rozdíly stačí 2 celé alely
    if len(ints) < 2:
        return None

    # seřadit podle čísla alely
    ints.sort(key=lambda x: x[0])

    # vytvořit mapu allele->bp (kdyby byly duplicity, necháme poslední)
    allele_to_bp = {a: bp for a, bp in ints}
    alleles_sorted = sorted(allele_to_bp.keys())

    # rozdíly jen mezi sousedními celými alelami
    diffs = []
    for a1, a2 in zip(alleles_sorted, alleles_sorted[1:]):
        bp1 = allele_to_bp[a1]
        bp2 = allele_to_bp[a2]
        d = abs(bp2 - bp1)
        if d > 0:
            diffs.append(d)

    if not diffs:
        return None

    # robustní výběr: nejčastější diff po zaokrouhlení na 0.01
    diffs_r = [round(d, 2) for d in diffs]

    # mode (nejčastější); při shodě vezmi medián
    from collections import Counter
    c = Counter(diffs_r)
    top = c.most_common()
    best_diff = top[0][0]

    # převod diff -> motif: vezmi nejbližší z typických motivů
    candidates = [3, 4, 5, 6]
    motif = min(candidates, key=lambda m: abs(m - best_diff))

    return motif

def max_micro_decimal(motif_len: int) -> float:
    # pro tetramer .1-.3, pro pentamer .1-.4, pro trimer .1-.2, atd.
    return (motif_len - 1) / 10.0  # 4→0.3, 5→0.4->

def transform_ol_with_ladder(meas_size: float,
                             ladder_ref: list,
                             size_tol: float,
                             locus: str) -> str | None:
    """
    Převod OL → alelová hodnota.

    Logika:
    1) Najde sousední celé alely (below/above). Když chybí, dopočítá (extrapolace).
    2) Nejdřív zkusí, zda OL nesedí na celé alele (below nebo above) v toleranci.
    3) Pokud ne, spočítá mikrovariantu mezi below→above (1..motif-1) a ověří toleranci.
    """

    # --- Základní kontrola ---
    if meas_size is None or not ladder_ref:
        return None

    motif = infer_motif_from_ladder(ladder_ref)
    if motif is None:
        return None

    # --- Připrav integer body z ladderu ---
    # ladder_ref očekává: (allele_label, size_bp, allele_numeric_or_None)
    int_pts = [(float(a), float(s)) for (a, s, a_num) in ladder_ref
               if a_num is not None and float(a_num).is_integer()]

    if len(int_pts) < 1:
        return None

    # řadíme podle velikosti v bp
    int_pts.sort(key=lambda x: x[1])

    # --- typický sklon v bp/repeat (z celých alel) ---
    if len(int_pts) >= 2:
        diffs = [int_pts[i + 1][1] - int_pts[i][1] for i in range(len(int_pts) - 1)]
        diffs = [d for d in diffs if d > 0]
        bp_per_repeat = (sum(diffs) / len(diffs)) if diffs else 4.0
    else:
        bp_per_repeat = 4.0  # nouzová defaultní hodnota

    below = None
    above = None

    # --- hledej přirozené sousedy (mezi dvěma celými alelami) ---
    for i in range(len(int_pts) - 1):
        s1 = int_pts[i][1]
        s2 = int_pts[i + 1][1]
        if s1 <= meas_size <= s2:
            below = int_pts[i]
            above = int_pts[i + 1]
            break

    # --- extrapolace, když je mimo rozsah ladderu ---
    if below is None and meas_size > int_pts[-1][1]:
        below = int_pts[-1]
        above = (below[0] + 1, below[1] + bp_per_repeat)

    if above is None and meas_size < int_pts[0][1]:
        above = int_pts[0]
        below = (above[0] - 1, above[1] - bp_per_repeat)

    # --- pokud pořád nic ---
    if below is None or above is None:
        return None

    #print("[OL] below:", below, "above:", above)

    # --- výpočty ---
    a_below, s_below = below
    a_above, s_above = above

    # bezpečnost proti dělení nulou
    if a_above == a_below:
        return None

    slope_bp_per_repeat = (s_above - s_below) / (a_above - a_below)

    # 1) Nejprve zkus „celou alelu“ (typicky když OL sedí na 28 a ladder končí 27)
    d_above = meas_size - s_above
    d_below = meas_size - s_below

    if abs(d_above) <= size_tol:
        allele_int = str(int(round(a_above)))
        #print(f"[OL→allele] {locus}: ✅ celé allele {allele_int} "
        #      f"(|Δ|={abs(d_above):.3f} ≤ {size_tol})")
        return allele_int

    if abs(d_below) <= size_tol:
        allele_int = str(int(round(a_below)))
        #print(f"[OL→allele] {locus}: ✅ celé allele {allele_int} "
        #      f"(|Δ|={abs(d_below):.3f} ≤ {size_tol})")
        return allele_int

    # 2) Mikrovarianta mezi below→above
    bp_per_nt = slope_bp_per_repeat / motif

    candidates = range(1, motif)  # mikrovarianty 1..motif-1
    best_nt = None
    best_diff = None

    for nt in candidates:
        expected = s_below + nt * bp_per_nt
        diff = meas_size - expected

        if best_diff is None or abs(diff) < abs(best_diff):
            best_diff = diff
            best_nt = nt

    if best_nt is None:
        return None

    extra_nt = best_nt
    expected_bp = s_below + extra_nt * bp_per_nt
    diff_bp = meas_size - expected_bp

    #print(f"[OL→allele] {locus}: size={meas_size:.2f} bp | "
    #      f"below={a_below}@{s_below:.2f} | above={a_above}@{s_above:.2f} | "
    #      f"motif={motif} | Δbp/repeat={slope_bp_per_repeat:.2f} | "
    #      f"→ extra_nt={extra_nt} | diff={diff_bp:.3f} bp")

    # --- kontrola rozsahu mikrovarianty ---
    if extra_nt <= 0 or extra_nt > motif - 1:
        #print(f"[OL→allele] {locus}: ❌ mimo rozsah mikrovarianty ({extra_nt})")
        return None

    allele_val = f"{int(a_below)}.{extra_nt}"

    # --- ověření tolerance ---
    if abs(diff_bp) <= size_tol:
        #print(f"[OL→allele] {locus}: ✅ transformováno na {allele_val} "
        #      f"(|Δ|={abs(diff_bp):.3f} ≤ {size_tol})")
        return allele_val
    else:
        #print(f"[OL→allele] {locus}: ❌ zamítnuto (|Δ|={abs(diff_bp):.3f} > {size_tol})")
        return None


# ----------------------
# Artefakty
# ----------------------

def detect_artifact(allele, height, size,
                    locus_alleles, dye, all_sample_alleles, locus_name=None):
    """
    Vrací důvod artefaktu, nebo None.
    - locus_alleles: [(allele, height)] pro kontrolu stutteru
    - all_sample_alleles: [(size, dye, allele, height)] pro pull-up (jen v rámci vzorku)
    """
    if height < HEIGHT_THRESHOLD:
        return "artefakt (pod prahem RFU)"

    # stutter (±1 repeat od silnější alely v lokusu a RFU výrazně nižší)
    for main_allele, main_height in locus_alleles:
        try:
            a_val = float(allele)
            m_val = float(main_allele)
            if abs(a_val - m_val) == 1 and height < 0.03 * (main_height or 1):
                return f"stutter alely {main_allele}"
        except Exception:
            continue

    # pull-up (stejná size jako jiný peak, ale jiný dye, v tomtéž vzorku)

    for s, d, a, h, _ in all_sample_alleles:
        try:
            if abs(size - s) <= SIZE_TOLERANCE and dye != d:
                # Definuj barvy pro PDF
                dye_colors_html = {
                    "B": "#0070C0",    # Blue
                    "G": "#00B050",    # Green
                    "Y": "#FFD700",    # Yellow
                    "R": "#FF0000",    # Red
                    "P": "#7030A0",    # Purple
                }
                color_html = dye_colors_html.get(d, "#000000")

                # Poznámka pro log s barvou lokusu
                return (
                    f"pull-up z alely <b>{a}</b> "
                    f"(<font color='{color_html}'>{locus_name or '?'} ({d}))</font>"
                )
        except Exception:
            continue

    return None

def _is_nan(x):
    return isinstance(x, float) and math.isnan(x)

def safe_str(x):
    if x is None or _is_nan(x):
        return ""
    return str(x)
def safe_join(sep, items):
    return sep.join(safe_str(i) for i in items if i is not None and not _is_nan(i))

def _norm_allele_for_log(a):
    if a is None:
        return ""
    s = str(a).strip()
    if s.upper() == "OL":
        return "OL"
    return normalize_allele_str(s)

def append_log_unique(log_list, sample, locus, allele, reason, dye, sort_allele=None):
    if log_list is None:
        return

    sample_s = str(sample).strip()
    locus_s  = str(locus).strip()
    reason_s = (str(reason) if reason is not None else "").strip()

    allele_s = _norm_allele_for_log(allele)
    sort_s   = _norm_allele_for_log(sort_allele if sort_allele is not None else allele)

    key = (sample_s, locus_s, allele_s, reason_s)

    for e in log_list:
        e_key = (
            str(e.get("Sample", "")).strip(),
            str(e.get("Locus", "")).strip(),
            _norm_allele_for_log(e.get("Allele")),
            (str(e.get("Reason")) if e.get("Reason") is not None else "").strip()
        )
        if e_key == key:
            return

    log_list.append({
        "Sample": sample_s,
        "Locus": locus_s,
        "Allele": allele_s,
        "SortAllele": sort_s,
        "Reason": reason_s,
        "Dye": dye,
    })


def detect_cluster_artifact(locus_peaks, log_list, sample, locus, dye):
    """
    Detekuje clustery – skupiny ≥3 slabých píků (<10 % maxima lokusu)
    s podobnou výškou (≤2.5× rozdíl) a vzdáleností sousedních <2 bp.
    Vrací seznam alel (bez OL), které patří do clusteru.
    """
    if not locus_peaks or len(locus_peaks) < 3:
        return []

    # validní píky s výškou
    valid_peaks = [(a, s, h) for a, s, h in locus_peaks if h and h > 0]
    if len(valid_peaks) < 3:
        return []

    # maximum lokusu
    max_height = max(h for _, _, h in valid_peaks)

    # jen slabé píky (≤10 % maxima)
    low_peaks = [(a, s, h) for a, s, h in valid_peaks if h <= 0.10 * max_height]
    if len(low_peaks) < 3:
        return []

    # seřaď podle velikosti
    low_peaks.sort(key=lambda x: x[1])

    clusters = []
    current_cluster = [low_peaks[0]]

    MAX_GAP_BP = 2.0        # mezera mezi sousedními píkami
    HEIGHT_RATIO_TOL = 2.5  # max. poměr výšek v rámci clusteru

    # --- seskupování podle blízkosti ---
    for i in range(1, len(low_peaks)):
        prev = low_peaks[i - 1]
        curr = low_peaks[i]
        if curr[1] - prev[1] <= MAX_GAP_BP:
            current_cluster.append(curr)
        else:
            if len(current_cluster) >= 3:
                clusters.append(current_cluster)
            current_cluster = [curr]
    if len(current_cluster) >= 3:
        clusters.append(current_cluster)

    clustered_alleles = set()

    # --- kontrola výšek v každém clusteru ---
    for group in clusters:
        heights = [h for _, _, h in group]
        if max(heights) / min(heights) <= HEIGHT_RATIO_TOL:
            # ignoruj clustery tvořené výhradně OL
            numeric_group = [
                a for a, _, _ in group
                if safe_str(a) and not safe_str(a).upper().startswith("OL")
            ]
            if not numeric_group:
                continue

            # normalizuj + unikátní + stabilní pořadí
            numeric_norm = [normalize_allele_str(a) for a in numeric_group]
            numeric_norm = sorted(set(numeric_norm), key=lambda x: float(x) if str(x).replace(".", "", 1).isdigit() else str(x))

            # interval clusteru do Reason
            cluster_interval = " - ".join(numeric_norm)
            reason_text = f"cluster artefakt {cluster_interval}"

            # přidej do seznamu odstraněných (pro návrat)
            clustered_alleles.update(numeric_norm)

            for a in numeric_norm:
                append_log_unique(log_list, sample, locus, a, reason_text, dye)

    return list(clustered_alleles)



# ----------------------
# Validate allele
# ----------------------

def validate_allele(allele, height, size, area,
                    ladder_sizes,
                    sample=None, case_id=None, run=None, kit=None,
                    locus=None, dye=None,
                    log_list=None, is_fu=False,
                    locus_alleles=None,
                    all_sample_alleles=None,
                    locus_all_heights=None):

    if pd.isna(allele) or pd.isna(height) or pd.isna(size):
        return None

    # --- CLUSTER ARTIFACT DETECTION ---

    locus_peaks = []
    if all_sample_alleles:
            for s, d, a, h, loc in all_sample_alleles:
                if loc == locus:
                    locus_peaks.append((a, s, h))
    
    if not any (a ==allele for a, _, _ in locus_peaks):
        locus_peaks.append((allele, size, height))

    clustered = detect_cluster_artifact(locus_peaks, log_list, sample, locus, dye)
    if allele in clustered:
        return None

    if str(allele).upper() == "OL":

        # --- Spočítej maximum z výšek všech alel v aktuálním lokusu ---
        heights_in_locus = locus_all_heights or []
        max_height = max(heights_in_locus) if heights_in_locus else 0

        # dynamický práh (10 % maxima, min. 100 RFU)
        dynamic_threshold = max(100, max_height * 0.10)
        # bezpečně převeď výšku aktuální OL
        try:
            h_val = float(height) if height is not None else 0
        except Exception:
            h_val = 0

        # --- Filtr: OL pod 10 % maxima se rovnou vyřadí ---
        if h_val < dynamic_threshold:
            # (nechceme logovat, jen odstranit)
            return None

        # --- Kontrola poměru plocha/výška (geometrický filtr) ---
        try:
            if not area or float(area) / h_val < 7 or float(area) / h_val > 15:
                return None
        except Exception:
            return None

        # --- Transformace OL podle ladderu ---
        new_label = transform_ol_with_ladder(size, ladder_sizes, SIZE_TOLERANCE, locus or "")

        if new_label:
            # Pokud je směsný vzorek (FU), zapíšeme transformaci do logu
            append_log_unique(log_list, sample, locus, "OL", f"transformace OL -> {new_label}", dye, sort_allele=new_label)
            return new_label

        # pokud se OL nepodaří transformovat, odstraníme ji
        return None


    # --- kontrola morfologie jen pro reálné alely ---
    if height and area:
        ratio = area / height
        if ratio < 7 or ratio > 15:
            if is_fu:
                append_log_unique(log_list, sample, locus, allele, "špatná morfologie peaku", dye)
            return None

    # --- artefakty (pod RFU, stutter, pull-up) ---
    reason = detect_artifact(
        allele, height, size,
        locus_alleles=locus_alleles or [],
        dye=dye,
        all_sample_alleles=all_sample_alleles or [],
        locus_name=locus,
    )

    if reason:
        if is_fu:
            append_log_unique(log_list, sample, locus, allele, f"{reason}", dye)
        return None

    # --- validní alela ---
    return normalize_allele_str(allele)

def select_alleles(alleles, is_fu):
    """
    Vrátí seznam alel podle typu vzorku:
    - FU (směsný profil) → všechny alely, seřazené číselně.
    - ne-FU (srovnávací vzorek) → 2 nejsilnější podle height,
      potom seřazené číselně.
    """
    if is_fu:
        return sort_alleles_numeric(alleles)
    else:
        # vyber top2 podle RFU
        top2 = sorted(alleles, key=lambda x: x[1] or 0, reverse=True)[:2]
        # seřaď top2 číselně
        return sort_alleles_numeric(top2)


def parse_sample_name(sample: str, pattern: str):
    """
    Rozkóduje název vzorku podle patternu (např. 'iiyydCCCCdssnn').
    Malá písmena = přesný počet znaků
    Velká písmena = proměnlivá délka (1+)
    """

    sample = sample.strip()

    # mapování symbolů
    mapping = {
        "i": r"[A-Z]",
        "I": r"[A-Z]+",
        "y": r"\d",
        "Y": r"\d+",
        "c": r"\d",
        "C": r"\d+",
        "s": r"[A-Z]",
        "S": r"[A-Z]+",
        "n": r"\d",
        "N": r"\d+",
        "d": r"[-_]",
    }

    regex = "".join(mapping.get(ch, ch) for ch in pattern)
    match = re.match(regex, sample)
    if not match:
        return None

    # extrakce konkrétních částí podle pořadí
    parts = {"id": "", "year": "", "case": "", "type": "", "num": ""}
    for ch, val in zip(pattern, sample):
        if ch.lower() == "i":
            parts["id"] += val
        elif ch.lower() == "y":
            parts["year"] += val
        elif ch.lower() == "c":
            parts["case"] += val
        elif ch.lower() == "s":
            parts["type"] += val
        elif ch.lower() == "n":
            parts["num"] += val
    return parts



def get_case_id(sample_name: str, pattern: str = None):
    if not sample_name:
        return ""
    if pattern:
        parsed = parse_sample_name(sample_name, pattern)
        if parsed and parsed["case"] and parsed["year"]:
            return f"{int(parsed['case'])}/{parsed['year']}"
        elif parsed and parsed["case"]:
            return str(int(parsed["case"]))
    # fallback – původní metoda
    parts = str(sample_name).split("-")
    return "-".join(parts[:2]) if len(parts) >= 2 else sample_name


def get_case_prefix(sample_name: str, pattern: str = None):
    
    sample_name = sample_name.strip().upper()
    if "-" in sample_name:
        parts = sample_name.split("-")
        if len(parts)>= 3:
            return "-".join(parts[:2])
        elif len(parts) == 2:
            return parts[0]
    return sample_name

def get_expert_code(sample_name: str, pattern: str = None):
    if not sample_name:
        return ""
    if pattern:
        parsed = parse_sample_name(sample_name, pattern)
        if parsed and parsed["id"]:
            return parsed["id"]
    s = str(sample_name)
    return s[:2] if len(s) >= 2 and s[:2].isalpha() else ""

def is_fu_sample(sample: str) -> bool:
    """
    Rozšířená detekce směsných (FU) vzorků.
    True = směs (obsahuje 'FU' nebo končí číselnou částí)
    False = srovnávací (koncovka 3–4 písmena, např. -UBP, -GIH)
    """
    if not sample:
        return False

    s = sample.upper().strip()

    # 1️⃣ klasické FU označení
    if "-FU" in s:
        return True

    # klasické buk označení
    if any(tag in s for tag in ["-ZZ", "-SK","-VK", "-OF", "-BF", "-BM", "-BS"]):
        return False

    # 2️⃣ koncovka po poslední pomlčce
    m = re.search(r"-([A-Z0-9]+)$", s)
    if not m:
        return False  # nemá pomlčku → považujeme za srovnávací

    suffix = m.group(1)

    # 3️⃣ pouze písmena (3–4 znaky) → srovnávací
    if re.fullmatch(r"[A-Z]{3,4}", suffix):
        return False



def top2_alleles(alleles, min_ratio=0.3):
    """
    Vrátí maximálně dvě nejvyšší alely podle RFU.
    Druhá je zahrnuta pouze tehdy, pokud má alespoň
    `min_ratio` (např. 0.3 = 30 %) výšky první alely.
    """

    if not alleles:
        return []

    # 1) seřaď podle RFU (od nejvyšší)
    sorted_alleles = sorted(
        alleles,
        key=lambda x: (x[1] or 0),
        reverse=True
    )

    # 2) vyber top alely podle RFU
    top = [sorted_alleles[0]]

    if len(sorted_alleles) > 1:
        top1_h = sorted_alleles[0][1] or 0
        top2_h = sorted_alleles[1][1] or 0
        if top2_h >= min_ratio * top1_h:
            top.append(sorted_alleles[1])

    # 3) 🔑 FINÁLNÍ SEŘAZENÍ PODLE HODNOTY ALELY (ne RFU)
    def allele_value_key(a):
        s = normalize_allele_str(a)
        try:
            return (0, float(s))
        except Exception:
            return (1, s)

    top = sorted(top, key=lambda t: allele_value_key(t[0]))

    return top


def normalize_allele_str(a):
    try:
        f = float(a)
        if f.is_integer():
            return str(int(f))
        else:
            return str(f).rstrip("0").rstrip(".")
    except Exception:
        return str(a)
    


def normalize_sample_name(name: str) -> str:
    """Ořízne, převede na velká písmena a sjednotí formátování názvu vzorku."""
    return str(name).strip().upper()

