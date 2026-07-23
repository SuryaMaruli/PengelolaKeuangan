import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="KeuanganKu", page_icon="$", layout="wide", initial_sidebar_state="expanded")
DB_PATH = Path(__file__).with_name("keuangan.db")

KATEGORI = {
    "Pengeluaran": ["Makan/Jajan", "Barang", "Biaya Wajib", "Biaya Tak Terduga", "Pekerjaan", "Kebutuhan Sehari-hari"],
    "Pemasukan": ["Gaji", "Sampingan (Joki)", "Translok"],
}
WARNA_JENIS = {"Pemasukan": "#22C55E", "Pengeluaran": "#F97316", "Saldo": "#2563EB"}
WARNA_KATEGORI = ["#F97316", "#06B6D4", "#8B5CF6", "#EC4899", "#EAB308", "#14B8A6", "#EF4444", "#3B82F6", "#84CC16", "#F43F5E"]
SKALA_PEMASUKAN = ["#DCFCE7", "#86EFAC", "#22C55E", "#15803D"]
SKALA_PENGELUARAN = ["#FFEDD5", "#FDBA74", "#F97316", "#C2410C"]
NAMA_BULAN = {1:"Januari",2:"Februari",3:"Maret",4:"April",5:"Mei",6:"Juni",7:"Juli",8:"Agustus",9:"September",10:"Oktober",11:"November",12:"Desember"}
NAMA_BULAN_PENDEK = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",7:"Jul",8:"Agu",9:"Sep",10:"Okt",11:"Nov",12:"Des"}

st.markdown("""
<style>
.stApp {background: linear-gradient(180deg,#f8fafc 0%,#eef2f7 100%)}
.block-container {padding-top:1.4rem; max-width:1450px}
[data-testid="stSidebar"] {background: linear-gradient(180deg,#0f172a 0%,#1e293b 100%)}
[data-testid="stSidebar"] * {color:#f8fafc}
.hero-card {background: linear-gradient(135deg,#2563eb 0%,#06b6d4 55%,#22c55e 100%); padding:1.5rem 1.7rem; border-radius:18px; color:white; margin-bottom:1.2rem; box-shadow:0 16px 30px rgba(37,99,235,.18)}
.hero-card h1 {margin:0; color:white; font-size:2rem}.hero-card p{margin:.45rem 0 0 0; opacity:.94}
.metric-card {background:white; border:1px solid #e2e8f0; border-radius:14px; padding:1rem 1.1rem; box-shadow:0 8px 24px rgba(15,23,42,.06); min-height:125px}
.metric-title{color:#64748b; font-size:.9rem; font-weight:700; margin-bottom:.55rem}.metric-value{color:#0f172a; font-size:1.55rem; font-weight:800}.metric-note{color:#64748b; font-size:.82rem; margin-top:.55rem}
.section-card{background:white; border:1px solid #e2e8f0; border-radius:14px; padding:1rem 1.1rem; box-shadow:0 8px 24px rgba(15,23,42,.05)}
.section-title{color:#0f172a; font-weight:800; font-size:1.12rem; margin-bottom:.2rem}.section-subtitle{color:#64748b; font-size:.9rem; margin-bottom:.8rem}
.status-positive,.status-warning,.status-negative{padding:.8rem 1rem; border-radius:12px; font-weight:700; margin-bottom:.4rem}.status-positive{background:#ecfdf5;color:#166534;border:1px solid #bbf7d0}.status-warning{background:#fff7ed;color:#9a3412;border:1px solid #fed7aa}.status-negative{background:#fef2f2;color:#991b1b;border:1px solid #fecaca}
div[data-testid="stForm"]{background:white; padding:1.2rem; border-radius:14px; border:1px solid #e2e8f0; box-shadow:0 8px 24px rgba(15,23,42,.05)}
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{border-radius:12px; font-weight:700; min-height:44px}
.sidebar-brand{padding:1rem 1rem .9rem 1rem; border:1px solid rgba(255,255,255,.14); border-radius:16px; background:linear-gradient(135deg,rgba(37,99,235,.95),rgba(6,182,212,.82)); box-shadow:0 14px 28px rgba(2,6,23,.24); margin-bottom:1rem}
.sidebar-brand-title{font-size:1.35rem; font-weight:900; letter-spacing:.02em; color:white; line-height:1.15}
.sidebar-brand-subtitle{font-size:.82rem; color:rgba(255,255,255,.86); margin-top:.35rem}
.sidebar-section-label{font-size:.72rem; font-weight:800; color:#93c5fd; letter-spacing:.08em; text-transform:uppercase; margin:.35rem 0 .55rem}
.sidebar-summary{padding:.9rem 1rem; border-radius:14px; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.12); margin-top:1rem}
.sidebar-summary-label{font-size:.78rem; color:#cbd5e1; margin-bottom:.35rem}.sidebar-summary-value{font-size:1.2rem; font-weight:900; color:#fff}.sidebar-summary-note{font-size:.78rem; color:#bfdbfe; margin-top:.25rem}
[data-testid="stSidebar"] div[role="radiogroup"]{display:flex; flex-direction:column; gap:.45rem}
[data-testid="stSidebar"] div[role="radiogroup"] label{border-radius:14px; padding:.72rem .85rem; border:1px solid rgba(255,255,255,.10); background:rgba(255,255,255,.055); transition:all .18s ease; box-shadow:inset 0 1px 0 rgba(255,255,255,.06)}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:rgba(255,255,255,.11); border-color:rgba(125,211,252,.42); transform:translateX(2px)}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){background:linear-gradient(135deg,#f8fafc,#dbeafe); border-color:#93c5fd; box-shadow:0 10px 22px rgba(15,23,42,.22)}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) *{color:#0f172a!important; font-weight:900}
[data-testid="stSidebar"] div[role="radiogroup"] label p{font-size:.95rem; font-weight:750}
</style>
""", unsafe_allow_html=True)

def get_connection(): return sqlite3.connect(DB_PATH)

def init_database():
    with get_connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS transaksi (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT NOT NULL, jenis TEXT NOT NULL CHECK (jenis IN ('Pemasukan','Pengeluaran')), kategori TEXT NOT NULL, nominal REAL NOT NULL CHECK (nominal > 0), keterangan TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        conn.commit()

def tambah_transaksi(tanggal, jenis, kategori, nominal, keterangan):
    with get_connection() as conn:
        conn.execute("INSERT INTO transaksi (tanggal,jenis,kategori,nominal,keterangan) VALUES (?,?,?,?,?)", (tanggal.isoformat(), jenis, kategori, float(nominal), keterangan.strip()))
        conn.commit()

def baca_transaksi():
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT id,tanggal,jenis,kategori,nominal,keterangan FROM transaksi ORDER BY tanggal DESC,id DESC", conn)
    if not df.empty:
        df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")
        df["nominal"] = pd.to_numeric(df["nominal"], errors="coerce").fillna(0)
    return df

def hapus_transaksi(transaction_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM transaksi WHERE id=?", (int(transaction_id),)); conn.commit()

def ubah_transaksi(transaction_id, tanggal, jenis, kategori, nominal, keterangan):
    with get_connection() as conn:
        conn.execute("UPDATE transaksi SET tanggal=?, jenis=?, kategori=?, nominal=?, keterangan=? WHERE id=?", (tanggal.isoformat(), jenis, kategori, float(nominal), keterangan.strip(), int(transaction_id)))
        conn.commit()

def rupiah(nilai): return f"Rp {nilai:,.0f}".replace(",", ".")
def format_selisih_rupiah(nilai): return f"+{rupiah(nilai)}" if nilai > 0 else f"-{rupiah(abs(nilai))}" if nilai < 0 else rupiah(0)

def render_header(judul, deskripsi):
    st.markdown(f'<div class="hero-card"><h1>{judul}</h1><p>{deskripsi}</p></div>', unsafe_allow_html=True)

def metric_card(judul, nilai, catatan):
    st.markdown(f'<div class="metric-card"><div class="metric-title">{judul}</div><div class="metric-value">{nilai}</div><div class="metric-note">{catatan}</div></div>', unsafe_allow_html=True)

def section_header(judul, deskripsi=""):
    st.markdown(f'<div class="section-title">{judul}</div><div class="section-subtitle">{deskripsi}</div>', unsafe_allow_html=True)

def tampilkan_notifikasi_aksi():
    pesan = st.session_state.pop("notifikasi_aksi", None)
    if pesan:
        st.toast(pesan, icon=":material/check_circle:"); st.success(pesan)

def siapkan_popup_aksi(nama_aksi, payload): st.session_state["popup_aksi"] = {"nama": nama_aksi, "payload": payload}

@st.dialog("Konfirmasi Aksi")
def popup_konfirmasi_aksi():
    aksi = st.session_state.get("popup_aksi")
    if not aksi:
        st.info("Tidak ada aksi yang perlu dikonfirmasi.")
        if st.button("Tutup", use_container_width=True): st.rerun()
        return
    nama, p = aksi["nama"], aksi["payload"]
    if nama == "tambah":
        st.subheader("Simpan transaksi baru?")
        st.write(f"**Jenis:** {p['jenis']}"); st.write(f"**Tanggal:** {p['tanggal'].strftime('%d-%m-%Y')}"); st.write(f"**Kategori:** {p['kategori']}"); st.write(f"**Nominal:** {rupiah(p['nominal'])}"); st.write(f"**Keterangan:** {p['keterangan'] or '-'}")
    elif nama == "edit":
        st.subheader("Simpan perubahan transaksi?")
        st.write(f"**ID:** {p['transaction_id']}"); st.write(f"**Jenis:** {p['jenis']}"); st.write(f"**Tanggal:** {p['tanggal'].strftime('%d-%m-%Y')}"); st.write(f"**Kategori:** {p['kategori']}"); st.write(f"**Nominal:** {rupiah(p['nominal'])}"); st.write(f"**Keterangan:** {p['keterangan'] or '-'}")
    else:
        st.subheader("Hapus transaksi ini?"); st.warning("Aksi ini permanen dan data tidak dapat dikembalikan.")
        st.write(f"**ID:** {p['transaction_id']}"); st.write(f"**Kategori:** {p['kategori']}"); st.write(f"**Nominal:** {rupiah(p['nominal'])}")
    col_batal, col_lanjut = st.columns(2)
    with col_batal:
        if st.button("Batal", use_container_width=True): st.session_state.pop("popup_aksi", None); st.rerun()
    with col_lanjut:
        label = "Ya, simpan" if nama == "tambah" else "Ya, perbarui" if nama == "edit" else "Ya, hapus"
        if st.button(label, type="primary", use_container_width=True):
            if nama == "tambah": tambah_transaksi(p["tanggal"], p["jenis"], p["kategori"], p["nominal"], p["keterangan"]); pesan = "Transaksi berhasil disimpan."
            elif nama == "edit": ubah_transaksi(p["transaction_id"], p["tanggal"], p["jenis"], p["kategori"], p["nominal"], p["keterangan"]); pesan = "Transaksi berhasil diperbarui."
            else: hapus_transaksi(p["transaction_id"]); pesan = "Transaksi berhasil dihapus."
            st.session_state.pop("popup_aksi", None); st.session_state["notifikasi_aksi"] = pesan; st.rerun()
def tampilkan_kartu_ringkasan(df):
    pemasukan = df.loc[df["jenis"] == "Pemasukan", "nominal"].sum()
    pengeluaran = df.loc[df["jenis"] == "Pengeluaran", "nominal"].sum()
    saldo = pemasukan - pengeluaran
    rasio = pengeluaran / pemasukan * 100 if pemasukan > 0 else 0
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Pemasukan", rupiah(pemasukan), "Akumulasi pemasukan pada periode terpilih")
    with c2: metric_card("Total Pengeluaran", rupiah(pengeluaran), f"{rasio:.1f}% dari pemasukan")
    with c3: metric_card("Saldo Bersih", rupiah(saldo), "Pemasukan dikurangi pengeluaran")
    with c4: metric_card("Jumlah Transaksi", str(len(df)), "Total catatan transaksi")
    if saldo < 0: st.markdown('<div class="status-negative">Pengeluaran lebih besar daripada pemasukan.</div>', unsafe_allow_html=True)
    elif pemasukan > 0 and rasio > 90: st.markdown('<div class="status-warning">Pengeluaran sudah menggunakan lebih dari 90% pemasukan.</div>', unsafe_allow_html=True)
    elif pemasukan > 0: st.markdown('<div class="status-positive">Kondisi arus kas positif dan masih memiliki saldo.</div>', unsafe_allow_html=True)

def filter_data(df, prefix):
    if df.empty: return df
    st.sidebar.markdown("---"); st.sidebar.subheader("Filter Data")
    tmin, tmax = df["tanggal"].min().date(), df["tanggal"].max().date()
    rentang = st.sidebar.date_input("Rentang tanggal", value=(tmin, tmax), min_value=tmin, max_value=tmax, key=f"{prefix}_rentang")
    jenis = st.sidebar.multiselect("Jenis transaksi", ["Pemasukan", "Pengeluaran"], default=["Pemasukan", "Pengeluaran"], key=f"{prefix}_jenis")
    kategori_all = sorted(df["kategori"].dropna().unique().tolist())
    kategori = st.sidebar.multiselect("Kategori", kategori_all, default=kategori_all, key=f"{prefix}_kategori")
    out = df.copy()
    if isinstance(rentang, (tuple, list)) and len(rentang) == 2:
        out = out[(out["tanggal"].dt.date >= rentang[0]) & (out["tanggal"].dt.date <= rentang[1])]
    out = out[out["jenis"].isin(jenis)] if jenis else out.iloc[0:0]
    out = out[out["kategori"].isin(kategori)] if kategori else out.iloc[0:0]
    return out

def format_plotly(fig, tinggi=420):
    fig.update_layout(template="plotly_white", height=tinggi, margin=dict(l=20,r=20,t=65,b=25), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248,250,252,.72)", hoverlabel=dict(bgcolor="white", bordercolor="#cbd5e1", font_size=12), font=dict(family="Arial", size=12, color="#334155"), title_font=dict(size=18, color="#0f172a"), legend_title_text="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)
    return fig

def tampilkan_plotly(fig, tinggi=420):
    st.plotly_chart(format_plotly(fig, tinggi), use_container_width=True, config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})

def grafik_kategori(df, jenis):
    data = df[df["jenis"] == jenis].groupby("kategori", as_index=False)["nominal"].sum().sort_values("nominal", ascending=True)
    if data.empty: st.info(f"Belum ada data {jenis.lower()} pada periode terpilih."); return
    fig = px.bar(data, x="nominal", y="kategori", orientation="h", text="nominal", title=f"{jenis} per Kategori", labels={"kategori":"", "nominal":"Nominal"}, color="nominal", color_continuous_scale=SKALA_PEMASUKAN if jenis == "Pemasukan" else SKALA_PENGELUARAN, custom_data=["kategori"])
    fig.update_traces(texttemplate="Rp %{text:,.0f}", textposition="outside", cliponaxis=False, hovertemplate="<b>%{customdata[0]}</b><br>Total: Rp %{x:,.0f}<extra></extra>")
    fig.update_layout(xaxis_tickprefix="Rp ", xaxis_tickformat=",.0f", coloraxis_showscale=False, showlegend=False)
    tampilkan_plotly(fig)

def grafik_komposisi(df, jenis):
    data = df[df["jenis"] == jenis].groupby("kategori", as_index=False)["nominal"].sum().sort_values("nominal", ascending=False)
    if data.empty: st.info(f"Belum ada data {jenis.lower()} untuk grafik komposisi."); return
    fig = px.pie(data, names="kategori", values="nominal", hole=.58, title=f"Komposisi {jenis}", color_discrete_sequence=WARNA_KATEGORI)
    fig.update_traces(textposition="inside", textinfo="percent", pull=[.06 if i == 0 else 0 for i in range(len(data))], marker=dict(line=dict(color="white", width=2)), hovertemplate="<b>%{label}</b><br>Nominal: Rp %{value:,.0f}<br>Porsi: %{percent}<extra></extra>")
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-.24, xanchor="center", x=.5))
    tampilkan_plotly(fig)

def grafik_bulanan(df):
    data = df.copy(); data["bulan"] = data["tanggal"].dt.to_period("M").dt.to_timestamp()
    bulanan = data.groupby(["bulan", "jenis"], as_index=False)["nominal"].sum().pivot(index="bulan", columns="jenis", values="nominal").fillna(0).reset_index().sort_values("bulan")
    for col in ["Pemasukan", "Pengeluaran"]:
        if col not in bulanan.columns: bulanan[col] = 0
    bulanan["Saldo"] = bulanan["Pemasukan"] - bulanan["Pengeluaran"]
    fig = go.Figure()
    for nama in ["Pemasukan", "Pengeluaran", "Saldo"]:
        fig.add_trace(go.Scatter(x=bulanan["bulan"], y=bulanan[nama], name=nama, mode="lines+markers", line=dict(color=WARNA_JENIS[nama], width=4, shape="spline"), marker=dict(size=10, color=WARNA_JENIS[nama], line=dict(color="white", width=2)), hovertemplate=f"Bulan: %{{x|%b %Y}}<br>{nama}: Rp %{{y:,.0f}}<extra></extra>"))
    fig.update_layout(title="Tren Keuangan Bulanan", hovermode="x unified", yaxis_tickprefix="Rp ", yaxis_tickformat=",.0f")
    fig.update_xaxes(tickformat="%b %Y", rangeslider=dict(visible=True))
    tampilkan_plotly(fig, 470)

def grafik_pengeluaran_harian(df):
    pengeluaran = df[df["jenis"] == "Pengeluaran"].copy()
    if pengeluaran.empty: st.info("Belum ada data pengeluaran harian pada periode terpilih."); return
    pengeluaran["bulan"] = pengeluaran["tanggal"].dt.to_period("M")
    bulan = st.selectbox("Pilih bulan pengeluaran harian", sorted(pengeluaran["bulan"].dropna().unique(), reverse=True), format_func=lambda x: f"{NAMA_BULAN[x.month]} {x.year}", key="bulan_pengeluaran_harian")
    pengeluaran = pengeluaran[pengeluaran["bulan"] == bulan]
    harian = pengeluaran.groupby(pengeluaran["tanggal"].dt.date)["nominal"].sum().reset_index().rename(columns={"tanggal":"Tanggal", "nominal":"Pengeluaran"})
    harian["Tanggal"] = pd.to_datetime(harian["Tanggal"]); harian = harian.sort_values("Tanggal"); harian["Rata-rata 7 Hari"] = harian["Pengeluaran"].rolling(7, min_periods=1).mean()
    total, rata, terbesar = harian["Pengeluaran"].sum(), harian["Pengeluaran"].mean(), harian.loc[harian["Pengeluaran"].idxmax()]
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Bulan Ini", rupiah(total))
    with c2: st.metric("Rata-rata Harian", rupiah(rata))
    with c3: st.metric("Hari Tertinggi", rupiah(terbesar["Pengeluaran"]), terbesar["Tanggal"].strftime("%d-%m-%Y"))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=harian["Tanggal"], y=harian["Pengeluaran"], name="Pengeluaran Harian", mode="lines+markers", fill="tozeroy", line=dict(color=WARNA_JENIS["Pengeluaran"], width=3, shape="spline"), marker=dict(size=8, color=WARNA_JENIS["Pengeluaran"], line=dict(color="white", width=2)), hovertemplate="Tanggal: %{x|%d-%m-%Y}<br>Pengeluaran: Rp %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=harian["Tanggal"], y=harian["Rata-rata 7 Hari"], name="Rata-rata 7 Hari", mode="lines", line=dict(color="#8B5CF6", width=3, dash="dot", shape="spline"), hovertemplate="Tanggal: %{x|%d-%m-%Y}<br>Rata-rata: Rp %{y:,.0f}<extra></extra>"))
    fig.update_layout(title=f"Pengeluaran Harian - {NAMA_BULAN[bulan.month]} {bulan.year}", hovermode="x unified", yaxis_tickprefix="Rp ", yaxis_tickformat=",.0f")
    fig.update_xaxes(tickformat="%d %b", rangeslider=dict(visible=True))
    tampilkan_plotly(fig, 450)
def grafik_pengeluaran_bulanan(df):
    pengeluaran = df[df["jenis"] == "Pengeluaran"].copy()
    if pengeluaran.empty: st.info("Belum ada data pengeluaran bulanan pada periode terpilih."); return
    pengeluaran["bulan"] = pengeluaran["tanggal"].dt.to_period("M").dt.to_timestamp()
    bulanan = pengeluaran.groupby("bulan", as_index=False)["nominal"].sum().sort_values("bulan").rename(columns={"nominal":"Pengeluaran"})
    fig = px.bar(bulanan, x="bulan", y="Pengeluaran", text="Pengeluaran", title="Pengeluaran Tiap Bulan", labels={"bulan":"", "Pengeluaran":"Pengeluaran"}, color="Pengeluaran", color_continuous_scale=SKALA_PENGELUARAN)
    fig.update_traces(texttemplate="Rp %{text:,.0f}", textposition="outside", hovertemplate="Bulan: %{x|%b %Y}<br>Pengeluaran: Rp %{y:,.0f}<extra></extra>")
    fig.update_layout(yaxis_tickprefix="Rp ", yaxis_tickformat=",.0f", coloraxis_showscale=False, showlegend=False)
    fig.update_xaxes(tickformat="%b %Y")
    tampilkan_plotly(fig, 450)

def grafik_pengeluaran_harian_semua_bulan(df):
    pengeluaran = df[df["jenis"] == "Pengeluaran"].copy()
    if pengeluaran.empty: st.info("Belum ada data pengeluaran harian antar bulan pada periode terpilih."); return
    pengeluaran["Hari"] = pengeluaran["tanggal"].dt.day
    pengeluaran["Bulan"] = pengeluaran["tanggal"].dt.to_period("M").dt.to_timestamp()
    pengeluaran["Label Bulan"] = pengeluaran["Bulan"].map(lambda x: f"{NAMA_BULAN_PENDEK[x.month]} {x.year}")
    data = pengeluaran.groupby(["Bulan", "Label Bulan", "Hari"], as_index=False)["nominal"].sum().sort_values(["Bulan", "Hari"]).rename(columns={"nominal":"Pengeluaran"})
    fig = px.line(data, x="Hari", y="Pengeluaran", color="Label Bulan", markers=True, title="Pengeluaran Harian di Setiap Bulan", labels={"Hari":"Tanggal", "Pengeluaran":"Pengeluaran", "Label Bulan":"Bulan"}, color_discrete_sequence=WARNA_KATEGORI, custom_data=["Label Bulan"])
    fig.update_traces(line=dict(width=3, shape="spline"), marker=dict(size=7, line=dict(color="white", width=1)), hovertemplate="Bulan: %{customdata[0]}<br>Tanggal: %{x}<br>Pengeluaran: Rp %{y:,.0f}<extra></extra>")
    fig.update_layout(hovermode="x unified", yaxis_tickprefix="Rp ", yaxis_tickformat=",.0f")
    fig.update_xaxes(dtick=1, range=[1, 31])
    tampilkan_plotly(fig, 480)

def grafik_treemap_kategori(df, jenis):
    data = df[df["jenis"] == jenis].groupby("kategori", as_index=False)["nominal"].sum().sort_values("nominal", ascending=False)
    if data.empty: st.info(f"Belum ada data {jenis.lower()} untuk treemap."); return
    fig = px.treemap(data, path=[px.Constant(jenis), "kategori"], values="nominal", color="nominal", color_continuous_scale=SKALA_PEMASUKAN if jenis == "Pemasukan" else SKALA_PENGELUARAN, title=f"Peta Besar Kategori {jenis}")
    fig.update_traces(texttemplate="<b>%{label}</b><br>Rp %{value:,.0f}", hovertemplate="<b>%{label}</b><br>Nominal: Rp %{value:,.0f}<extra></extra>", marker=dict(line=dict(color="white", width=2)))
    fig.update_layout(coloraxis_showscale=False)
    tampilkan_plotly(fig)

def rekap_bulanan(df):
    if df.empty: return pd.DataFrame()
    data = df.copy(); data["Bulan"] = data["tanggal"].dt.to_period("M").astype(str)
    rekap = data.groupby(["Bulan", "jenis"], as_index=False)["nominal"].sum().pivot(index="Bulan", columns="jenis", values="nominal").fillna(0).reset_index()
    for col in ["Pemasukan", "Pengeluaran"]:
        if col not in rekap.columns: rekap[col] = 0
    rekap = rekap.sort_values("Bulan")
    rekap["Saldo"] = rekap["Pemasukan"] - rekap["Pengeluaran"]
    rekap["Rasio Pengeluaran (%)"] = rekap.apply(lambda r: r["Pengeluaran"] / r["Pemasukan"] * 100 if r["Pemasukan"] > 0 else 0, axis=1)
    rekap["Perubahan Pemasukan"] = rekap["Pemasukan"].diff().fillna(0)
    rekap["Perubahan Pengeluaran"] = rekap["Pengeluaran"].diff().fillna(0)
    def label(nilai):
        if nilai > 0: return "Lebih tinggi dari bulan sebelumnya"
        if nilai < 0: return "Lebih rendah dari bulan sebelumnya"
        return "Sama dengan bulan sebelumnya"
    rekap["Status Pemasukan"] = rekap["Perubahan Pemasukan"].map(label)
    rekap["Status Pengeluaran"] = rekap["Perubahan Pengeluaran"].map(label)
    if len(rekap) == 1:
        rekap.loc[rekap.index[0], "Status Pemasukan"] = "Belum ada bulan pembanding"
        rekap.loc[rekap.index[0], "Status Pengeluaran"] = "Belum ada bulan pembanding"
    return rekap.sort_values("Bulan", ascending=False)

def format_tabel_rekap(rekap):
    hasil = rekap.copy()
    for col in ["Pemasukan", "Pengeluaran", "Saldo"]: hasil[col] = hasil[col].map(rupiah)
    for col in ["Perubahan Pemasukan", "Perubahan Pengeluaran"]: hasil[col] = hasil[col].map(format_selisih_rupiah)
    hasil["Rasio Pengeluaran (%)"] = hasil["Rasio Pengeluaran (%)"].map(lambda x: f"{x:.1f}%")
    return hasil

def pesan_perubahan_bulanan(rekap):
    if rekap.empty: return
    urut = rekap.sort_values("Bulan")
    if len(urut) < 2:
        st.info("Belum ada bulan pembanding untuk melihat perubahan pemasukan dan pengeluaran."); return
    now, prev = urut.iloc[-1], urut.iloc[-2]
    bp, bl = now["Bulan"], prev["Bulan"]
    dp, dg = now["Perubahan Pemasukan"], now["Perubahan Pengeluaran"]
    if dp > 0: st.success(f"Pemasukan {bp} lebih tinggi {format_selisih_rupiah(dp)} dibanding {bl}.")
    elif dp < 0: st.warning(f"Pemasukan {bp} lebih rendah {format_selisih_rupiah(dp)} dibanding {bl}.")
    else: st.info(f"Pemasukan {bp} sama dengan {bl}.")
    if dg > 0: st.warning(f"Pengeluaran {bp} lebih tinggi {format_selisih_rupiah(dg)} dibanding {bl}.")
    elif dg < 0: st.success(f"Pengeluaran {bp} lebih rendah {format_selisih_rupiah(dg)} dibanding {bl}.")
    else: st.info(f"Pengeluaran {bp} sama dengan {bl}.")

def tampilkan_ringkasan_kategori(df):
    pengeluaran = df[df["jenis"] == "Pengeluaran"]
    if pengeluaran.empty: return
    terbesar = pengeluaran.groupby("kategori")["nominal"].sum().sort_values(ascending=False)
    transaksi = pengeluaran.loc[pengeluaran["nominal"].idxmax()]
    c1, c2 = st.columns(2)
    with c1: st.info(f"Kategori pengeluaran terbesar: **{terbesar.index[0]}** ({rupiah(terbesar.iloc[0])})")
    with c2: st.info(f"Transaksi pengeluaran terbesar: **{rupiah(transaksi['nominal'])}** untuk {transaksi['kategori']}")
init_database()
tampilkan_notifikasi_aksi()
if st.session_state.get("popup_aksi"): popup_konfirmasi_aksi()
df_semua = baca_transaksi()

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">KeuanganKu</div>
            <div class="sidebar-brand-subtitle">Kelola arus kas pribadi dengan lebih rapi.</div>
        </div>
        <div class="sidebar-section-label">Menu Utama</div>
        """,
        unsafe_allow_html=True,
    )
    label_menu = {
        "Dashboard": "Dashboard  |  Ringkasan",
        "Tambah Transaksi": "Input Data  |  Tambah transaksi",
        "Riwayat Transaksi": "Riwayat  |  Data transaksi",
        "Kelola Data": "Kelola  |  Edit dan hapus",
    }
    menu = st.radio(
        "Navigasi",
        list(label_menu.keys()),
        format_func=lambda nilai: label_menu[nilai],
        label_visibility="collapsed",
    )
    if not df_semua.empty:
        st.markdown(
            f"""
            <div class="sidebar-summary">
                <div class="sidebar-summary-label">Total nominal seluruh transaksi</div>
                <div class="sidebar-summary-value">{rupiah(df_semua['nominal'].sum())}</div>
                <div class="sidebar-summary-note">{len(df_semua)} transaksi tersimpan</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="sidebar-summary">
                <div class="sidebar-summary-label">Status data</div>
                <div class="sidebar-summary-value">Belum ada transaksi</div>
                <div class="sidebar-summary-note">Mulai dari menu Input Data.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

if menu == "Dashboard":
    render_header("Dashboard Keuangan", "Pantau pemasukan, pengeluaran, saldo, dan tren keuangan dalam satu tampilan.")
    if df_semua.empty: st.info("Belum ada transaksi. Silakan buka menu Tambah Transaksi.")
    else:
        df_filter = filter_data(df_semua, "dashboard")
        if df_filter.empty: st.warning("Tidak ada transaksi yang sesuai dengan filter.")
        else:
            tampilkan_kartu_ringkasan(df_filter); st.write(""); tampilkan_ringkasan_kategori(df_filter); st.write("")
            section_header("Visualisasi Interaktif", "Gunakan hover, zoom, legend, dan range slider untuk menelusuri pola transaksi.")
            tab_tren, tab_pengeluaran, tab_pemasukan = st.tabs(["Tren Keuangan", "Pengeluaran", "Pemasukan"])
            with tab_tren:
                grafik_bulanan(df_filter)
                c1, c2 = st.columns(2)
                with c1: grafik_pengeluaran_harian(df_filter)
                with c2: grafik_pengeluaran_bulanan(df_filter)
                grafik_pengeluaran_harian_semua_bulan(df_filter)
            with tab_pengeluaran:
                c1, c2 = st.columns([1.15, 1])
                with c1: grafik_kategori(df_filter, "Pengeluaran")
                with c2: grafik_komposisi(df_filter, "Pengeluaran")
                grafik_treemap_kategori(df_filter, "Pengeluaran")
            with tab_pemasukan:
                c1, c2 = st.columns([1.15, 1])
                with c1: grafik_kategori(df_filter, "Pemasukan")
                with c2: grafik_komposisi(df_filter, "Pemasukan")
                grafik_treemap_kategori(df_filter, "Pemasukan")
            st.write("")
            section_header("Rekap Bulanan", "Ringkasan pemasukan, pengeluaran, saldo, rasio, dan perubahan dibanding bulan sebelumnya.")
            rekap = rekap_bulanan(df_filter)
            pesan_perubahan_bulanan(rekap)
            st.dataframe(format_tabel_rekap(rekap), use_container_width=True, hide_index=True, column_config={
                "Bulan": st.column_config.TextColumn("Bulan", width="small"),
                "Pemasukan": st.column_config.TextColumn("Pemasukan"),
                "Pengeluaran": st.column_config.TextColumn("Pengeluaran"),
                "Saldo": st.column_config.TextColumn("Saldo"),
                "Rasio Pengeluaran (%)": st.column_config.TextColumn("Rasio Pengeluaran"),
                "Perubahan Pemasukan": st.column_config.TextColumn("Perubahan Pemasukan"),
                "Status Pemasukan": st.column_config.TextColumn("Status Pemasukan"),
                "Perubahan Pengeluaran": st.column_config.TextColumn("Perubahan Pengeluaran"),
                "Status Pengeluaran": st.column_config.TextColumn("Status Pengeluaran"),
            })
            st.info("Klik tombol unduh untuk menyimpan rekap bulanan sebagai CSV.")
            st.download_button("Unduh Rekap Bulanan", data=rekap.to_csv(index=False).encode("utf-8-sig"), file_name="rekap_keuangan_bulanan.csv", mime="text/csv", use_container_width=True)

elif menu == "Tambah Transaksi":
    render_header("Tambah Transaksi", "Catat pemasukan atau pengeluaran baru dengan cepat.")
    info, form_col = st.columns([.85, 1.8])
    with info:
        st.markdown("""<div class="section-card"><div class="section-title">Petunjuk Pengisian</div><div class="section-subtitle">Isi tanggal, jenis, kategori, nominal, dan keterangan transaksi.</div><b>Pengeluaran</b><p>Makan, barang, biaya wajib, pekerjaan, dan kebutuhan lainnya.</p><b>Pemasukan</b><p>Gaji, sampingan, dan translok.</p></div>""", unsafe_allow_html=True)
    with form_col:
        jenis = st.radio("Pilih jenis transaksi", ["Pengeluaran", "Pemasukan"], horizontal=True)
        with st.form("form_transaksi", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                tanggal = st.date_input("Tanggal transaksi", value=date.today()); kategori = st.selectbox("Kategori", KATEGORI[jenis])
            with c2:
                nominal = st.number_input("Nominal", min_value=1_000, step=1_000, format="%d", help="Masukkan nominal tanpa tanda titik."); keterangan = st.text_input("Keterangan", placeholder="Contoh: makan siang")
            simpan = st.form_submit_button("Simpan Transaksi", use_container_width=True, type="primary")
        if simpan:
            siapkan_popup_aksi("tambah", {"tanggal": tanggal, "jenis": jenis, "kategori": kategori, "nominal": nominal, "keterangan": keterangan}); popup_konfirmasi_aksi()

elif menu == "Riwayat Transaksi":
    render_header("Riwayat Transaksi", "Lihat seluruh transaksi dan unduh data dalam format CSV.")
    if df_semua.empty: st.info("Belum ada transaksi.")
    else:
        df_filter = filter_data(df_semua, "riwayat")
        if df_filter.empty: st.warning("Tidak ada transaksi yang sesuai dengan filter.")
        else:
            tampil = df_filter.copy(); tampil["tanggal"] = tampil["tanggal"].dt.strftime("%d-%m-%Y"); tampil["nominal"] = tampil["nominal"].map(rupiah)
            st.dataframe(tampil, use_container_width=True, hide_index=True, column_config={"id": st.column_config.NumberColumn("ID", width="small"), "tanggal": st.column_config.TextColumn("Tanggal", width="small"), "jenis": st.column_config.TextColumn("Jenis", width="small"), "kategori": st.column_config.TextColumn("Kategori"), "nominal": st.column_config.TextColumn("Nominal"), "keterangan": st.column_config.TextColumn("Keterangan", width="large")})
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Jumlah Data", len(df_filter))
            with c2: st.metric("Total Pemasukan", rupiah(df_filter.loc[df_filter["jenis"] == "Pemasukan", "nominal"].sum()))
            with c3: st.metric("Total Pengeluaran", rupiah(df_filter.loc[df_filter["jenis"] == "Pengeluaran", "nominal"].sum()))
            st.info("Klik tombol unduh untuk menyimpan riwayat transaksi sebagai CSV.")
            st.download_button("Unduh Riwayat Transaksi", data=df_filter.to_csv(index=False).encode("utf-8-sig"), file_name="riwayat_transaksi.csv", mime="text/csv", use_container_width=True)

elif menu == "Kelola Data":
    render_header("Kelola Data", "Edit atau hapus transaksi yang sudah tersimpan.")
    if df_semua.empty: st.info("Belum ada transaksi yang dapat dikelola.")
    else:
        daftar_id = df_semua["id"].tolist()
        transaction_id = st.selectbox("Pilih transaksi", daftar_id, format_func=lambda x: f"ID {x} | {df_semua.loc[df_semua['id'] == x, 'tanggal'].iloc[0].strftime('%d-%m-%Y')} | {df_semua.loc[df_semua['id'] == x, 'kategori'].iloc[0]} | {rupiah(df_semua.loc[df_semua['id'] == x, 'nominal'].iloc[0])}")
        data_lama = df_semua[df_semua["id"] == transaction_id].iloc[0]
        edit_col, hapus_col = st.columns([1.6, .9])
        with edit_col:
            st.subheader("Edit Transaksi")
            jenis_baru = st.radio("Jenis transaksi", ["Pengeluaran", "Pemasukan"], index=0 if data_lama["jenis"] == "Pengeluaran" else 1, horizontal=True, key=f"jenis_edit_{transaction_id}")
            daftar_kategori = KATEGORI[jenis_baru]; idx = daftar_kategori.index(data_lama["kategori"]) if data_lama["kategori"] in daftar_kategori else 0
            with st.form(f"form_edit_{transaction_id}"):
                tanggal_baru = st.date_input("Tanggal", value=data_lama["tanggal"].date()); kategori_baru = st.selectbox("Kategori", daftar_kategori, index=idx); nominal_baru = st.number_input("Nominal", min_value=1_000, step=1_000, value=int(data_lama["nominal"]), format="%d"); keterangan_baru = st.text_area("Keterangan", value=data_lama["keterangan"] or "", height=100)
                simpan_perubahan = st.form_submit_button("Simpan Perubahan", use_container_width=True, type="primary")
            if simpan_perubahan:
                siapkan_popup_aksi("edit", {"transaction_id": transaction_id, "tanggal": tanggal_baru, "jenis": jenis_baru, "kategori": kategori_baru, "nominal": nominal_baru, "keterangan": keterangan_baru}); popup_konfirmasi_aksi()
        with hapus_col:
            st.subheader("Hapus Transaksi"); st.error("Data yang dihapus tidak dapat dikembalikan.")
            st.write(f"**ID:** {transaction_id}"); st.write(f"**Kategori:** {data_lama['kategori']}"); st.write(f"**Nominal:** {rupiah(data_lama['nominal'])}")
            konfirmasi = st.checkbox("Saya yakin ingin menghapus transaksi ini", key=f"hapus_{transaction_id}")
            if st.button("Hapus Transaksi", disabled=not konfirmasi, use_container_width=True, type="secondary"):
                siapkan_popup_aksi("hapus", {"transaction_id": transaction_id, "kategori": data_lama["kategori"], "nominal": data_lama["nominal"]}); popup_konfirmasi_aksi()