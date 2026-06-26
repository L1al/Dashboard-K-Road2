import datetime

import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────
SHEET_ID = "1D8CvGijiw15Gw83UZb1ZeurMM6EoLHUeel-drcLVR7U"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Interval auto-refresh (ms) & TTL cache (detik)
AUTOREFRESH_INTERVAL_MS = 60000
CACHE_TTL_SECONDS = 60

# Palet warna tema profesional
PAGE_BG = "#F3F5F7"
SURFACE = "#FFFFFF"
TEAL = "#0E7C72"
TEAL_DARK = "#0B5C54"
INK = "#1F2937"
MUTED = "#6B7280"
BORDER = "#E5E8EB"

# Warna semantik berdasarkan contoh gambar mockup baru
COLOR_TOTAL = "#3B82F6"       # Biru penuh untuk total laporan masuk
COLOR_VERIFIKASI = "#FBBF24"  # Kuning penuh untuk proses verifikasi
COLOR_SELESAI = "#10B981"     # Hijau penuh untuk selesai penanganan
COLOR_PARAH = "#EF4444"       # Merah untuk rusak parah

# ─────────────────────────────────────────────
# KONEKSI KE GOOGLE SHEETS
# ─────────────────────────────────────────────
@st.cache_resource
def get_client():
    """Buat koneksi ke Google Sheets (di-cache agar tidak reconnect tiap render)."""
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def load_sheet(worksheet_index: int = 0) -> pd.DataFrame:
    """Ambil data dari worksheet dan kembalikan sebagai DataFrame."""
    client = get_client()
    spreadsheet = client.open_by_url(SHEET_URL)
    worksheet = spreadsheet.get_worksheet(worksheet_index)
    records = worksheet.get_all_records()
    return pd.DataFrame(records)


def write_row(new_data: dict):
    """Tulis satu baris baru ke sheet."""
    client = get_client()
    spreadsheet = client.open_by_url(SHEET_URL)
    worksheet = spreadsheet.get_worksheet(0)
    worksheet.append_row(list(new_data.values()))
    load_sheet.clear()


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────
def normalize_status(s: str) -> str:
    s = str(s).strip().lower()
    if s in ("selesai", "done", "complete"):
        return "Selesai"
    if s in ("verifikasi", "verify"):
        return "Verifikasi"
    if s in ("proses", "diproses", "process", "in progress"):
        return "Proses"
    return s.title() if s else "Tidak Diketahui"


def normalize_kerusakan(s: str) -> str:
    s = str(s).strip().lower()
    if "ringan" in s:
        return "Rusak Ringan"
    if "sedang" in s:
        return "Rusak Sedang"
    if "parah" in s or "berat" in s:
        return "Rusak Parah"
    return s.title() if s else "Tidak Diketahui"


# ─────────────────────────────────────────────
# UI STREAMLIT
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Analisis Jalan Rusak",
    page_icon="📊",
    layout="wide",
)

# Auto-refresh halaman setiap N detik
st_autorefresh(interval=AUTOREFRESH_INTERVAL_MS, key="datarefresh")

# CSS kustom terintegrasi (gaya aplikasi mobile modern)
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"], .main {{
        background-color: {PAGE_BG} !important;
        color: {INK};
        font-family: 'Inter', sans-serif;
    }}
    [data-testid="stHeader"] {{
        background-color: transparent;
    }}
    [data-testid="stSidebar"] {{
        background-color: {SURFACE};
    }}

    /* Header bergaya aplikasi mobile kustom */
    .header-bar {{
        background-color: {TEAL};
        color: white;
        padding: 16px;
        border-radius: 12px 12px 0 0;
        font-size: 18px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    .stat-row {{
        display: flex;
        flex-direction: row;
        gap: 10px;
        margin-bottom: 12px;
    }}

    /* Kartu statistik dengan header warna blok penuh */
    .stat-card {{
        flex: 1;
        background-color: {SURFACE};
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        overflow: hidden;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }}

    .stat-card .label {{
        color: white;
        font-size: 11px;
        font-weight: 600;
        padding: 6px 4px;
        line-height: 1.2;
        min-height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .stat-card .value {{
        font-size: 22px;
        font-weight: 700;
        color: #111827;
        padding: 8px 4px;
        line-height: 1;
    }}

    .section-title {{
        font-weight: 700;
        font-size: 14px;
        color: #111827;
        margin-bottom: 8px;
    }}

    /* Container kartu pie & bar — pakai st.container(key=...) -> class .st-key-xxx */
    .st-key-pie_card, .st-key-bar_card {{
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}
    .st-key-pie_card {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
    }}
    .st-key-bar_card {{
        background-color: {TEAL};
        color: white;
    }}
    .st-key-bar_card .section-title {{
        color: white;
    }}

    /* Tombol refresh bergaya kapsul / capsule modern */
    .stButton button {{
        background: linear-gradient(135deg, #0E7C72 0%, #0B5C54 100%);
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 8px 20px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        box-shadow: 0 4px 10px rgba(14, 124, 114, 0.2) !important;
        transition: all 0.2s ease-in-out !important;
        width: auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 10px auto 0 auto !important;
    }}

    .stButton button:hover {{
        background: linear-gradient(135deg, #0B5C54 0%, #083F3A 100%) !important;
        box-shadow: 0 6px 14px rgba(14, 124, 114, 0.3) !important;
        transform: translateY(-1px);
    }}

    .stButton button:active {{
        transform: translateY(1px);
        box-shadow: 0 2px 6px rgba(14, 124, 114, 0.2) !important;
    }}

    /* Hilangkan sela padding kolom native streamlit */
    [data-testid="column"] {{
        padding: 0px !important;
    }}

    [data-testid="stCaptionContainer"] {{
        color: {MUTED};
    }}
    [data-testid="stExpander"] {{
        background-color: {SURFACE};
        border-radius: 10px;
        border: 1px solid {BORDER};
    }}
    hr {{
        border-color: {BORDER};
    }}

    /* Reduksi ukuran khusus desktop agar tidak perlu banyak scroll */
    @media (min-width: 768px) {{
        .main .block-container {{
            max-width: 1100px;
            padding-top: 1rem !important;
        }}
        .stat-card .value {{
            font-size: 24px;
        }}
    }}

    /* Responsif mobile (TIDAK DIUBAH) */
    @media (max-width: 640px) {{
        .main .block-container {{
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            padding-top: 0.5rem !important;
        }}
        .stat-card .value {{
            font-size: 20px !important;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Render navigasi atas bergaya aplikasi mobile
st.markdown(
    """
    <div class="header-bar">
        <span class="back-icon">←</span>
        <span>Dashboard Analisis</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── LOAD DATA DARI GOOGLE SHEETS ───────────────────
try:
    df = load_sheet(worksheet_index=0)

    if df.empty:
        st.warning("Sheet kosong atau tidak ada data.")
    else:
        # Normalisasi data kolom utama
        if "Status" in df.columns:
            df["Status_norm"] = df["Status"].apply(normalize_status)
        else:
            df["Status_norm"] = "Tidak Diketahui"

        if "Tingkat_Kerusakan" in df.columns:
            df["Kerusakan_norm"] = df["Tingkat_Kerusakan"].apply(normalize_kerusakan)
        else:
            df["Kerusakan_norm"] = "Tidak Diketahui"

        # Hitung kalkulasi angka metrik
        total_laporan = len(df)
        proses_verifikasi = (df["Status_norm"] == "Verifikasi").sum() + (df["Status_norm"] == "Proses").sum()
        selesai_penanganan = (df["Status_norm"] == "Selesai").sum()

        # ── 1. Kartu Statistik Atas (Model Blok Warna Penuh) ──
        st.markdown(
            f"""
            <div class="stat-row">
                <div class="stat-card">
                    <div class="label" style="background-color: {COLOR_TOTAL};">Total Laporan<br>Masuk</div>
                    <div class="value">{total_laporan:,}</div>
                </div>
                <div class="stat-card">
                    <div class="label" style="background-color: {COLOR_VERIFIKASI};">Proses<br>Verifikasi</div>
                    <div class="value">{proses_verifikasi:,}</div>
                </div>
                <div class="stat-card">
                    <div class="label" style="background-color: {COLOR_SELESAI};">Selesai<br>Penanganan</div>
                    <div class="value">{selesai_penanganan:,}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_pie, col_bar = st.columns(2)

        # ── 2. Pie Chart: Tingkat Kerusakan Jalan ──
        with col_pie:
            with st.container(key="pie_card"):
                st.markdown('<div class="section-title">Tingkat Kerusakan Jalan (Pie Chart)</div>', unsafe_allow_html=True)

                kerusakan_counts = (
                    df["Kerusakan_norm"].value_counts().reindex(
                        ["Rusak Ringan", "Rusak Sedang", "Rusak Parah"]
                    ).fillna(0).astype(int)
                )

                other = df["Kerusakan_norm"][
                    ~df["Kerusakan_norm"].isin(["Rusak Ringan", "Rusak Sedang", "Rusak Parah"])
                ].value_counts()
                for k, v in other.items():
                    kerusakan_counts[k] = v

                pie_df = kerusakan_counts.reset_index()
                pie_df.columns = ["Kategori", "Jumlah"]
                pie_df = pie_df[pie_df["Jumlah"] > 0]

                color_map = {
                    "Rusak Ringan": COLOR_SELESAI,
                    "Rusak Sedang": COLOR_VERIFIKASI,
                    "Rusak Parah": COLOR_PARAH,
                }

                if pie_df["Jumlah"].sum() > 0:
                    fig_pie = px.pie(
                        pie_df,
                        names="Kategori",
                        values="Jumlah",
                        color="Kategori",
                        color_discrete_map=color_map,
                        hole=0.0,
                    )
                    fig_pie.update_traces(
                        textinfo="percent",  # Tampilkan persentase di dalam slice agar tetap kebaca
                        textposition="inside",
                        textfont=dict(color="white", size=12, family="Inter"),
                        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
                        marker=dict(line=dict(color=SURFACE, width=2)),
                    )
                    fig_pie.update_layout(
                        margin=dict(t=10, b=50, l=10, r=10),
                        height=260,
                        paper_bgcolor=SURFACE,
                        plot_bgcolor=SURFACE,
                        font_color=INK,
                        font_family="Inter",
                        showlegend=True,
                        legend=dict(
                            orientation="h",   # legend horizontal di bawah, biar tidak terpotong di mobile
                            yanchor="top",
                            y=-0.12,
                            xanchor="center",
                            x=0.5,
                            title=None,
                            font=dict(size=11, color=INK),
                        ),
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Belum ada data tingkat kerusakan.")

        # ── 3. Bar Chart: Sebaran Kecamatan Jalan Rusak ──
        with col_bar:
            with st.container(key="bar_card"):
                st.markdown('<div class="section-title">Sebaran Lokasi Jalan Rusak (Bar Chart)</div>', unsafe_allow_html=True)

                if "Kecamatan" in df.columns:
                    kecamatan_series = df["Kecamatan"].astype(str).str.strip()
                    kecamatan_series = kecamatan_series[
                        ~kecamatan_series.isin(["", "Tidak diketahui", "Tidak Diketahui", "nan"])
                    ]
                    kecamatan_counts = kecamatan_series.value_counts().head(5).sort_values(ascending=True)

                    if len(kecamatan_counts) > 0:
                        bar_df = kecamatan_counts.reset_index()
                        bar_df.columns = ["Kecamatan", "Jumlah"]

                        fig_bar = px.bar(
                            bar_df,
                            x="Jumlah",
                            y="Kecamatan",
                            orientation="h",
                            text="Jumlah",
                        )
                        fig_bar.update_traces(
                            marker_color="white",
                            marker_line_width=0,
                            textposition="outside",
                            textfont_color="white",
                            cliponaxis=False
                        )
                        fig_bar.update_layout(
                            plot_bgcolor=TEAL,
                            paper_bgcolor=TEAL,
                            font_color="white",
                            font_family="Inter",
                            margin=dict(t=10, b=10, l=10, r=40),
                            height=260,
                            bargap=0.35,
                            xaxis=dict(showgrid=False, visible=False, range=[0, bar_df["Jumlah"].max() * 1.2]),
                            yaxis=dict(
                                showgrid=False,
                                title=None,
                                tickfont=dict(color="white", size=12, family="Inter")  # Memaksa warna teks menjadi putih terang
                            ),
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                    else:
                        st.info("Belum ada data kecamatan yang valid.")
                else:
                    st.info("Kolom 'Kecamatan' tidak ditemukan di sheet.")

except Exception as e:
    st.error(f"❌ Gagal terhubung ke Google Sheets: {e}")

# Informasi metadata berkas
st.caption(f"Sheet ID: {SHEET_ID} · Terakhir dimuat: {datetime.datetime.now().strftime('%H:%M:%S')}")
st.write("")

# ── 4. Tombol Aksi Manual ──
if st.button("🔄 Refresh Sekarang"):
    load_sheet.clear()
    st.rerun()

st.divider()
