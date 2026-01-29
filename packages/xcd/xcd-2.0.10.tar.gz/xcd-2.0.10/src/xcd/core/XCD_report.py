from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from xcd.core.XCD_kits import KITS, KIT_TYPE, KIT_SPLITS
from xcd.core import XCD_utils, XCD_parsing, XCD_db
import os, sys, subprocess
from datetime import datetime
import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from tempfile import gettempdir

# ----------------------
# Font (Calibri Light → fallback Helvetica)
# ----------------------
try:
    pdfmetrics.registerFont(TTFont("CalibriLight", "calibril.ttf"))
    pdfmetrics.registerFont(TTFont("Calibri", "calibri.ttf"))
    pdfmetrics.registerFont(TTFont("CalibriBold", "calibrib.ttf"))
    pdfmetrics.registerFont(TTFont("CalibriItalic", "calibrii.ttf"))
    pdfmetrics.registerFont(TTFont("CalibriLightItalic", "calibrili.ttf"))
    DEFAULT_FONT = "CalibriLight"
except Exception:
    DEFAULT_FONT = "Helvetica"

# ----- Konstanta rozměrů
ROW_HEIGHT_MARKER = 20
ROW_HEIGHT_QUANT = 14
COL_WIDTHS = [65] + [120, 120, 120, 120]

# Layout widths (sample columns)
SHORT_COL_W = 120
LONG_COL_W = 240

IGNORE_MARKERS_DEFAULT = {"AMEL", "Yindel", "QS1|QS2", "IQCS|IQCL"}

def _is_long_sample(sample: str, samples_dict: dict, allele_threshold: int = 10,
                    ignore_markers: set | None = None) -> bool:
    """Vrátí True pokud má vzorek alespoň v jednom lokusu >= allele_threshold alel.
    Používá stejný filtr markerů jako report (AMEL/QS/… a DYS lokusy ignoruje).
    """
    if not sample or sample not in samples_dict:
        return False
    ignore = ignore_markers or IGNORE_MARKERS_DEFAULT
    max_n = 0
    try:
        for locus, (alleles, _) in samples_dict[sample].items():
            if locus in ignore or locus.startswith("DYS"):
                continue
            if alleles:
                n = len(alleles)
                if n > max_n:
                    max_n = n
                    if max_n >= allele_threshold:
                        return True
    except Exception:
        # pokud je struktura dat nečekaná, nechceme rozbíjet generování – bereme jako short
        return False
    return False


def _plan_batches_with_layout(run_samples: list, samples_dict: dict,
                             allele_threshold: int = 10) -> list[tuple[list, str, list[int]]]:
    """Naplánuje stránky pro jeden run.

    Vrací list položek: (batch, layout, col_widths)
    - layout: 'kkkk', 'dkk', 'kdk', 'kkd', 'dd'
    - batch: seznam vzorků (pro kkkk vždy délka 4; pro mix vždy délka 3; pro dd délka 2)
             prázdné sloty jsou "".
    - col_widths: colWidths pro ReportLab Table (včetně marker sloupce).
    """
    out = []
    i = 0
    n = len(run_samples)

    # předpočítej long/short mapu pro rychlost
    is_long = {s: _is_long_sample(s, samples_dict, allele_threshold=allele_threshold)
               for s in run_samples if s}

    while i < n:
        # 1) kandidát na kkkk (až 4 další vzorky) – povoleno jen pokud všechny existující jsou short
        cand4 = run_samples[i:i+4]
        if cand4 and all(not is_long.get(s, False) for s in cand4 if s):
            batch = cand4[:]
            while len(batch) < 4:
                batch.append("")
            layout = "kkkk"
            col_widths = [COL_WIDTHS[0]] + [SHORT_COL_W] * 4
            out.append((batch, layout, col_widths))
            i += len(cand4)  # spotřebuj reálné vzorky
            continue

        # 2) pokud jsou první dva dlouhé, dej dd
        cand2 = run_samples[i:i+2]
        if len(cand2) == 2 and is_long.get(cand2[0], False) and is_long.get(cand2[1], False):
            batch = cand2[:]
            layout = "dd"
            col_widths = [COL_WIDTHS[0], LONG_COL_W, LONG_COL_W]
            out.append((batch, layout, col_widths))
            i += 2
            continue

        # 3) jinak vezmi mix 3-slot (dkk/kdk/kkd), případně doplň prázdný třetí slot
        cand3 = run_samples[i:i+3]
        # pokud jsou v prvních 3 více než 1 long, ber jen první 2 a třetí nech prázdný (aby se nevešlo 240+120+240)
        long_positions = [idx for idx, s in enumerate(cand3) if s and is_long.get(s, False)]
        if len(long_positions) > 1:
            # spotřebuj jen první 2 (nebo 1 na konci)
            cand = run_samples[i:i+2]
            i += len(cand)
            batch = cand[:]
            while len(batch) < 3:
                batch.append("")
            # urči layout podle long pozice v prvních 2
            lp = [idx for idx, s in enumerate(batch[:2]) if s and is_long.get(s, False)]
            if lp and lp[0] == 0:
                layout = "dkk"
                col_widths = [COL_WIDTHS[0], LONG_COL_W, SHORT_COL_W, SHORT_COL_W]
            elif lp and lp[0] == 1:
                layout = "kdk"
                col_widths = [COL_WIDTHS[0], SHORT_COL_W, LONG_COL_W, SHORT_COL_W]
            else:
                # bez long (fallback) -> chovej se jako krátké 3 sloty
                layout = "dkk"  # vizuálně, ale šířky short
                col_widths = [COL_WIDTHS[0], SHORT_COL_W, SHORT_COL_W, SHORT_COL_W]
            out.append((batch, layout, col_widths))
            continue

        # standardní 3-slot mix
        batch = cand3[:]
        i += len(cand3)
        while len(batch) < 3:
            batch.append("")
        # zvol layout podle pozice long (pokud žádný long, stále dáme 3 short sloty)
        lp = [idx for idx, s in enumerate(batch) if s and is_long.get(s, False)]
        if lp and lp[0] == 0:
            layout = "dkk"
            col_widths = [COL_WIDTHS[0], LONG_COL_W, SHORT_COL_W, SHORT_COL_W]
        elif lp and lp[0] == 1:
            layout = "kdk"
            col_widths = [COL_WIDTHS[0], SHORT_COL_W, LONG_COL_W, SHORT_COL_W]
        elif lp and lp[0] == 2:
            layout = "kkd"
            col_widths = [COL_WIDTHS[0], SHORT_COL_W, SHORT_COL_W, LONG_COL_W]
        else:
            # žádný long -> tři krátké sloupce
            layout = "kkkk"  # obsahově short, ale jen 3 sloty; raději explicitně
            col_widths = [COL_WIDTHS[0], SHORT_COL_W, SHORT_COL_W, SHORT_COL_W]
        out.append((batch, layout, col_widths))

    return out



# Barvy lokusů (žlutý kanál tiskneme černě kvůli čitelnosti)
DYE_COLORS = {
    "B": colors.blue,
    "G": colors.green,
    "Y": colors.black,
    "R": colors.red,
    "P": colors.purple
}

# ---------- Pomocné ----------

def detect_degraded_samples(results, kit_name=None):
    """
    Dynamická detekce degradovaných vzorků podle slope effectu.
    Krátké/dlouhé lokusy se určují automaticky podle pořadí v kitu.
    """
    from xcd.core.XCD_kits import KITS

    degraded = set()
    IGNORE = {"AMEL", "YINDEL", "QS1|QS2", "IQCS|IQCL"}

    # získej pořadí lokusů dle kitu
    KIT_ORDER = KITS.get(kit_name, [])
    if not KIT_ORDER:
        print(f"⚠️ Kit '{kit_name}' nenalezen – slope nebude přesný.")
        return degraded

    n = len(KIT_ORDER)
    if n < 6:
        return degraded  # příliš málo markerů na smysluplné dělení

    # určíme hranice (např. 30 % nejkratších vs. 30 % nejdelších)
    short_idx_limit = max(1, int(n * 0.3))
    long_idx_start = max(short_idx_limit, n - short_idx_limit)

    short_loci = set(KIT_ORDER[:short_idx_limit])
    long_loci = set(KIT_ORDER[long_idx_start:])

    for case_id, samples in results.items():
        for sample, loci in samples.items():
            short_vals, long_vals = [], []

            for locus, (alleles, dye) in loci.items():
                if not alleles or locus in IGNORE or locus.startswith("DYS"):
                    continue

                max_h = max((h for _, h in alleles if h), default=0)
                if max_h <= 0:
                    continue

                if locus in short_loci:
                    short_vals.append(max_h)
                elif locus in long_loci:
                    long_vals.append(max_h)

            if len(short_vals) < 2 or len(long_vals) < 2:
                continue

            avg_short = sum(short_vals) / len(short_vals)
            avg_long = sum(long_vals) / len(long_vals)

            if avg_long == 0:
                continue

            slope = avg_short / avg_long

            # ✅ Klíčová podmínka
            if slope >= 1.5:
                degraded.add(sample)

    return degraded



def format_case_id(case_id: str) -> str:
    """
    Převod: TI25-02507 -> 2507/25, 1565-25-FU01 -> 1565/25, 1565-25 -> 1565/25.
    """
    if not case_id:
        return ""
    
    parts = str(case_id).split("-")
    # 1565-25 -> číslo/rok
    if len(parts) < 2:
        return case_id
    
    prefix = parts[0]
    year = "".join(ch for ch in prefix[-2:] if ch.isdigit())
    number = parts[1]

    if not number.isdigit():
        for seg in parts:
            if seg.isdigit():
                number = seg
                break
    
    number = number.lstrip("0")

    if number and year:
        return f"{number}/{year}"

def make_super_header(case_id, run_header, kit_name, page_number, total_pages, pattern):
    today = datetime.now().strftime("%d.%m.%y")
    if "   " in run_header:
        run, _ = run_header.split("   ", 1)
    else:
        run = run_header

    case_fmt = format_case_id(case_id)
    style_left_bold   = ParagraphStyle("left",   fontName="CalibriBold",      fontSize=10, alignment=1)
    style_left   = ParagraphStyle("left",   fontName="CalibriLight",      fontSize=10, alignment=1)
    style_right  = ParagraphStyle("right",  fontName="CalibriLight",      fontSize=10, alignment=2)

    row = [
        Paragraph(case_fmt, style_left_bold),
        Paragraph(run, style_left),
        Paragraph("Kontrola:", style_left),
        Paragraph(f"List {page_number}/{total_pages}", style_right),
    ]
    return row

def make_log_header(run_header, page_number, total_pages):
    """Hlavička nad log tabulkou – místo čísla případu je 'LOG'."""

    today = datetime.now().strftime("%d.%m.%y")
    if "   " in run_header:
        run, _ = run_header.split("   ", 1)
    else:
        run = run_header

    style_left_bold = ParagraphStyle("left_bold", fontName="Calibri", fontSize=10, alignment=0)
    style_left = ParagraphStyle("left", fontName="Calibri", fontSize=10, alignment=0)
    style_right = ParagraphStyle("right", fontName="Calibri", fontSize=10, alignment=2)

    row = [
        Paragraph("LOG", style_left_bold),
        Paragraph(run, style_left),
        Paragraph(f"", style_left),
        Paragraph(f"List {page_number}/{total_pages}", style_right),
    ]
    return row


def apply_filter(results, mode: str, value: str, pattern: str, sample_meta_all=None, run_headers=None):

    if mode == "VŠE" or not value or value == "__ALL__":
        return results

    def _norm(x):
        return "" if x is None else str(x).strip()

    filtered = {}

    if mode == "SOUPISKA":
        def _norm(x):
            return "" if x is None else str(x).strip()

        wanted = _norm(value)

        if not sample_meta_all:
            print("[WARN] SOUPISKA: chybí sample_meta_all – vracím vše")
            return results

        def belongs(sample: str) -> bool:
            run_name = _norm(sample_meta_all.get(sample, {}).get("run"))
            return run_name == wanted

        # odfiltruj vzorky, které nepatří do vybrané soupisky
        filtered = {
            cid: {s: loci for s, loci in smap.items() if belongs(s)}
            for cid, smap in results.items()
        }

        # vyhoď prázdné případy
        filtered = {cid: smap for cid, smap in filtered.items() if smap}

        return filtered

    if mode == "PŘÍPAD":
        for cid, smap in results.items():
            cid_norm = cid.strip().upper()
            val_norm = value.strip().upper()

            # 🔹 Pokud je ve filter_value lomítko (např. 3352/16)
            if "/" in val_norm:
                try:
                    # vezmeme číslo před lomítkem a doplníme nuly na 5 znaků
                    num = val_norm.split("/")[0].zfill(5)  # 3352 -> 03352
                    # porovnáme podle konce ID nebo přítomnosti čísla
                    if cid_norm.endswith(num) or num in cid_norm:
                        filtered[cid] = smap
                except Exception:
                    pass
            else:
                # klasické přesné porovnání, pokud lomítko není
                if cid_norm == val_norm:
                    filtered[cid] = smap

        return filtered

    if mode == "VZOREK":
        wanted = (value or "").strip()
        for case_id, smap in results.items():
            keep = {}
            for sample, loci in smap.items():
                if (sample or "").strip() == wanted:
                    keep[sample] = loci
            if keep:
                filtered[case_id] = keep

        return filtered



    if mode == "EXPERT":
        for case_id, smap in results.items():
            keep = {}
            for sample, loci in smap.items():
                if XCD_utils.get_expert_code(sample, pattern) == value:
                    keep[sample] = loci
            if keep:
                filtered[case_id] = keep
        return filtered

    return results

def open_file(path):
    if sys.platform.startswith("win"):
        os.startfile(path)  # Windows
    elif sys.platform.startswith("darwin"):
        subprocess.Popen(["open", path])  # macOS
    else:
        subprocess.Popen(["xdg-open", path])  # Linux

def _allele_sort_key(val):
    if val is None:
        return float("inf")

    s = str(val).strip()
    if s.upper() == "OL":
        return float("inf")

    try:
        return float(s)
    except Exception:
        return float("inf")

# ---------- Hlavní generátor ----------

def generate_report(path_txt, path_csv, out_pdf, kit_name, kit_name_auto, kit_name_y,
                    mode_filter="SOUPISKA", filter_value="",
                    highlight_major=False, slope_effect=False,
                    notes_dict=None, verze=None, pattern=None, user_name=None, db_data=None, header_text=None, progress_cb=None):
    """
    Vygeneruje PDF report s DNA profily.
    Struktura výstupu pro každý batch 4 vzorků:
      • Strana A: tabulka profilů → PageBreak
      • Strana B: info blok + (volitelně) log tabulka → PageBreak (kromě úplného konce)
    """
    # -------------------------------------------------
    # 0) DATA Z PARSERU + FILTR
    # -------------------------------------------------
    results, run_headers, df_all, log_list, kits_all, sample_meta_all = XCD_parsing.build_all_results(path_txt)
    filtered = apply_filter(results, mode_filter, filter_value, pattern=pattern, sample_meta_all=sample_meta_all)


    def _is_true_me(x):
        if x is True:
            return True
        s = "" if x is None else str(x).strip().lower()
        return s in ("true", "1", "yes", "y", "t")

    def _modifications_text_for_batch(batch, df_all, locus_order_map=None):
        """
        Vrátí:
        - 'Ne' pokud v batchi není žádná ME=True
        - jinak 'SAMPLE (LOC1, LOC2); SAMPLE2 (LOCX)'
        """
        if df_all is None or "ME" not in df_all.columns:
            return "Ne"

        samples = [s for s in batch if s]
        if not samples:
            return "Ne"

        # jen řádky pro vzorky na stránce
        sub = df_all[df_all["Sample Name"].isin(samples)].copy()
        if sub.empty:
            return "Ne"

        # jen ME==True
        sub = sub[sub["ME"].apply(_is_true_me)]
        if sub.empty:
            return "Ne"

        # ignoruj technické markery, pokud chceš (doporučeno)
        IGNORE_MARKERS = {"AMEL", "Yindel", "QS1|QS2", "IQCS|IQCL"}
        if "Marker" in sub.columns:
            sub["Marker"] = sub["Marker"].astype(str).str.strip()
            sub = sub[~sub["Marker"].isin(IGNORE_MARKERS)]

        out = []
        for s in samples:
            loci = []
            if "Marker" in sub.columns:
                loci = sub.loc[sub["Sample Name"] == s, "Marker"].dropna().unique().tolist()

            if loci:
                if locus_order_map:
                    loci = sorted(loci, key=lambda L: locus_order_map.get(L, 10**6))
                else:
                    loci = sorted(loci)
                out.append(f"{s} ({', '.join(loci)})")

        return "Ne" if not out else "; ".join(out)


    # Bezpečné defaulty
    run_headers     = run_headers or {}
    kits_all        = kits_all or {}
    sample_meta_all = sample_meta_all or {}

    # Čas razítka jednotný pro celý dokument
    now_str = datetime.now().strftime('%d.%m.%Y, %H:%M:%S')

    app_ver = verze 
    # -------------------------------------------------
    # 1) HLAVIČKY A KIT DO TISKU (popisky)
    # -------------------------------------------------
    selected_run  = None
    header_to_use = ""                 # text „Soupiska: …“
    kit_to_print  = kit_name or ""     # text do tabulky (název kitu)

    if mode_filter == "SOUPISKA" and filter_value:
        selected_run  = str(filter_value).strip()
        header_to_use = run_headers.get(selected_run, header_to_use)
        kit_to_print  = kits_all.get(selected_run, kit_to_print)
        # Připrav results jen z dané soupisky
        def _belongs(sample: str) -> bool:
            return sample_meta_all.get(sample, {}).get("run") == selected_run
        results = {cid: {s: loci for s, loci in smap.items() if _belongs(s)} for cid, smap in results.items()}

    # vyhoď prázdné případy
    results = {cid: smap for cid, smap in results.items() if smap}

    # Vypočti jedinečný run/kit pro zvolený subset
    printed_samples = [s for _cid, smap in filtered.items() for s in smap.keys()]
    runs_in_subset = {sample_meta_all.get(s, {}).get("run") for s in printed_samples if s in sample_meta_all}
    kits_in_subset = {sample_meta_all.get(s, {}).get("kit") for s in printed_samples if s in sample_meta_all}
    runs_in_subset.discard(None)
    kits_in_subset.discard(None)

    if not selected_run:
        if len(runs_in_subset) == 1:
            only_run = next(iter(runs_in_subset))
            header_to_use = run_headers.get(only_run, header_to_use)
        elif not header_to_use:
            header_to_use = next(iter(run_headers.values()), "")

    if len(kits_in_subset) == 1:
        kit_to_print = next(iter(kits_in_subset))
    elif not kit_to_print:
        kit_to_print = next(iter(kits_all.values()), kit_name or "")

    def _txt(x):
        if isinstance(x, dict):
            return next(iter(x.values()), "")
        return "" if x is None else str(x).strip()

    header_to_use = _txt(header_to_use)
    kit_to_print  = _txt(kit_to_print)

    # -------------------------------------------------
    # 2) DB DOPLŇKY (kvantifikace, poznámky)
    # -------------------------------------------------

    print("=== DEBUG REPORT QUANT ===")
    print("db_data keys:", db_data.keys())

    if db_data:
        quant_df   = db_data["quant_df"]
        notes_dict = db_data["notes_dict"]
    else:
        quant_df   = XCD_db.get_quant_data(filter_value, path_csv)
        notes_dict = XCD_db.get_sample_notes(filter_value)

    # aliasy / fallbacky sloupců kvantifikace
    def _add_quant_alias_cols(df):
        pairs = {"A": "koncentrace", "Y": "koncentrace_y", "DI_A": "deg_a", "DI_Y": "deg_y"}
        for new, old in pairs.items():
            if new in df.columns and old not in df.columns:
                df[old] = df[new]
            if old in df.columns and new not in df.columns:
                df[new] = df[old]
        return df

    quant_df = _add_quant_alias_cols(quant_df)
    results  = filtered  # dál už pracujeme jen s filtrovaným datasetem

    # Pokud máš v db_data per-sample doplňky do smap, tady je můžeš sloučit
    if db_data:
        for _cid, smap in results.items():
            for s in list(smap.keys()):
                if s in db_data:
                    smap[s].update(db_data[s])

    degraded_samples = detect_degraded_samples(results, kit_name=kit_name)

    # Log omezený jen na vytištěné vzorky
    allowed_samples = {s for _c, smap in results.items() for s in smap.keys()}
    filtered_log = [e for e in log_list if e.get("Sample") in allowed_samples]

    # -------------------------------------------------
    # 3) PROGRESS – POČET STRÁNEK (2 stránky / batch 4 vzorků)
    # -------------------------------------------------
    from collections import defaultdict
    import math

    samples_by_run = defaultdict(list)
    for _cid, smap in results.items():
        for s in smap.keys():
            r = (sample_meta_all.get(s, {}) or {}).get("run") or "_NO_RUN_"
            samples_by_run[r].append(s)

    total_pages_to_build = 0
    for r, sample_list in samples_by_run.items():
        sample_list.sort()
        # 2 stránky na batch
        total_pages_to_build += (math.ceil(len(sample_list) / 4) * 2) if sample_list else 0

    pages_done = 0
    if progress_cb:
        progress_cb(0)

    # -------------------------------------------------
    # 4) PDF DOKUMENT
    # -------------------------------------------------
    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=A4,
        leftMargin=10, rightMargin=10,
        topMargin=10, bottomMargin=10
    )
    elems = []

    # -------------------------------------------------
    # 5) GENEROVÁNÍ – PO CASE → PO RUNU → PO BATCHI
    # -------------------------------------------------
    for case_id, samples_dict in results.items():

        # rozdělit vzorky případu podle runu
        by_run = defaultdict(list)
        for s in sorted(samples_dict.keys()):
            run = (sample_meta_all.get(s, {}) or {}).get("run") or "_NO_RUN_"
            by_run[run].append(s)

        sorted_runs = sorted(by_run.keys(), key=lambda x: (x == "_NO_RUN_", x))

        for run_name in sorted_runs:
            run_samples = by_run[run_name]
            if not run_samples:
                continue

            # naplánuj batchování podle obsahu (short/long)
            planned_batches = _plan_batches_with_layout(run_samples, samples_dict)

            total_pages_for_run = len(planned_batches)  # pro číslování „List x/y“ u runu

            for page_number, (batch, layout, col_widths) in enumerate(planned_batches, start=1):

                # ---- hlavičky per-run ----
                page_header = (run_headers or {}).get(run_name, header_to_use) if run_name != "_NO_RUN_" else header_to_use

                # reálný kit této stránky (z metadat)
                kits_for_page = {
                    sample_meta_all.get(s, {}).get("kit")
                    for s in batch if s and s in sample_meta_all
                }
                kits_for_page.discard(None)
                page_kit = next(iter(kits_for_page)) if len(kits_for_page) == 1 else kit_to_print

                # ---- pořadí lokusů podle UI (AUTO/Y) – přes KIT_TYPE v batchi
                def _batch_is_y_by_type(bat, meta):
                    types = []
                    for _s in bat:
                        if not _s: 
                            continue
                        k = meta.get(_s, {}).get("kit")
                        if k and KIT_TYPE.get(k):
                            types.append(KIT_TYPE[k])
                    return bool(types) and all(t == "Y" for t in types)

                is_y_page = _batch_is_y_by_type(batch, sample_meta_all)
                ui_kit_for_order = kit_name_y if is_y_page else kit_name_auto

                KIT_ORDER_page = []
                if ui_kit_for_order:
                    try:
                        KIT_ORDER_page = XCD_utils.merged_kit_order(ui_kit_for_order)
                    except Exception:
                        KIT_ORDER_page = []
                present_loci = set()
                for s in batch:
                    if not s: 
                        continue
                    present_loci.update((samples_dict.get(s, {}) or {}).keys())
                for locus in sorted(present_loci):
                    if locus not in KIT_ORDER_page:
                        KIT_ORDER_page.append(locus)

                locus_order_map = {locus: i for i, locus in enumerate(KIT_ORDER_page or [])}
                
                def _allele_sort_key(val):
                    # řadí podle SortAllele (pokud existuje), jinak podle Allele
                    if val is None:
                        return (2, float("inf"), "")
                    s = str(val).strip()
                    if s.upper() == "OL":
                        return (2, float("inf"), "OL")
                    # normalizace "20.0" -> "20", "23.20" -> "23.2"
                    s = XCD_utils.normalize_allele_str(s)
                    try:
                        return (0, float(s), s)
                    except Exception:
                        return (1, float("inf"), s)

                # ---- Super hlavička
                super_header_row = make_super_header(
                    case_id, page_header, page_kit or ui_kit_for_order, page_number, total_pages_for_run, pattern
                )
                SUPER_HEADER_COL_RATIOS = [0.15, 0.4, 0.25, 0.15]
                super_header_col_widths = [doc.width * r for r in SUPER_HEADER_COL_RATIOS]

                super_header_table = Table([super_header_row], colWidths=super_header_col_widths)
                
                super_header_table.setStyle(TableStyle([
                    ("LINEBELOW", (0,0), (-1,0), 1, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ]))
                elems.append(super_header_table)
                elems.append(Spacer(1, 6))

                # ---- Hlavní tabulka pro batch
                table = build_case_page(
                    case_id,
                    samples_dict,
                    batch,
                    degraded_samples=degraded_samples,
                    quant_df=quant_df,
                    highlight_major=highlight_major,
                    slope_effect=slope_effect,
                    KIT_ORDER=KIT_ORDER_page,
                    kit_name=ui_kit_for_order,                # řazení/legendy
                    run_header=page_header,
                    page_number=page_number,
                    total_pages=total_pages_for_run,
                    notes_dict=notes_dict,
                    normalized_kit=page_kit or ui_kit_for_order,   # zobrazený název kitu = reálný
                    col_widths=col_widths,
                )

                # -----------------------------
                # A) STRANA: TABULKA → PB
                # -----------------------------
                elems.append(table)
                elems.append(Spacer(1, 5))
                elems.append(PageBreak())
                # progress (po první straně batch)
                if progress_cb and total_pages_to_build:
                    pages_done += 1
                    progress_cb(min(int(pages_done * 100 / total_pages_to_build), 99))


                # ==============================
                # Log odstraněných / transformovaných alel
                # ==============================

                batch_log = [e for e in filtered_log if e.get("Sample") in batch]

                log_table = None
                if batch_log:

                    # --- 1) DEDUP + NORMALIZE (MUSÍ být před groupingem) ---
                    dedup = []
                    seen = set()

                    for e in batch_log:
                        sample = str(e.get("Sample", "")).strip()
                        locus  = str(e.get("Locus", "")).strip()
                        reason = (str(e.get("Reason")) if e.get("Reason") is not None else "").strip()

                        allele_raw = e.get("Allele", "")
                        allele = "OL" if str(allele_raw).upper() == "OL" else XCD_utils.normalize_allele_str(allele_raw)

                        sort_raw = e.get("SortAllele", allele)
                        sort_allele = "OL" if str(sort_raw).upper() == "OL" else XCD_utils.normalize_allele_str(sort_raw)

                        key = (sample, locus, allele, reason)
                        if key in seen:
                            continue
                        seen.add(key)

                        e2 = dict(e)
                        e2["Sample"] = sample
                        e2["Locus"] = locus
                        e2["Reason"] = reason
                        e2["Allele"] = allele
                        e2["SortAllele"] = sort_allele
                        dedup.append(e2)

                    batch_log = dedup

                    # --- 2) pořadí lokusů podle profilu pro tuto stránku ---
                    locus_order_map = {loc: i for i, loc in enumerate(KIT_ORDER_page or [])}

                    # --- 3) klíč pro řazení alel (vzestupně), OL až nakonec ---
                    def _allele_sort_key(val):
                        if val is None:
                            return (2, float("inf"), "")
                        s = str(val).strip()
                        if s.upper() == "OL":
                            return (2, float("inf"), "OL")
                        s = XCD_utils.normalize_allele_str(s)
                        try:
                            return (0, float(s), s)
                        except Exception:
                            return (1, float("inf"), s)

                    # --- 4) seskupit (Sample, Locus) a uvnitř lokusu seřadit alely ---
                    groups = {}
                    for e in batch_log:
                        groups.setdefault((e.get("Sample", ""), e.get("Locus", "")), []).append(e)

                    for k in groups:
                        groups[k].sort(key=lambda e: _allele_sort_key(e.get("SortAllele", e.get("Allele"))))

                    # --- 5) seřadit skupiny: sample -> locus podle profilu ---
                    ordered_keys = sorted(
                        groups.keys(),
                        key=lambda k: (k[0], locus_order_map.get(k[1], 10**6))
                    )

                    # --- 6) sestavit tabulku ---

                    log_table_data = [["Vzorek", "Lokus", "Alela", "Důvod"]]
                    prev_sample, prev_marker = None, None

                    for (sample, marker) in ordered_keys:
                        entries = groups[(sample, marker)]

                        for entry in entries:
                            dye    = entry.get("Dye", None)
                            allele = entry.get("Allele", "")
                            reason = entry.get("Reason", "")

                            sample_disp = "" if sample == prev_sample else sample
                            marker_disp = "" if (sample == prev_sample and marker == prev_marker) else \
                                        XCD_utils.format_locus_for_log(marker, dye)

                            log_table_data.append([sample_disp, marker_disp, allele, reason])
                            prev_sample, prev_marker = sample, marker

                    log_table = Table(log_table_data, hAlign="LEFT", colWidths=[90, 50, 50, 200])


                    log_table.setStyle(TableStyle([
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("FONTNAME", (0, 0), (-1, 0), "Calibri"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 1),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ]))

                # --- test úplného konce
                last_page_of_run = page_number == total_pages_for_run
                last_run_in_case = (run_name == sorted_runs[-1])
                last_case        = (case_id == list(results.keys())[-1])
                at_report_end    = (last_case and last_run_in_case and last_page_of_run)

                # -----------------------------
                # B) STRANA: INFO + (VOL.) LOG → (PB pokud není konec)
                # -----------------------------
                settings_style = ParagraphStyle("Settings", fontName="CalibriLight", fontSize=10, leading=12, textColor=colors.black)
                elems.append(Spacer(1, 5))
                elems.append(Paragraph(f"X-CELL DNA v{app_ver}", settings_style))
                elems.append(Paragraph(f"• Uživatel: {user_name}", settings_style))
                elems.append(Paragraph(f"• Datum a čas odečtu: {now_str}", settings_style))
                modif_text = _modifications_text_for_batch(batch, df_all, locus_order_map=locus_order_map)
                elems.append(Paragraph(f"• Manuální úpravy před odečtem: {modif_text}", settings_style))
                elems.append(Paragraph(f"• Pořadí lokusů podle kitu: {ui_kit_for_order}", settings_style))
                elems.append(Paragraph(f"• Zvýraznění majoritní složky: {'Zapnuto' if highlight_major else 'Vypnuto'}", settings_style))
                elems.append(Paragraph(f"• Slope efekt: {'Zapnut (U degradovaných vzorků je název psán kurzívou)' if slope_effect else 'Vypnut (U degradovaných vzorků je název psán kurzívou)'}", settings_style))

                if log_table is not None:
                    elems.append(Spacer(1, 8))
                    elems.append(Paragraph("<b>Log odstraněných / transformovaných alel</b>", ParagraphStyle("LogHeading", fontName="Calibri", fontSize=11)))
                    elems.append(Spacer(1, 3))
                    elems.append(Spacer(1, 3))
                    elems.append(log_table)
                    elems.append(Spacer(1, 3))

                    LOG_PAGE_LIMIT = 49
                    log_rows_count = len(log_table_data)

                    if log_rows_count > LOG_PAGE_LIMIT and not at_report_end:
                        elems.append(PageBreak()) 

                if not at_report_end:
                    elems.append(PageBreak())
                # progress (po druhé straně batch)
                if progress_cb and total_pages_to_build:
                    pages_done += 1
                    progress_cb(min(int(pages_done * 100 / total_pages_to_build), 99))

    # -------------------------------------------------
    # 6) POJISTKA: nikdy nekončit samotným PageBreak
    # -------------------------------------------------

    while elems and isinstance(elems[-1], PageBreak):
        elems.pop()

    # -------------------------------------------------
    # 7) BUILD + FINISH
    # -------------------------------------------------
    from tempfile import gettempdir
    temp_dir  = gettempdir()

    def _safe(s):
        if not s:
            return "report"
        s = str(s)
        if "Soupiska:" in s:
            s = s.split("Soupiska:", 1)[1].strip()
        s = s.split()[0]
        return s.replace("/", "-").replace("\\", "-")

    safe_name = _safe(header_to_use)
    temp_path = os.path.join(temp_dir, f"{safe_name}_XCD.pdf")
    doc.filename = temp_path

    doc.build(elems)

    if progress_cb:
        progress_cb(100)

    # (volitelně) auto-open
    try:
        if sys.platform.startswith("win"):
            os.startfile(temp_path)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", temp_path])
        else:
            subprocess.Popen(["xdg-open", temp_path])
    except Exception as e:
        print(f"⚠️ Nelze otevřít PDF: {e}")




# ---------- Stavba jedné tabulky (jen data) ----------

def build_case_page(case_id, samples_dict, batch, degraded_samples,
                    quant_df=None, highlight_major=False,
                    slope_effect=False, KIT_ORDER=None, kit_name=None,
                    run_header="", page_number=1, total_pages=1,
                    notes_dict=None, normalized_kit=None, col_widths=None):

    IGNORE_MARKERS = {"AMEL", "Yindel", "QS1|QS2", "IQCS|IQCL"}


    # --- 1️⃣ Určení majoritních vzorků ---
    sample_majority = set()
    for sample in batch:
        if not sample or sample not in samples_dict:
            continue
        loci_data = [
            (locus, alleles)
            for locus, (alleles, _) in samples_dict[sample].items()
            if locus not in IGNORE_MARKERS and not locus.startswith("DYS")
        ]
        if not loci_data:
            continue

        total_loci = len(loci_data)
        majority_loci = 0
        for locus, alleles in loci_data:
            heights = [h for _, h in alleles if h]
            if len(heights) < 2:
                continue
            max_h = max(heights)
            dominant = [h for h in heights if h >= 0.7 * max_h]
            if 1 <= len(dominant) <= 2:
                majority_loci += 1

        if total_loci and majority_loci / total_loci >= 0.9:
            sample_majority.add(sample)

    # --- 2️⃣ Výpočet RFU maxima ---
    sample_locus_max = {s: {} for s in batch if s}
    sample_dye_max = {s: {} for s in batch if s}
    locus_dyes = []
    for locus in KIT_ORDER:
        dye_found = None
        for sample in batch:
            if sample and locus in samples_dict.get(sample, {}):
                alleles, dye = samples_dict[sample][locus]
                dye_found = dye_found or dye
                max_val = max((h for _, h in alleles if h), default=0)
                sample_locus_max[sample][locus] = max_val
                if slope_effect and sample in degraded_samples:
                    if locus not in IGNORE_MARKERS and not locus.startswith("DYS"):
                        sample_dye_max[sample][dye] = max(sample_dye_max[sample].get(dye, 0), max_val)
        locus_dyes.append(dye_found)

    # --- 3️⃣ Hlavička tabulky ---
    header_row = [normalized_kit]
    for s in batch:
        if s:
            style_head = ParagraphStyle(
                name="Head",
                fontName="CalibriItalic" if s in degraded_samples else "Calibri",
                fontSize=11,
                alignment=1
            )
            header_row.append(Paragraph(s, style_head))
        else:
            header_row.append("")
    table_data = [header_row]

    empty_style = ParagraphStyle(name="Empty", fontName="Calibri", fontSize=10, alignment=0, textColor=colors.grey)
    grey_rows = []

    # --- 4️⃣ Markerové řádky ---
    for locus in KIT_ORDER:
        row_has_data = False
        dye_locus = None
        locus_present = False
        row = []

        for col_idx, sample in enumerate(batch, start=1):
            if not sample:
                row.append("")
                continue

            if locus in samples_dict.get(sample, {}):
                locus_present = True
                alleles, dye_locus = samples_dict[sample][locus]
                if not alleles:
                    row.append(Paragraph("-", empty_style))
                    continue

                row_has_data = True
                local_max = sample_locus_max[sample].get(locus, 0)
                if slope_effect and sample in degraded_samples:
                    local_max = sample_dye_max[sample].get(dye_locus, local_max)

                bold_indices = []
                if highlight_major and sample in sample_majority and locus not in IGNORE_MARKERS:
                    heights = [h for _, h in alleles if h]
                    if heights:
                        max_h = max(heights)
                        bold_indices = [i for i, (_, h) in enumerate(alleles) if h >= 0.7 * max_h]
                        if locus.startswith("DYS") and locus != "DYS385":
                            top_index = max(range(len(alleles)), key=lambda i: alleles[i][1] or 0)
                            bold_indices = [top_index]

                sample_col_width = col_widths[col_idx]

                row.append(
                    XCD_utils.format_alleles_for_cell(
                        alleles, local_max,
                        XCD_utils.is_fu_sample(sample),
                        highlight_major=highlight_major,
                        cell_width=sample_col_width,
                        safe_width=sample_col_width,
                        bold_indices=bold_indices, 
                        allow_wrap=False,
                    )
                )
            else:
                row.append("")

        # --- barvy lokusů ---
        if locus == "rs199815934":
            style_marker = ParagraphStyle(
                name="Marker",
                fontName="Calibri",
                fontSize=9,
                leading=14,
                textColor=DYE_COLORS.get(str(dye_locus), colors.black),
                alignment=0
            )
        elif row_has_data or locus_present:
            style_marker = ParagraphStyle(
                name="Marker",
                fontName="Calibri",
                fontSize=12,
                leading=14,
                textColor=DYE_COLORS.get(str(dye_locus), colors.black),
                alignment=0
            )
        else:
            style_marker = ParagraphStyle(
                name="MarkerGrey",
                fontName="Calibri",
                fontSize=12,
                leading=14,
                textColor=colors.grey,
                alignment=0
            )

        row = [Paragraph(locus, style_marker)] + row
        table_data.append(row)
        if not locus_present:
            grey_rows.append(len(table_data) - 1)

    # --- 5️⃣ IS blok ---
    is_rows = ["IS InfoDNA", "IS CODIS", "shoda CODIS", "IS SHODA"]
    style_is = ParagraphStyle(name="IS", fontName="Calibri", fontSize=9, alignment=0)
    for label in is_rows:
        row = [Paragraph(label, style_is)]
        for _ in batch:
            row.append("")
        table_data.append(row)
    first_is_row = len(table_data) - len(is_rows)

    # --- 6️⃣ Kvantifikace ---
    quant_rows = []
    if isinstance(quant_df, pd.DataFrame) and not quant_df.empty:
        quant_rows = [("A", "koncentrace"), ("Y", "koncentrace_y"), ("DI_A", "deg_a"), ("DI_Y", "deg_y"), ("A/Y", "A/Y")]
        style_quant = ParagraphStyle(name="Quant", fontName="Calibri", fontSize=8, alignment=1)

        # --- Přepočet DI_A, DI_Y, A/Y po načtení z DB ---
        if not quant_df.empty:
            # Převod všech čísel na float kvůli jistotě
            for c in ["koncentrace", "koncentrace_y", "deg_a", "deg_y"]:
                if c in quant_df.columns:
                    quant_df[c] = pd.to_numeric(quant_df[c], errors="coerce")

            # Degradační indexy
            quant_df["DI_A"] = quant_df.apply(
                lambda x: round(x["koncentrace"] / x["deg_a"], 2)
                if pd.notna(x["koncentrace"]) and pd.notna(x["deg_a"]) and x["deg_a"] != 0
                else None,
                axis=1
            )
            quant_df["DI_Y"] = quant_df.apply(
                lambda x: round(x["koncentrace_y"] / x["deg_y"], 2)
                if pd.notna(x["koncentrace_y"]) and pd.notna(x["deg_y"]) and x["deg_y"] != 0
                else None,
                axis=1
            )

            # Poměr A/Y
            quant_df["A/Y"] = quant_df.apply(
                lambda x: round(x["koncentrace"] / x["koncentrace_y"], 2)
                if pd.notna(x["koncentrace"]) and pd.notna(x["koncentrace_y"]) and x["koncentrace_y"] != 0
                else None,
                axis=1
            )

            # Zaokrouhlení A a Y na 4 desetinná místa
            for col in ["koncentrace", "koncentrace_y"]:
                if col in quant_df.columns:
                    quant_df[col] = quant_df[col].apply(
                        lambda v: f"{v:.4f}" if isinstance(v, (float, int)) and pd.notna(v) else ""
                    )

        for label, colname in quant_rows:
            row = [Paragraph(label, style_quant)]
            for sample in batch:
                txt = "-"
                if sample and quant_df is not None and not quant_df.empty:
                    row_df = quant_df[quant_df["Sample"] == sample]
                    if not row_df.empty:
                        val = None

                        # --- Přímý výpočet DI_A a DI_Y ---
                        if label == "DI_A":
                            a = row_df.iloc[0].get("koncentrace")
                            da = row_df.iloc[0].get("deg_a")
                            try:
                                a = float(a)
                                da = float(da)
                                if da != 0:
                                    val = a / da
                            except (TypeError, ValueError):
                                val = None
                        elif label == "DI_Y":
                            y = row_df.iloc[0].get("koncentrace_y")
                            dy = row_df.iloc[0].get("deg_y")
                            try:
                                y = float(y)
                                dy = float(dy)
                                if dy != 0:
                                    val = y / dy
                            except (TypeError, ValueError):
                                val = None
                        elif colname in row_df.columns:
                            val = row_df.iloc[0][colname]

                        # --- Formátování ---
                        if pd.notna(val):
                            try:
                                val = float(val)
                                if label in ("A", "Y"):
                                    txt = f"{val:.4f} ng/µl"
                                elif label in ("DI_A", "DI_Y", "A/Y"):
                                    txt = f"{val:.2f}"
                            except (ValueError, TypeError):                               
                                txt = "-"
                        row.append(Paragraph(txt, style_quant))
                    else:
                        row.append(Paragraph("-", style_quant))
            table_data.append(row)

    first_quant_row = len(table_data) - len(quant_rows)
    last_row = len(table_data) - 1

    # --- Poznámky pod tabulkou ---

    notes_row = None
    if notes_dict:
        style_notes_label = ParagraphStyle(name="NotesLabel", fontName="Calibri", fontSize=8, alignment=1)
        style_notes = ParagraphStyle(name="Notes", fontName="Calibri", fontSize=8, alignment=1)

        row = [Paragraph("poznámky", style_notes_label)]
        for sample in batch:
            if sample:
                txt = (notes_dict.get(sample) or "").strip()
                if txt:
                    row.append(Paragraph(f"<i>{txt}</i>", style_notes))
                else:
                    row.append("")
            else:
                row.append("")
        table_data.append(row)
        notes_row = len(table_data) - 1


    # --- 7️⃣ Výšky řádků ---

    row_heights = []

    n_total = len(table_data)
    n_quant = len(quant_rows) if quant_rows else 0
    quant_start = n_total - n_quant - (1 if notes_row is not None else 0)
    quant_end = quant_start + n_quant - 1

    for i in range(n_total):

        # 1️⃣ první dva řádky (hlavičky)
        if i < 2:
            row_heights.append(ROW_HEIGHT_MARKER)
            continue

        # 2️⃣ řádky kvantifikace
        if quant_rows and quant_start <= i <= quant_end:
            row_heights.append(ROW_HEIGHT_QUANT)
            continue

        # 3️⃣ řádek poznámek (pokud existuje)
        if notes_row is not None and i == notes_row:
            row_heights.append(ROW_HEIGHT_MARKER)
            continue

        # 4️⃣ ostatní markerové / IS bloky
        row_heights.append(ROW_HEIGHT_MARKER)


    # --- 8️⃣ Vytvoření tabulky ---
    table = Table(table_data, repeatRows=2, rowHeights=row_heights, colWidths=(col_widths or COL_WIDTHS))
    base_style = [
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEAFTER", (0, 0), (0, -1), 1, colors.black),
    ]
    table.setStyle(TableStyle(base_style))

    table.setStyle(TableStyle([
        ("LINEABOVE", (0, first_is_row), (-1, first_is_row), 1, colors.black),
    ]))
    # šedé pozadí IS bloku (první sloupec)
    for i in range(first_is_row, first_is_row + len(is_rows)):
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, i), (0, i), colors.lightgrey), 
        ]))

    # šedé pozadí kvantifikace
    if quant_rows:
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, first_quant_row), (-1, last_row), colors.lightgrey),
            ("LINEABOVE", (0, first_quant_row), (-1, first_quant_row), 1, colors.black)
        ]))

    # čáry mezi barvami (dye bloky)
    splits = KIT_SPLITS.get(kit_name, [])
    for idx in splits:
        r_cur, r_next = 1 + idx, 2 + idx
        table.setStyle(TableStyle([
            ("LINEBELOW", (0, r_cur), (-1, r_cur), 1, colors.black),
            ("LINEABOVE", (0, r_next), (-1, r_next), 1, colors.black),
        ]))

    # šedé řádky pro chybějící lokusy
    for r in grey_rows:
        table.setStyle(TableStyle([("BACKGROUND", (0, r), (-1, r), colors.lightgrey)]))

    if notes_row is not None:
        table.setStyle(TableStyle([
            ("LINEABOVE", (0, notes_row), (-1, notes_row), 1, colors.black),
        ]))


    return table
