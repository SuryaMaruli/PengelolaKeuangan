import re
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account


st.set_page_config(
    page_title="Monitoring Keuangan",
    page_icon="$",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_TITLE = "Monitoring Keuangan"
TRANSAKSI_RANGE = "Transaksi!A:H"
KATEGORI_RANGE = "Kategori!A:B"
TRANSAKSI_COLUMNS = [
    "id",
    "tanggal",
    "jenis",
    "kategori",
    "keterangan",
    "jumlah",
    "dibuat_pada",
    "diubah_pada",
]
KATEGORI_COLUMNS = ["Jenis", "Kategori"]
HEADER_ALIASES = {
    "id": "id",
    "tanggal": "tanggal",
    "tgl": "tanggal",
    "date": "tanggal",
    "jenis": "jenis",
    "tipe": "jenis",
    "type": "jenis",
    "kategori": "kategori",
    "category": "kategori",
    "keterangan": "keterangan",
    "catatan": "keterangan",
    "deskripsi": "keterangan",
    "jumlah": "jumlah",
    "nominal": "jumlah",
    "amount": "jumlah",
    "dibuat_pada": "dibuat_pada",
    "created_at": "dibuat_pada",
    "diubah_pada": "diubah_pada",
    "updated_at": "diubah_pada",
}

WARNA_JENIS = {
    "Pemasukan": "#22C55E",
    "Pengeluaran": "#F97316",
    "Saldo": "#2563EB",
}
WARNA_KATEGORI = [
    "#F97316",
    "#06B6D4",
    "#8B5CF6",
    "#EC4899",
    "#EAB308",
    "#14B8A6",
    "#EF4444",
    "#3B82F6",
    "#84CC16",
    "#F43F5E",
]
SKALA_PEMASUKAN = ["#DCFCE7", "#86EFAC", "#22C55E", "#15803D"]
SKALA_PENGELUARAN = ["#FFEDD5", "#FDBA74", "#F97316", "#C2410C"]
NAMA_BULAN = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}
NAMA_BULAN_PENDEK = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "Mei",
    6: "Jun",
    7: "Jul",
    8: "Agu",
    9: "Sep",
    10: "Okt",
    11: "Nov",
    12: "Des",
}


st.markdown(
    """
    <style>
        .stApp { background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%); }
        .block-container { padding-top: 1.3rem; max-width: 1450px; }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
        [data-testid="stSidebar"] * { color: #f8fafc; }
        .hero-card {
            background: linear-gradient(135deg, #2563eb 0%, #06b6d4 55%, #22c55e 100%);
            padding: 1.45rem 1.65rem;
            border-radius: 18px;
            color: white;
            margin-bottom: 1.1rem;
            box-shadow: 0 16px 30px rgba(37, 99, 235, 0.18);
        }
        .hero-card h1 { margin: 0; color: white; font-size: 2rem; }
        .hero-card p { margin: .45rem 0 0; opacity: .94; }
        .metric-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, .06);
            min-height: 125px;
        }
        .metric-title { color: #64748b; font-size: .9rem; font-weight: 800; margin-bottom: .55rem; }
        .metric-value { color: #0f172a; font-size: 1.55rem; font-weight: 900; }
        .metric-note { color: #64748b; font-size: .82rem; margin-top: .55rem; }
        .section-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, .05);
            margin-bottom: 1rem;
        }
        .section-title { color: #0f172a; font-weight: 900; font-size: 1.12rem; margin-bottom: .2rem; }
        .section-subtitle { color: #64748b; font-size: .9rem; margin-bottom: .8rem; }
        .status-positive, .status-warning, .status-negative {
            padding: .8rem 1rem;
            border-radius: 12px;
            font-weight: 800;
            margin-bottom: .45rem;
        }
        .status-positive { background: #ecfdf5; color: #166534; border: 1px solid #bbf7d0; }
        .status-warning { background: #fff7ed; color: #9a3412; border: 1px solid #fed7aa; }
        .status-negative { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
        .sidebar-brand {
            padding: 1rem;
            border: 1px solid rgba(255,255,255,.14);
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(37,99,235,.95), rgba(6,182,212,.82));
            box-shadow: 0 14px 28px rgba(2,6,23,.24);
            margin-bottom: 1rem;
        }
        .sidebar-brand-title { font-size: 1.3rem; font-weight: 900; color: white; }
        .sidebar-brand-subtitle { font-size: .82rem; color: rgba(255,255,255,.86); margin-top: .35rem; }
        .sidebar-section-label {
            font-size: .72rem;
            font-weight: 900;
            color: #93c5fd;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin: .35rem 0 .55rem;
        }
        .sidebar-summary {
            padding: .9rem 1rem;
            border-radius: 14px;
            background: rgba(255,255,255,.08);
            border: 1px solid rgba(255,255,255,.12);
            margin-top: 1rem;
        }
        .sidebar-summary-label { font-size: .78rem; color: #cbd5e1; margin-bottom: .35rem; }
        .sidebar-summary-value { font-size: 1.15rem; font-weight: 900; color: #fff; }
        .sidebar-summary-note { font-size: .78rem; color: #bfdbfe; margin-top: .25rem; }
        [data-testid="stSidebar"] div[role="radiogroup"] { display: flex; flex-direction: column; gap: .45rem; }
        [data-testid="stSidebar"] div[role="radiogroup"] label {
            border-radius: 14px;
            padding: .72rem .85rem;
            border: 1px solid rgba(255,255,255,.10);
            background: rgba(255,255,255,.055);
            transition: all .18s ease;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: rgba(255,255,255,.11);
            border-color: rgba(125,211,252,.42);
            transform: translateX(2px);
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            background: linear-gradient(135deg, #f8fafc, #dbeafe);
            border-color: #93c5fd;
            box-shadow: 0 10px 22px rgba(15,23,42,.22);
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) * {
            color: #0f172a !important;
            font-weight: 900;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 12px;
            font-weight: 800;
            min-height: 42px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def rupiah(nilai):
    return f"Rp {nilai:,.0f}".replace(",", ".")


def format_selisih_rupiah(nilai):
    if nilai > 0:
        return f"+{rupiah(nilai)}"
    if nilai < 0:
        return f"-{rupiah(abs(nilai))}"
    return rupiah(0)


def render_header(judul, deskripsi):
    st.markdown(
        f'<div class="hero-card"><h1>{judul}</h1><p>{deskripsi}</p></div>',
        unsafe_allow_html=True,
    )


def section_header(judul, deskripsi=""):
    st.markdown(
        f'<div class="section-title">{judul}</div><div class="section-subtitle">{deskripsi}</div>',
        unsafe_allow_html=True,
    )


def metric_card(judul, nilai, catatan):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{judul}</div>
            <div class="metric-value">{nilai}</div>
            <div class="metric-note">{catatan}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def extract_spreadsheet_id(value):
    value = (value or "").strip()
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", value)
    return match.group(1) if match else value


def get_service_account_info():
    try:
        info = dict(st.secrets["gcp_service_account"])
    except Exception:
        return None

    if info.get("private_key"):
        info["private_key"] = info["private_key"].replace("\\n", "\n")
    return info


def get_spreadsheet_id(default=""):
    try:
        spreadsheet = st.secrets.get("spreadsheet", {})
        return spreadsheet.get("id", default)
    except Exception:
        return default


def create_authorized_session(service_account_info):
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return AuthorizedSession(credentials)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_values(spreadsheet_id, range_name, _session):
    url = (
        "https://sheets.googleapis.com/v4/spreadsheets/"
        f"{spreadsheet_id}/values/{quote(range_name)}"
    )
    response = _session.get(url, timeout=20)
    if not response.ok:
        raise RuntimeError(
            f"Google Sheets API error {response.status_code}: {response.text}"
        )
    return response.json().get("values", [])


def normalize_header(header):
    text = str(header).strip()
    key = re.sub(r"\s+", "_", text.lower())
    return HEADER_ALIASES.get(key, text)


def values_to_df(values, expected_headers):
    if not values:
        return pd.DataFrame(columns=expected_headers)

    headers = [normalize_header(item) for item in values[0]]
    rows = values[1:]
    width = max(len(headers), len(expected_headers))
    headers = (headers + expected_headers)[:width]
    normalized = [row + [""] * (width - len(row)) for row in rows]
    return pd.DataFrame(normalized, columns=headers)


def normalize_jenis(nilai):
    text = str(nilai).strip().lower()
    if text in ["pemasukan", "masuk", "income"]:
        return "Pemasukan"
    if text in ["pengeluaran", "keluar", "expense"]:
        return "Pengeluaran"
    return str(nilai).strip()


def normalize_jumlah(nilai):
    text = str(nilai).strip()
    text = re.sub(r"[^0-9,.-]", "", text)
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    return pd.to_numeric(text, errors="coerce")


def prepare_transaksi(df):
    for column in TRANSAKSI_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    clean = df[TRANSAKSI_COLUMNS].copy()
    clean["jenis"] = clean["jenis"].map(normalize_jenis)
    clean["kategori"] = clean["kategori"].astype(str).str.strip()
    clean["keterangan"] = clean["keterangan"].astype(str).str.strip()
    clean["tanggal"] = pd.to_datetime(clean["tanggal"], errors="coerce", dayfirst=True)
    clean["jumlah"] = clean["jumlah"].map(normalize_jumlah)
    clean["dibuat_pada"] = pd.to_datetime(clean["dibuat_pada"], errors="coerce", dayfirst=True)
    clean["diubah_pada"] = pd.to_datetime(clean["diubah_pada"], errors="coerce", dayfirst=True)
    clean = clean.dropna(subset=["tanggal", "jumlah"])
    clean = clean[clean["jenis"].isin(["Pemasukan", "Pengeluaran"])]
    clean["jumlah"] = clean["jumlah"].fillna(0)
    return clean.sort_values(["tanggal", "id"], ascending=[False, False])


def prepare_kategori(df):
    for column in KATEGORI_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    clean = df[KATEGORI_COLUMNS].copy()
    clean["Jenis"] = clean["Jenis"].map(normalize_jenis)
    clean["Kategori"] = clean["Kategori"].astype(str).str.strip()
    clean = clean[(clean["Jenis"] != "") & (clean["Kategori"] != "")]
    return clean


def load_spreadsheet(spreadsheet_id, session):
    transaksi = values_to_df(
        fetch_values(spreadsheet_id, TRANSAKSI_RANGE, session),
        TRANSAKSI_COLUMNS,
    )
    kategori = values_to_df(
        fetch_values(spreadsheet_id, KATEGORI_RANGE, session),
        KATEGORI_COLUMNS,
    )
    return prepare_transaksi(transaksi), prepare_kategori(kategori)


def append_transaksi(spreadsheet_id, session, tanggal, jenis, kategori, keterangan, jumlah):
    now = pd.Timestamp.now(tz="Asia/Jakarta").strftime("%Y-%m-%d %H:%M:%S")
    transaction_id = f"TRX-{pd.Timestamp.now(tz='Asia/Jakarta').strftime('%Y%m%d%H%M%S')}"
    row = [
        transaction_id,
        tanggal.strftime("%Y-%m-%d"),
        jenis,
        kategori,
        keterangan.strip(),
        int(jumlah),
        now,
        now,
    ]
    url = (
        "https://sheets.googleapis.com/v4/spreadsheets/"
        f"{spreadsheet_id}/values/{quote('Transaksi!A:H')}:append"
        "?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS"
    )
    response = session.post(url, json={"values": [row]}, timeout=20)
    if not response.ok:
        raise RuntimeError(
            f"Google Sheets API error {response.status_code}: {response.text}"
        )
    st.cache_data.clear()
    return transaction_id


def mark_transaction_saved(transaction_id):
    st.session_state["last_saved_transaction_id"] = transaction_id


def show_saved_transaction_message():
    transaction_id = st.session_state.pop("last_saved_transaction_id", None)
    if transaction_id:
        st.success(
            "Transaksi berhasil disimpan ke spreadsheet dan data terbaru "
            f"sudah dibaca ulang dengan ID {transaction_id}."
        )


def filter_data(df):
    if df.empty:
        return df

    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Data")
    tanggal_min = df["tanggal"].min().date()
    tanggal_max = df["tanggal"].max().date()
    rentang = st.sidebar.date_input(
        "Rentang tanggal",
        value=(tanggal_min, tanggal_max),
        min_value=tanggal_min,
        max_value=tanggal_max,
    )
    jenis_filter = st.sidebar.multiselect(
        "Jenis transaksi",
        ["Pemasukan", "Pengeluaran"],
        default=["Pemasukan", "Pengeluaran"],
    )
    kategori_list = sorted(df["kategori"].dropna().unique().tolist())
    kategori_filter = st.sidebar.multiselect(
        "Kategori",
        kategori_list,
        default=kategori_list,
    )

    filtered = df.copy()
    if isinstance(rentang, (tuple, list)) and len(rentang) == 2:
        filtered = filtered[
            (filtered["tanggal"].dt.date >= rentang[0])
            & (filtered["tanggal"].dt.date <= rentang[1])
        ]
    filtered = (
        filtered[filtered["jenis"].isin(jenis_filter)]
        if jenis_filter
        else filtered.iloc[0:0]
    )
    filtered = (
        filtered[filtered["kategori"].isin(kategori_filter)]
        if kategori_filter
        else filtered.iloc[0:0]
    )
    return filtered


def format_plotly(fig, tinggi=420):
    fig.update_layout(
        template="plotly_white",
        height=tinggi,
        margin=dict(l=20, r=20, t=65, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,.72)",
        hoverlabel=dict(bgcolor="white", bordercolor="#cbd5e1", font_size=12),
        font=dict(family="Arial", size=12, color="#334155"),
        title_font=dict(size=18, color="#0f172a"),
        legend_title_text="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)
    return fig


def show_plot(fig, tinggi=420):
    st.plotly_chart(
        format_plotly(fig, tinggi),
        use_container_width=True,
        config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
    )


def tampilkan_kartu_ringkasan(df):
    pemasukan = df.loc[df["jenis"] == "Pemasukan", "jumlah"].sum()
    pengeluaran = df.loc[df["jenis"] == "Pengeluaran", "jumlah"].sum()
    saldo = pemasukan - pengeluaran
    rasio = pengeluaran / pemasukan * 100 if pemasukan > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Total Pemasukan", rupiah(pemasukan), "Akumulasi pemasukan pada filter aktif")
    with col2:
        metric_card("Total Pengeluaran", rupiah(pengeluaran), f"{rasio:.1f}% dari pemasukan")
    with col3:
        metric_card("Saldo Bersih", rupiah(saldo), "Pemasukan dikurangi pengeluaran")
    with col4:
        metric_card("Jumlah Transaksi", str(len(df)), "Baris valid dari spreadsheet")

    if saldo < 0:
        st.markdown('<div class="status-negative">Pengeluaran lebih besar daripada pemasukan.</div>', unsafe_allow_html=True)
    elif pemasukan > 0 and rasio > 90:
        st.markdown('<div class="status-warning">Pengeluaran sudah menggunakan lebih dari 90% pemasukan.</div>', unsafe_allow_html=True)
    elif pemasukan > 0:
        st.markdown('<div class="status-positive">Kondisi arus kas positif dan masih memiliki saldo.</div>', unsafe_allow_html=True)


def grafik_bulanan(df):
    data = df.copy()
    data["bulan"] = data["tanggal"].dt.to_period("M").dt.to_timestamp()
    bulanan = (
        data.groupby(["bulan", "jenis"], as_index=False)["jumlah"]
        .sum()
        .pivot(index="bulan", columns="jenis", values="jumlah")
        .fillna(0)
        .reset_index()
        .sort_values("bulan")
    )
    for column in ["Pemasukan", "Pengeluaran"]:
        if column not in bulanan.columns:
            bulanan[column] = 0
    bulanan["Saldo"] = bulanan["Pemasukan"] - bulanan["Pengeluaran"]

    fig = go.Figure()
    for name in ["Pemasukan", "Pengeluaran", "Saldo"]:
        fig.add_trace(
            go.Scatter(
                x=bulanan["bulan"],
                y=bulanan[name],
                name=name,
                mode="lines+markers",
                line=dict(color=WARNA_JENIS[name], width=4, shape="spline"),
                marker=dict(size=10, color=WARNA_JENIS[name], line=dict(color="white", width=2)),
                hovertemplate=f"Bulan: %{{x|%b %Y}}<br>{name}: Rp %{{y:,.0f}}<extra></extra>",
            )
        )
    fig.update_layout(
        title="Tren Keuangan Bulanan",
        hovermode="x unified",
        yaxis_tickprefix="Rp ",
        yaxis_tickformat=",.0f",
    )
    fig.update_xaxes(tickformat="%b %Y", rangeslider=dict(visible=True))
    show_plot(fig, 470)


def grafik_kategori(df, jenis):
    data = (
        df[df["jenis"] == jenis]
        .groupby("kategori", as_index=False)["jumlah"]
        .sum()
        .sort_values("jumlah", ascending=True)
    )
    if data.empty:
        st.info(f"Belum ada data {jenis.lower()} pada filter aktif.")
        return
    fig = px.bar(
        data,
        x="jumlah",
        y="kategori",
        orientation="h",
        text="jumlah",
        title=f"{jenis} per Kategori",
        labels={"kategori": "", "jumlah": "Jumlah"},
        color="jumlah",
        color_continuous_scale=SKALA_PEMASUKAN if jenis == "Pemasukan" else SKALA_PENGELUARAN,
        custom_data=["kategori"],
    )
    fig.update_traces(
        texttemplate="Rp %{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{customdata[0]}</b><br>Total: Rp %{x:,.0f}<extra></extra>",
    )
    fig.update_layout(xaxis_tickprefix="Rp ", xaxis_tickformat=",.0f", coloraxis_showscale=False, showlegend=False)
    show_plot(fig)


def grafik_komposisi(df, jenis):
    data = (
        df[df["jenis"] == jenis]
        .groupby("kategori", as_index=False)["jumlah"]
        .sum()
        .sort_values("jumlah", ascending=False)
    )
    if data.empty:
        st.info(f"Belum ada data {jenis.lower()} untuk grafik komposisi.")
        return
    fig = px.pie(
        data,
        names="kategori",
        values="jumlah",
        hole=.58,
        title=f"Komposisi {jenis}",
        color_discrete_sequence=WARNA_KATEGORI,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        marker=dict(line=dict(color="white", width=2)),
        hovertemplate="<b>%{label}</b><br>Jumlah: Rp %{value:,.0f}<br>Porsi: %{percent}<extra></extra>",
    )
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-.24, xanchor="center", x=.5))
    show_plot(fig)


def grafik_pengeluaran_harian(df):
    pengeluaran = df[df["jenis"] == "Pengeluaran"].copy()
    if pengeluaran.empty:
        st.info("Belum ada data pengeluaran harian.")
        return
    pengeluaran["bulan"] = pengeluaran["tanggal"].dt.to_period("M")
    bulan = st.selectbox(
        "Pilih bulan pengeluaran harian",
        sorted(pengeluaran["bulan"].dropna().unique(), reverse=True),
        format_func=lambda item: f"{NAMA_BULAN[item.month]} {item.year}",
    )
    pengeluaran = pengeluaran[pengeluaran["bulan"] == bulan]
    harian = (
        pengeluaran.groupby(pengeluaran["tanggal"].dt.date)["jumlah"]
        .sum()
        .reset_index()
        .rename(columns={"tanggal": "Tanggal", "jumlah": "Pengeluaran"})
    )
    harian["Tanggal"] = pd.to_datetime(harian["Tanggal"])
    harian = harian.sort_values("Tanggal")
    harian["Rata-rata 7 Hari"] = harian["Pengeluaran"].rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=harian["Tanggal"],
            y=harian["Pengeluaran"],
            name="Pengeluaran Harian",
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color=WARNA_JENIS["Pengeluaran"], width=3, shape="spline"),
            marker=dict(size=8, color=WARNA_JENIS["Pengeluaran"], line=dict(color="white", width=2)),
            hovertemplate="Tanggal: %{x|%d-%m-%Y}<br>Pengeluaran: Rp %{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=harian["Tanggal"],
            y=harian["Rata-rata 7 Hari"],
            name="Rata-rata 7 Hari",
            mode="lines",
            line=dict(color="#8B5CF6", width=3, dash="dot", shape="spline"),
            hovertemplate="Tanggal: %{x|%d-%m-%Y}<br>Rata-rata: Rp %{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=f"Pengeluaran Harian - {NAMA_BULAN[bulan.month]} {bulan.year}",
        hovermode="x unified",
        yaxis_tickprefix="Rp ",
        yaxis_tickformat=",.0f",
    )
    fig.update_xaxes(tickformat="%d %b", rangeslider=dict(visible=True))
    show_plot(fig, 450)


def grafik_pengeluaran_harian_semua_bulan(df):
    pengeluaran = df[df["jenis"] == "Pengeluaran"].copy()
    if pengeluaran.empty:
        return
    pengeluaran["Hari"] = pengeluaran["tanggal"].dt.day
    pengeluaran["Bulan"] = pengeluaran["tanggal"].dt.to_period("M").dt.to_timestamp()
    pengeluaran["Label Bulan"] = pengeluaran["Bulan"].map(lambda item: f"{NAMA_BULAN_PENDEK[item.month]} {item.year}")
    data = (
        pengeluaran.groupby(["Bulan", "Label Bulan", "Hari"], as_index=False)["jumlah"]
        .sum()
        .sort_values(["Bulan", "Hari"])
        .rename(columns={"jumlah": "Pengeluaran"})
    )
    fig = px.line(
        data,
        x="Hari",
        y="Pengeluaran",
        color="Label Bulan",
        markers=True,
        title="Pengeluaran Harian di Setiap Bulan",
        labels={"Hari": "Tanggal", "Pengeluaran": "Pengeluaran", "Label Bulan": "Bulan"},
        color_discrete_sequence=WARNA_KATEGORI,
        custom_data=["Label Bulan"],
    )
    fig.update_traces(
        line=dict(width=3, shape="spline"),
        marker=dict(size=7, line=dict(color="white", width=1)),
        hovertemplate="Bulan: %{customdata[0]}<br>Tanggal: %{x}<br>Pengeluaran: Rp %{y:,.0f}<extra></extra>",
    )
    fig.update_layout(hovermode="x unified", yaxis_tickprefix="Rp ", yaxis_tickformat=",.0f")
    fig.update_xaxes(dtick=1, range=[1, 31])
    show_plot(fig, 480)


def rekap_bulanan(df):
    if df.empty:
        return pd.DataFrame()
    data = df.copy()
    data["Bulan"] = data["tanggal"].dt.to_period("M").astype(str)
    rekap = (
        data.groupby(["Bulan", "jenis"], as_index=False)["jumlah"]
        .sum()
        .pivot(index="Bulan", columns="jenis", values="jumlah")
        .fillna(0)
        .reset_index()
    )
    for column in ["Pemasukan", "Pengeluaran"]:
        if column not in rekap.columns:
            rekap[column] = 0
    rekap = rekap.sort_values("Bulan")
    rekap["Saldo"] = rekap["Pemasukan"] - rekap["Pengeluaran"]
    rekap["Rasio Pengeluaran (%)"] = rekap.apply(
        lambda row: row["Pengeluaran"] / row["Pemasukan"] * 100
        if row["Pemasukan"] > 0
        else 0,
        axis=1,
    )
    rekap["Perubahan Pemasukan"] = rekap["Pemasukan"].diff().fillna(0)
    rekap["Perubahan Pengeluaran"] = rekap["Pengeluaran"].diff().fillna(0)

    def status(nilai):
        if nilai > 0:
            return "Lebih tinggi dari bulan sebelumnya"
        if nilai < 0:
            return "Lebih rendah dari bulan sebelumnya"
        return "Sama dengan bulan sebelumnya"

    rekap["Status Pemasukan"] = rekap["Perubahan Pemasukan"].map(status)
    rekap["Status Pengeluaran"] = rekap["Perubahan Pengeluaran"].map(status)
    if len(rekap) == 1:
        rekap.loc[rekap.index[0], "Status Pemasukan"] = "Belum ada bulan pembanding"
        rekap.loc[rekap.index[0], "Status Pengeluaran"] = "Belum ada bulan pembanding"
    return rekap.sort_values("Bulan", ascending=False)


def format_tabel_rekap(rekap):
    hasil = rekap.copy()
    for column in ["Pemasukan", "Pengeluaran", "Saldo"]:
        hasil[column] = hasil[column].map(rupiah)
    for column in ["Perubahan Pemasukan", "Perubahan Pengeluaran"]:
        hasil[column] = hasil[column].map(format_selisih_rupiah)
    hasil["Rasio Pengeluaran (%)"] = hasil["Rasio Pengeluaran (%)"].map(lambda item: f"{item:.1f}%")
    return hasil


def pesan_perubahan_bulanan(rekap):
    if rekap.empty:
        return
    urut = rekap.sort_values("Bulan")
    if len(urut) < 2:
        st.info("Belum ada bulan pembanding untuk melihat perubahan pemasukan dan pengeluaran.")
        return
    now, prev = urut.iloc[-1], urut.iloc[-2]
    bulan_ini, bulan_lalu = now["Bulan"], prev["Bulan"]
    delta_pemasukan = now["Perubahan Pemasukan"]
    delta_pengeluaran = now["Perubahan Pengeluaran"]
    if delta_pemasukan > 0:
        st.success(f"Pemasukan {bulan_ini} lebih tinggi {format_selisih_rupiah(delta_pemasukan)} dibanding {bulan_lalu}.")
    elif delta_pemasukan < 0:
        st.warning(f"Pemasukan {bulan_ini} lebih rendah {format_selisih_rupiah(delta_pemasukan)} dibanding {bulan_lalu}.")
    else:
        st.info(f"Pemasukan {bulan_ini} sama dengan {bulan_lalu}.")
    if delta_pengeluaran > 0:
        st.warning(f"Pengeluaran {bulan_ini} lebih tinggi {format_selisih_rupiah(delta_pengeluaran)} dibanding {bulan_lalu}.")
    elif delta_pengeluaran < 0:
        st.success(f"Pengeluaran {bulan_ini} lebih rendah {format_selisih_rupiah(delta_pengeluaran)} dibanding {bulan_lalu}.")
    else:
        st.info(f"Pengeluaran {bulan_ini} sama dengan {bulan_lalu}.")


def show_setup_help():
    render_header(APP_TITLE, "Hubungkan dashboard dengan Google Spreadsheet melalui Service Account.")
    st.info("Aplikasi membaca Google Spreadsheet memakai Service Account dari Streamlit Secrets.")
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Format Spreadsheet</div>
            <div class="section-subtitle">Pastikan spreadsheet sudah dibagikan ke email service account pada field client_email.</div>
            <b>Sheet Transaksi</b>
            <p>id, tanggal, jenis, kategori, keterangan, jumlah, dibuat_pada, diubah_pada</p>
            <b>Sheet Kategori</b>
            <p>Jenis, Kategori</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">Monitoring Keuangan</div>
            <div class="sidebar-brand-subtitle">Data langsung dari Google Spreadsheet.</div>
        </div>
        <div class="sidebar-section-label">Koneksi Spreadsheet</div>
        """,
        unsafe_allow_html=True,
    )
    service_account_info = get_service_account_info()
    default_sheet_id = get_spreadsheet_id("")
    sheet_input = st.text_input("Spreadsheet ID atau URL", value=default_sheet_id)
    spreadsheet_id = extract_spreadsheet_id(sheet_input)
    if service_account_info:
        st.success("Service account terdeteksi dari Secrets.")
        st.caption(f"Email service account: {service_account_info.get('client_email', '-')}")
    else:
        st.warning("Secrets gcp_service_account belum ditemukan.")
    st.caption(f"Judul spreadsheet: {APP_TITLE}")
    if st.button("Muat ulang data", use_container_width=True):
        st.cache_data.clear()

    menu = st.radio(
        "Menu",
        ["Dashboard", "Tambah Transaksi", "Data Transaksi", "Kategori", "Panduan"],
        format_func=lambda item: {
            "Dashboard": "Dashboard  |  Visualisasi",
            "Tambah Transaksi": "Input Data  |  Simpan ke sheet",
            "Data Transaksi": "Transaksi  |  Tabel data",
            "Kategori": "Kategori  |  Referensi",
            "Panduan": "Panduan  |  Setup",
        }[item],
        label_visibility="collapsed",
    )


if not service_account_info or not spreadsheet_id:
    show_setup_help()
    st.stop()

try:
    with st.spinner("Mengambil data dari Google Spreadsheet..."):
        session = create_authorized_session(service_account_info)
        df_semua, df_kategori = load_spreadsheet(spreadsheet_id, session)
except Exception as exc:
    render_header(APP_TITLE, "Data belum bisa dimuat dari Google Spreadsheet.")
    st.error(f"Gagal membaca spreadsheet: {exc}")
    st.info("Periksa Secrets gcp_service_account, spreadsheet.id, nama sheet, dan pastikan spreadsheet sudah di-share ke client_email service account sebagai Editor.")
    st.stop()

with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-summary">
            <div class="sidebar-summary-label">Transaksi valid terbaca</div>
            <div class="sidebar-summary-value">{len(df_semua)}</div>
            <div class="sidebar-summary-note">{len(df_kategori)} kategori referensi</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if df_semua.empty and menu not in ["Panduan", "Tambah Transaksi", "Kategori"]:
    render_header(APP_TITLE, "Spreadsheet sudah terhubung, tetapi belum ada transaksi valid.")
    st.warning("Sheet Kategori sudah terbaca, tetapi sheet Transaksi belum memiliki baris yang valid.")
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Cek Sheet Transaksi</div>
            <div class="section-subtitle">Header boleh huruf besar/kecil, tetapi isi data wajib valid.</div>
            <p><b>jenis</b> harus berisi Pemasukan atau Pengeluaran.</p>
            <p><b>tanggal</b> bisa memakai format 26/07/2026, 26-07-2026, atau 2026-07-26.</p>
            <p><b>jumlah</b> harus angka, misalnya 50000 atau Rp 50.000.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    contoh = pd.DataFrame(
        [
            {
                "id": "1",
                "tanggal": "26/07/2026",
                "jenis": "Pengeluaran",
                "kategori": "Makan / Jajan",
                "keterangan": "Makan siang",
                "jumlah": "25000",
                "dibuat_pada": "26/07/2026",
                "diubah_pada": "26/07/2026",
            }
        ]
    )
    st.caption("Contoh baris yang valid untuk sheet Transaksi")
    st.dataframe(contoh, use_container_width=True, hide_index=True)
    st.caption("Kategori yang berhasil terbaca")
    st.dataframe(df_kategori, use_container_width=True, hide_index=True)
    st.stop()

if menu == "Tambah Transaksi":
    render_header("Tambah Transaksi", "Input transaksi dari Streamlit dan simpan otomatis ke sheet Transaksi.")
    show_saved_transaction_message()
    if df_kategori.empty:
        st.warning("Sheet Kategori masih kosong. Isi dulu kategori agar dropdown dapat digunakan.")
    else:
        jenis = st.radio("Jenis transaksi", ["Pengeluaran", "Pemasukan"], horizontal=True)
        opsi_kategori = sorted(
            df_kategori.loc[df_kategori["Jenis"] == jenis, "Kategori"]
            .dropna()
            .unique()
            .tolist()
        )
        if not opsi_kategori:
            st.warning(f"Belum ada kategori untuk jenis {jenis} di sheet Kategori.")
        else:
            with st.form("form_tambah_transaksi", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    tanggal = st.date_input("Tanggal transaksi")
                    kategori = st.selectbox("Kategori", opsi_kategori)
                with col2:
                    jumlah = st.number_input("Jumlah", min_value=1_000, step=1_000, format="%d")
                    keterangan = st.text_input("Keterangan", placeholder="Contoh: makan siang")
                simpan = st.form_submit_button("Simpan ke Spreadsheet", type="primary", use_container_width=True)

            if simpan:
                try:
                    transaction_id = append_transaksi(
                        spreadsheet_id,
                        session,
                        tanggal,
                        jenis,
                        kategori,
                        keterangan,
                        jumlah,
                    )
                    mark_transaction_saved(transaction_id)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Gagal menyimpan transaksi: {exc}")

elif menu == "Dashboard":
    render_header(APP_TITLE, "Pantau transaksi dari Google Spreadsheet dalam visualisasi interaktif.")
    df_filter = filter_data(df_semua)
    if df_filter.empty:
        st.warning("Tidak ada transaksi yang sesuai dengan filter.")
    else:
        tampilkan_kartu_ringkasan(df_filter)
        st.write("")
        section_header("Visualisasi Interaktif", "Grafik dapat di-hover, zoom, dan difilter lewat sidebar.")
        tab_tren, tab_pengeluaran, tab_pemasukan = st.tabs(["Tren Keuangan", "Pengeluaran", "Pemasukan"])
        with tab_tren:
            grafik_bulanan(df_filter)
            grafik_pengeluaran_harian(df_filter)
            grafik_pengeluaran_harian_semua_bulan(df_filter)
        with tab_pengeluaran:
            col1, col2 = st.columns([1.15, 1])
            with col1:
                grafik_kategori(df_filter, "Pengeluaran")
            with col2:
                grafik_komposisi(df_filter, "Pengeluaran")
        with tab_pemasukan:
            col1, col2 = st.columns([1.15, 1])
            with col1:
                grafik_kategori(df_filter, "Pemasukan")
            with col2:
                grafik_komposisi(df_filter, "Pemasukan")

        st.write("")
        section_header("Rekap Bulanan", "Ringkasan pemasukan dan pengeluaran tiap bulan.")
        rekap = rekap_bulanan(df_filter)
        pesan_perubahan_bulanan(rekap)
        st.dataframe(format_tabel_rekap(rekap), use_container_width=True, hide_index=True)
        st.download_button(
            "Unduh Rekap Bulanan",
            data=rekap.to_csv(index=False).encode("utf-8-sig"),
            file_name="rekap_keuangan_bulanan.csv",
            mime="text/csv",
            use_container_width=True,
        )

elif menu == "Data Transaksi":
    render_header("Data Transaksi", "Tabel ini dibaca langsung dari sheet Transaksi.")
    tampil = df_semua.copy()
    tampil["tanggal"] = tampil["tanggal"].dt.strftime("%d-%m-%Y")
    tampil["jumlah"] = tampil["jumlah"].map(rupiah)
    st.dataframe(tampil, use_container_width=True, hide_index=True)
    st.download_button(
        "Unduh Data Transaksi",
        data=df_semua.to_csv(index=False).encode("utf-8-sig"),
        file_name="transaksi_spreadsheet.csv",
        mime="text/csv",
        use_container_width=True,
    )

elif menu == "Kategori":
    render_header("Kategori", "Daftar kategori dibaca dari sheet Kategori.")
    st.dataframe(df_kategori, use_container_width=True, hide_index=True)
    if not df_kategori.empty:
        fig = px.treemap(
            df_kategori,
            path=["Jenis", "Kategori"],
            title="Struktur Kategori Spreadsheet",
            color="Jenis",
            color_discrete_map={"Pemasukan": "#22C55E", "Pengeluaran": "#F97316"},
        )
        show_plot(fig, 480)

else:
    show_setup_help()
