import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# KONFIGURASI
# =========================================================
st.set_page_config(
    page_title="Analisis Keuangan Pribadi",
    page_icon="💰",
    layout="wide",
)

DB_PATH = Path(__file__).with_name("keuangan.db")

KATEGORI = {
    "Pengeluaran": [
        "Makan/Jajan",
        "Barang",
        "Biaya Wajib",
        "Biaya Tak Terduga",
        "Pekerjaan",
        "Kebutuhan Sehari-hari",
    ],
    "Pemasukan": [
        "Gaji",
        "Sampingan (Joki)",
        "Translok",
    ],
}


# =========================================================
# FUNGSI DATABASE
# =========================================================
def get_connection():
    return sqlite3.connect(DB_PATH)


def init_database():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transaksi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanggal TEXT NOT NULL,
                jenis TEXT NOT NULL
                    CHECK (jenis IN ('Pemasukan', 'Pengeluaran')),
                kategori TEXT NOT NULL,
                nominal REAL NOT NULL CHECK (nominal > 0),
                keterangan TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def tambah_transaksi(tanggal, jenis, kategori, nominal, keterangan):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO transaksi
                (tanggal, jenis, kategori, nominal, keterangan)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tanggal.isoformat(),
                jenis,
                kategori,
                float(nominal),
                keterangan.strip(),
            ),
        )
        conn.commit()


def baca_transaksi():
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT id, tanggal, jenis, kategori, nominal, keterangan
            FROM transaksi
            ORDER BY tanggal DESC, id DESC
            """,
            conn,
        )

    if not df.empty:
        df["tanggal"] = pd.to_datetime(df["tanggal"])
        df["nominal"] = pd.to_numeric(df["nominal"], errors="coerce").fillna(0)
    return df


def hapus_transaksi(transaction_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM transaksi WHERE id = ?", (int(transaction_id),))
        conn.commit()


def ubah_transaksi(transaction_id, tanggal, jenis, kategori, nominal, keterangan):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE transaksi
            SET tanggal = ?, jenis = ?, kategori = ?, nominal = ?, keterangan = ?
            WHERE id = ?
            """,
            (
                tanggal.isoformat(),
                jenis,
                kategori,
                float(nominal),
                keterangan.strip(),
                int(transaction_id),
            ),
        )
        conn.commit()


# =========================================================
# FUNGSI TAMPILAN
# =========================================================
def rupiah(nilai):
    return f"Rp {nilai:,.0f}".replace(",", ".")


def tampilkan_kartu_ringkasan(df):
    total_pemasukan = df.loc[df["jenis"] == "Pemasukan", "nominal"].sum()
    total_pengeluaran = df.loc[df["jenis"] == "Pengeluaran", "nominal"].sum()
    saldo = total_pemasukan - total_pengeluaran

    if total_pemasukan > 0:
        rasio_tabungan = saldo / total_pemasukan * 100
    else:
        rasio_tabungan = 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Pemasukan", rupiah(total_pemasukan))
    col2.metric("Total Pengeluaran", rupiah(total_pengeluaran))
    col3.metric("Saldo", rupiah(saldo))
    col4.metric("Rasio Saldo", f"{rasio_tabungan:.1f}%")

    if saldo < 0:
        st.warning("Pengeluaran lebih besar daripada pemasukan pada periode ini.")
    elif total_pemasukan > 0 and rasio_tabungan < 10:
        st.info("Saldo masih di bawah 10% dari pemasukan.")
    elif total_pemasukan > 0:
        st.success("Arus kas pada periode ini masih positif.")


def filter_data(df):
    if df.empty:
        return df

    st.sidebar.header("Filter Analisis")

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

    semua_kategori = sorted(df["kategori"].dropna().unique().tolist())
    kategori_filter = st.sidebar.multiselect(
        "Kategori",
        semua_kategori,
        default=semua_kategori,
    )

    filtered = df.copy()

    if isinstance(rentang, (tuple, list)) and len(rentang) == 2:
        mulai, selesai = rentang
        filtered = filtered[
            (filtered["tanggal"].dt.date >= mulai)
            & (filtered["tanggal"].dt.date <= selesai)
        ]

    if jenis_filter:
        filtered = filtered[filtered["jenis"].isin(jenis_filter)]
    else:
        filtered = filtered.iloc[0:0]

    if kategori_filter:
        filtered = filtered[filtered["kategori"].isin(kategori_filter)]
    else:
        filtered = filtered.iloc[0:0]

    return filtered


def grafik_kategori(df, jenis):
    data = (
        df[df["jenis"] == jenis]
        .groupby("kategori", as_index=False)["nominal"]
        .sum()
        .sort_values("nominal", ascending=False)
    )

    if data.empty:
        st.info(f"Belum ada data {jenis.lower()} pada periode terpilih.")
        return

    fig = px.bar(
        data,
        x="kategori",
        y="nominal",
        text_auto=".2s",
        title=f"{jenis} per Kategori",
        labels={"kategori": "Kategori", "nominal": "Nominal"},
    )
    fig.update_layout(
        xaxis_title=None,
        yaxis_tickprefix="Rp ",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def grafik_komposisi(df, jenis):
    data = (
        df[df["jenis"] == jenis]
        .groupby("kategori", as_index=False)["nominal"]
        .sum()
    )

    if data.empty:
        return

    fig = px.pie(
        data,
        names="kategori",
        values="nominal",
        hole=0.45,
        title=f"Komposisi {jenis}",
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)


def grafik_bulanan(df):
    if df.empty:
        st.info("Belum ada data untuk grafik bulanan.")
        return

    data = df.copy()
    data["bulan"] = data["tanggal"].dt.to_period("M").astype(str)

    bulanan = (
        data.groupby(["bulan", "jenis"], as_index=False)["nominal"]
        .sum()
        .pivot(index="bulan", columns="jenis", values="nominal")
        .fillna(0)
        .reset_index()
    )

    if "Pemasukan" not in bulanan.columns:
        bulanan["Pemasukan"] = 0
    if "Pengeluaran" not in bulanan.columns:
        bulanan["Pengeluaran"] = 0

    bulanan["Saldo"] = bulanan["Pemasukan"] - bulanan["Pengeluaran"]

    data_grafik = bulanan.melt(
        id_vars="bulan",
        value_vars=["Pemasukan", "Pengeluaran", "Saldo"],
        var_name="Jenis",
        value_name="Nominal",
    )

    fig = px.line(
        data_grafik,
        x="bulan",
        y="Nominal",
        color="Jenis",
        markers=True,
        title="Tren Keuangan Bulanan",
        labels={"bulan": "Bulan"},
    )
    fig.update_layout(
        xaxis_title=None,
        yaxis_tickprefix="Rp ",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def rekap_bulanan(df):
    if df.empty:
        return pd.DataFrame()

    data = df.copy()
    data["Bulan"] = data["tanggal"].dt.to_period("M").astype(str)

    rekap = (
        data.groupby(["Bulan", "jenis"], as_index=False)["nominal"]
        .sum()
        .pivot(index="Bulan", columns="jenis", values="nominal")
        .fillna(0)
        .reset_index()
    )

    if "Pemasukan" not in rekap.columns:
        rekap["Pemasukan"] = 0
    if "Pengeluaran" not in rekap.columns:
        rekap["Pengeluaran"] = 0

    rekap["Saldo"] = rekap["Pemasukan"] - rekap["Pengeluaran"]
    rekap["Rasio Pengeluaran (%)"] = rekap.apply(
        lambda row: (
            row["Pengeluaran"] / row["Pemasukan"] * 100
            if row["Pemasukan"] > 0
            else 0
        ),
        axis=1,
    )

    return rekap.sort_values("Bulan", ascending=False)


def format_tabel_rekap(rekap):
    hasil = rekap.copy()
    for kolom in ["Pemasukan", "Pengeluaran", "Saldo"]:
        hasil[kolom] = hasil[kolom].map(rupiah)
    hasil["Rasio Pengeluaran (%)"] = hasil["Rasio Pengeluaran (%)"].map(
        lambda nilai: f"{nilai:.1f}%"
    )
    return hasil


# =========================================================
# INISIALISASI
# =========================================================
init_database()

st.title("💰 Analisis Keuangan Pribadi")
st.caption(
    "Catat pemasukan dan pengeluaran, lihat visualisasi, "
    "dan pantau rekap keuangan setiap bulan."
)

menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Tambah Transaksi",
        "Riwayat Transaksi",
        "Kelola Data",
    ],
)

df_semua = baca_transaksi()


# =========================================================
# MENU: TAMBAH TRANSAKSI
# =========================================================
if menu == "Tambah Transaksi":
    st.subheader("Tambah Transaksi")

    jenis = st.radio(
        "Jenis transaksi",
        ["Pengeluaran", "Pemasukan"],
        horizontal=True,
    )

    with st.form("form_transaksi", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            tanggal = st.date_input("Tanggal", value=date.today())
            kategori = st.selectbox("Kategori", KATEGORI[jenis])

        with col2:
            nominal = st.number_input(
                "Nominal",
                min_value=1_000,
                step=1_000,
                format="%d",
            )
            keterangan = st.text_input(
                "Keterangan",
                placeholder="Contoh: makan siang, gaji bulan Juli, dan sebagainya",
            )

        simpan = st.form_submit_button(
            "Simpan Transaksi",
            use_container_width=True,
            type="primary",
        )

    if simpan:
        tambah_transaksi(
            tanggal=tanggal,
            jenis=jenis,
            kategori=kategori,
            nominal=nominal,
            keterangan=keterangan,
        )
        st.success("Transaksi berhasil disimpan.")
        st.rerun()


# =========================================================
# MENU: DASHBOARD
# =========================================================
elif menu == "Dashboard":
    if df_semua.empty:
        st.info(
            "Belum ada transaksi. Silakan buka menu "
            "'Tambah Transaksi' untuk memasukkan data."
        )
    else:
        df_filter = filter_data(df_semua)

        if df_filter.empty:
            st.warning("Tidak ada transaksi yang sesuai dengan filter.")
        else:
            tampilkan_kartu_ringkasan(df_filter)

            st.divider()
            st.subheader("Visualisasi Bulanan")
            grafik_bulanan(df_filter)

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                grafik_kategori(df_filter, "Pengeluaran")
            with col2:
                grafik_komposisi(df_filter, "Pengeluaran")

            col3, col4 = st.columns(2)
            with col3:
                grafik_kategori(df_filter, "Pemasukan")
            with col4:
                grafik_komposisi(df_filter, "Pemasukan")

            st.divider()
            st.subheader("Rekap Setiap Bulan")
            rekap = rekap_bulanan(df_filter)
            st.dataframe(
                format_tabel_rekap(rekap),
                use_container_width=True,
                hide_index=True,
            )

            csv_rekap = rekap.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Unduh Rekap Bulanan (CSV)",
                data=csv_rekap,
                file_name="rekap_keuangan_bulanan.csv",
                mime="text/csv",
            )


# =========================================================
# MENU: RIWAYAT
# =========================================================
elif menu == "Riwayat Transaksi":
    st.subheader("Riwayat Transaksi")

    if df_semua.empty:
        st.info("Belum ada transaksi.")
    else:
        df_filter = filter_data(df_semua)

        tampil = df_filter.copy()
        tampil["tanggal"] = tampil["tanggal"].dt.strftime("%d-%m-%Y")
        tampil["nominal"] = tampil["nominal"].map(rupiah)

        st.dataframe(
            tampil,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID"),
                "tanggal": "Tanggal",
                "jenis": "Jenis",
                "kategori": "Kategori",
                "nominal": "Nominal",
                "keterangan": "Keterangan",
            },
        )

        csv = df_filter.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Unduh Riwayat Transaksi (CSV)",
            data=csv,
            file_name="riwayat_transaksi.csv",
            mime="text/csv",
        )


# =========================================================
# MENU: KELOLA DATA
# =========================================================
elif menu == "Kelola Data":
    st.subheader("Edit atau Hapus Transaksi")

    if df_semua.empty:
        st.info("Belum ada transaksi yang dapat dikelola.")
    else:
        daftar_id = df_semua["id"].tolist()

        transaction_id = st.selectbox(
            "Pilih ID transaksi",
            daftar_id,
            format_func=lambda nilai: (
                f"ID {nilai} — "
                f"{df_semua.loc[df_semua['id'] == nilai, 'tanggal'].iloc[0].strftime('%d-%m-%Y')} — "
                f"{df_semua.loc[df_semua['id'] == nilai, 'kategori'].iloc[0]} — "
                f"{rupiah(df_semua.loc[df_semua['id'] == nilai, 'nominal'].iloc[0])}"
            ),
        )

        data_lama = df_semua[df_semua["id"] == transaction_id].iloc[0]

        jenis_baru = st.radio(
            "Jenis transaksi",
            ["Pengeluaran", "Pemasukan"],
            index=0 if data_lama["jenis"] == "Pengeluaran" else 1,
            horizontal=True,
            key=f"jenis_edit_{transaction_id}",
        )

        kategori_default = data_lama["kategori"]
        daftar_kategori = KATEGORI[jenis_baru]
        index_kategori = (
            daftar_kategori.index(kategori_default)
            if kategori_default in daftar_kategori
            else 0
        )

        with st.form(f"form_edit_{transaction_id}"):
            col1, col2 = st.columns(2)

            with col1:
                tanggal_baru = st.date_input(
                    "Tanggal",
                    value=data_lama["tanggal"].date(),
                )
                kategori_baru = st.selectbox(
                    "Kategori",
                    daftar_kategori,
                    index=index_kategori,
                )

            with col2:
                nominal_baru = st.number_input(
                    "Nominal",
                    min_value=1_000,
                    step=1_000,
                    value=int(data_lama["nominal"]),
                    format="%d",
                )
                keterangan_baru = st.text_input(
                    "Keterangan",
                    value=data_lama["keterangan"] or "",
                )

            simpan_perubahan = st.form_submit_button(
                "Simpan Perubahan",
                use_container_width=True,
                type="primary",
            )

        if simpan_perubahan:
            ubah_transaksi(
                transaction_id,
                tanggal_baru,
                jenis_baru,
                kategori_baru,
                nominal_baru,
                keterangan_baru,
            )
            st.success("Transaksi berhasil diperbarui.")
            st.rerun()

        st.divider()
        st.warning("Penghapusan data tidak dapat dibatalkan.")

        konfirmasi = st.checkbox(
            f"Saya yakin ingin menghapus transaksi ID {transaction_id}"
        )

        if st.button(
            "Hapus Transaksi",
            disabled=not konfirmasi,
            use_container_width=True,
        ):
            hapus_transaksi(transaction_id)
            st.success("Transaksi berhasil dihapus.")
            st.rerun()
