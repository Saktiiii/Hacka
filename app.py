
import streamlit as st
import pandas as pd
import plotly.express as px

from datetime import date, datetime, time, timedelta
from pathlib import Path

from prediction import prediksi_durasi
from scheduler import buat_jadwal_produksi
from energy import hitung_batas_watt, buat_profil_beban
from finance import hitung_ekonomi


# =====================================================
# KONFIGURASI HALAMAN
# =====================================================

st.set_page_config(
    page_title="MAECO | Batik Optimizer",
    page_icon="⚡",
    layout="wide"
)

# Memuat CSS
css = Path(__file__).with_name("style.css")

if css.exists():
    st.markdown(
        f"<style>{css.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True
    )


# =====================================================
# SESSION STATE
# =====================================================

if "pesanan" not in st.session_state:
    st.session_state.pesanan = pd.DataFrame([
        {
            "Kode": "ORD-001",
            "Jenis": "Batik Cap",
            "Kuantitas": 100,
            "Satuan": "potong",
            "Deadline": date.today() + timedelta(days=2),
            "Harga Jual": 75000
        }
    ])

if "sumber_daya" not in st.session_state:
    st.session_state.sumber_daya = {
        "pekerja": 4,
        "kompor": 1,
        "pompa": 1,
        "oven": 1
    }

if "hasil_jadwal" not in st.session_state:
    st.session_state.hasil_jadwal = None


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown("# ⚡ MAECO")
    st.caption("SMART BATIK PRODUCTION OPTIMIZER")

    page = st.radio(
        "NAVIGASI",
        [
            "Dashboard",
            "Input Produksi",
            "Jadwal & Energi",
            "Simulasi Skenario"
        ]
    )

    st.divider()

    st.markdown("### Pengaturan Kelistrikan")

    va = st.number_input(
        "Kapasitas MCB (VA)",
        450,
        30000,
        3500,
        500
    )

    pf = st.slider(
        "Faktor daya",
        0.50,
        1.00,
        0.85,
        0.05
    )

    work_start = st.time_input(
        "Mulai operasional",
        time(8, 0)
    )

    work_end = st.time_input(
        "Selesai operasional",
        time(16, 0)
    )

    tariff = st.number_input(
        "Tarif listrik (Rp/kWh)",
        0,
        10000,
        1444,
        50
    )

    st.divider()

    st.markdown("### Pengaturan Biaya Tenaga Kerja")

    upah_per_pekerja = st.number_input(
        "Upah per pekerja per hari (Rp)",
        min_value=0,
        max_value=10000000,
        value=100000,
        step=5000
    )


# =====================================================
# PENGATURAN DAYA DAN DATA
# =====================================================

safe_watt = hitung_batas_watt(va, pf)

orders = st.session_state.pesanan.copy()
resources = st.session_state.sumber_daya


# =====================================================
# HEADER
# =====================================================

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">SMART ENERGY MANAGEMENT PLATFORM</div>
        <h1>MAECO — Batik Production Optimizer</h1>
        <p>
            Optimasi jadwal produksi dengan mempertimbangkan
            listrik, pekerja, mesin, dan target pesanan.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# =====================================================
# FUNGSI SUMBER DAYA
# =====================================================

def resource_inputs():

    st.markdown("### Ketersediaan Sumber Daya")

    a, b, c, d = st.columns(4)

    resources["pekerja"] = a.number_input(
        "Pekerja hadir",
        1,
        100,
        int(resources["pekerja"])
    )

    resources["kompor"] = b.number_input(
        "Kompor malam berfungsi",
        0,
        20,
        int(resources["kompor"])
    )

    resources["pompa"] = c.number_input(
        "Pompa air berfungsi",
        0,
        20,
        int(resources["pompa"])
    )

    resources["oven"] = d.number_input(
        "Oven curing berfungsi",
        0,
        20,
        int(resources["oven"])
    )

    st.session_state.sumber_daya = resources


# =====================================================
# FUNGSI MEMBUAT OPERASI PRODUKSI
# =====================================================

def operations_from_orders(order_df):

    rows = []

    for _, order in order_df.iterrows():

        tahapan = prediksi_durasi(
            order["Jenis"],
            order["Kuantitas"]
        )

        for stage, machine, watt, hours, workers in tahapan:

            rows.append({
                "Kode": order["Kode"],
                "Jenis": order["Jenis"],
                "Tahap": stage,
                "Mesin": machine,
                "Daya (Watt)": watt,
                "Durasi (Jam)": hours,
                "Pekerja": workers
            })

    return pd.DataFrame(rows)


# =====================================================
# FUNGSI PERHITUNGAN EKONOMI
# =====================================================

def get_economics(result):

    return hitung_ekonomi(
        orders,
        result,
        tariff,
        resources["pekerja"],
        upah_per_pekerja
    )


# =====================================================
# HALAMAN DASHBOARD
# =====================================================

if page == "Dashboard":

    st.markdown("### Ringkasan Operasional")

    result = st.session_state.hasil_jadwal

    peak = 0
    profit = 0
    status = "Belum dihitung"

    if result is not None and not result.empty:

        profile = buat_profil_beban(
            result,
            work_start,
            work_end
        )

        peak = (
            int(profile["Daya (Watt)"].max())
            if not profile.empty else 0
        )

        economics = get_economics(result)

        profit = economics["Estimasi Profit"]

        status = (
            "AMAN"
            if peak <= safe_watt
            else "MELEBIHI BATAS"
        )

    a, b, c, d = st.columns(4)

    a.metric(
        "Status Keamanan Daya",
        status
    )

    b.metric(
        "Pesanan Aktif",
        len(orders)
    )

    c.metric(
        "Pekerja Hadir",
        f"{resources['pekerja']} orang"
    )

    d.metric(
        "Estimasi Profit",
        f"Rp {profit:,.0f}"
    )

    st.caption(
        f"Batas Watt efektif = {va:,} VA × PF {pf:.2f} "
        f"× margin aman 90% = {safe_watt:,.0f} W."
    )

    if result is None or result.empty:

        st.info(
            "Belum ada jadwal. Buka halaman Jadwal & Energi "
            "untuk membuat rekomendasi."
        )

    else:

        if peak <= safe_watt:
            st.success(
                f"Beban puncak: {peak:,} W dari batas efektif "
                f"{safe_watt:,} W."
            )
        else:
            st.error(
                f"Beban puncak {peak:,} W melewati batas efektif "
                f"{safe_watt:,} W."
            )

        st.dataframe(
            orders,
            use_container_width=True,
            hide_index=True
        )


# =====================================================
# HALAMAN INPUT PRODUKSI
# =====================================================

elif page == "Input Produksi":

    st.markdown("### Panel Input Produksi")

    with st.form("new_order", clear_on_submit=True):

        a, b, c = st.columns(3)

        code = a.text_input(
            "Kode pesanan",
            placeholder="ORD-002"
        )

        kind = b.selectbox(
            "Jenis produksi",
            [
                "Batik Cap",
                "Batik Tulis",
                "Sablon/Printing"
            ]
        )

        qty = c.number_input(
            "Kuantitas",
            1,
            100000,
            100
        )

        d, e, f = st.columns(3)

        unit = d.selectbox(
            "Satuan",
            ["potong", "meter"]
        )

        deadline = e.date_input(
            "Deadline",
            date.today() + timedelta(days=2)
        )

        price = f.number_input(
            "Harga jual per satuan (Rp)",
            0,
            100000000,
            75000,
            5000
        )

        submitted = st.form_submit_button(
            "Tambah Pesanan",
            type="primary",
            use_container_width=True
        )

        if submitted:

            if not code.strip():

                st.error("Kode pesanan wajib diisi.")

            elif code.strip() in st.session_state.pesanan["Kode"].tolist():

                st.error("Kode pesanan sudah digunakan.")

            else:

                new = pd.DataFrame([
                    {
                        "Kode": code.strip(),
                        "Jenis": kind,
                        "Kuantitas": int(qty),
                        "Satuan": unit,
                        "Deadline": deadline,
                        "Harga Jual": int(price)
                    }
                ])

                st.session_state.pesanan = pd.concat(
                    [st.session_state.pesanan, new],
                    ignore_index=True
                )

                st.session_state.hasil_jadwal = None

                st.success("Pesanan ditambahkan.")

                st.rerun()

    st.markdown("### Pesanan Terdaftar")

    st.dataframe(
        st.session_state.pesanan,
        use_container_width=True,
        hide_index=True
    )

    delete = st.selectbox(
        "Hapus pesanan",
        ["—"] + st.session_state.pesanan["Kode"].tolist()
    )

    if st.button("Hapus Pesanan") and delete != "—":

        st.session_state.pesanan = (
            st.session_state.pesanan[
                st.session_state.pesanan["Kode"] != delete
            ].reset_index(drop=True)
        )

        st.session_state.hasil_jadwal = None

        st.rerun()

    st.divider()

    resource_inputs()


# =====================================================
# HALAMAN JADWAL DAN ENERGI
# =====================================================

elif page == "Jadwal & Energi":

    st.markdown("### Pusat Visualisasi Jadwal")

    resource_inputs()

    st.warning(
        "Estimasi durasi masih memakai model demonstrasi dari data sintetis. "
        "Validasi tahapan dan durasi bersama UMKM sebelum dipakai "
        "untuk keputusan operasional."
    )

    if st.button(
        "⚡ Prediksi Durasi dan Buat Jadwal",
        type="primary",
        use_container_width=True
    ):

        if orders.empty:

            st.error("Masukkan minimal satu pesanan.")

        elif work_end <= work_start:

            st.error("Jam selesai harus setelah jam mulai.")

        else:

            result, message = buat_jadwal_produksi(
                operations_from_orders(orders),
                safe_watt,
                resources,
                work_start,
                work_end,
                30
            )

            if result is None:

                st.session_state.hasil_jadwal = None

                st.error(message)

            else:

                st.session_state.hasil_jadwal = result

                st.success(message)

    result = st.session_state.hasil_jadwal

    if result is not None and not result.empty:

        st.markdown("#### Instruksi Kerja")

        st.dataframe(
            result[
                [
                    "Kode",
                    "Tahap",
                    "Mesin",
                    "Mulai",
                    "Selesai",
                    "Daya (Watt)",
                    "Pekerja"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        # GANTT CHART
        plot = result.copy()

        base = datetime.combine(
            date.today(),
            time.min
        )

        plot["Start"] = plot["Mulai Menit"].apply(
            lambda x: base + timedelta(minutes=int(x))
        )

        plot["Finish"] = plot["Selesai Menit"].apply(
            lambda x: base + timedelta(minutes=int(x))
        )

        fig = px.timeline(
            plot,
            x_start="Start",
            x_end="Finish",
            y="Tahap",
            color="Kode",
            hover_data=["Mesin", "Daya (Watt)"],
            template="plotly_white"
        )

        fig.update_yaxes(autorange="reversed")

        fig.update_xaxes(
            tickformat="%H:%M",
            title=""
        )

        fig.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=20, b=10)
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # PROFIL BEBAN LISTRIK
        profile = buat_profil_beban(
            result,
            work_start,
            work_end
        )

        fig2 = px.area(
            profile,
            x="Waktu",
            y="Daya (Watt)",
            template="plotly_white",
            title="Profil Beban Listrik per 30 Menit"
        )

        fig2.add_hline(
            y=safe_watt,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Batas efektif {safe_watt} W"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

        # PERHITUNGAN EKONOMI
        economics = get_economics(result)

        st.markdown("#### Analisis Biaya dan Keuntungan")

        x, y, z, w = st.columns(4)

        x.metric(
            "Energi",
            f"{economics['Energi (kWh)']:.2f} kWh"
        )

        y.metric(
            "Biaya Listrik",
            f"Rp {economics['Biaya Listrik']:,.0f}"
        )

        z.metric(
            "Biaya Gaji",
            f"Rp {economics['Upah Harian']:,.0f}"
        )

        w.metric(
            "Estimasi Profit",
            f"Rp {economics['Estimasi Profit']:,.0f}"
        )

        st.caption(
            f"Upah harian dihitung dari {resources['pekerja']} pekerja "
            f"× Rp {upah_per_pekerja:,.0f} per orang."
        )

        st.caption(
            "Estimasi profit belum mengurangi biaya bahan baku, "
            "pewarna, malam, dan biaya operasional lainnya."
        )

        # DOWNLOAD JADWAL
        st.download_button(
            "Unduh Jadwal CSV",
            result.to_csv(index=False).encode("utf-8-sig"),
            "jadwal_maeco.csv",
            "text/csv"
        )

        st.caption(
            "Untuk mencetak jadwal, gunakan Ctrl + P pada browser."
        )

    else:

        st.info("Jadwal belum dibuat.")


# =====================================================
# HALAMAN SIMULASI SKENARIO
# =====================================================

elif page == "Simulasi Skenario":

    st.markdown("### Simulasi Skenario")

    absent = st.slider(
        "Pekerja tidak masuk",
        0,
        max(0, int(resources["pekerja"]) - 1),
        0
    )

    broken_stove = st.slider(
        "Kompor malam rusak",
        0,
        int(resources["kompor"]),
        0
    )

    broken_pump = st.slider(
        "Pompa air rusak",
        0,
        int(resources["pompa"]),
        0
    )

    broken_oven = st.slider(
        "Oven curing rusak",
        0,
        int(resources["oven"]),
        0
    )

    if st.button(
        "Jalankan Simulasi",
        type="primary"
    ):

        if orders.empty:

            st.error("Belum ada pesanan.")

        else:

            simulated = {
                "pekerja": resources["pekerja"] - absent,
                "kompor": resources["kompor"] - broken_stove,
                "pompa": resources["pompa"] - broken_pump,
                "oven": resources["oven"] - broken_oven
            }

            result, message = buat_jadwal_produksi(
                operations_from_orders(orders),
                safe_watt,
                simulated,
                work_start,
                work_end,
                30
            )

            if result is None:

                st.error(
                    "Skenario tidak dapat dijadwalkan: " + message
                )

            else:

                st.success("Jadwal skenario berhasil dihitung.")

                st.dataframe(
                    result,
                    use_container_width=True,
                    hide_index=True
                )

                st.download_button(
                    "Unduh Jadwal Skenario",
                    result.to_csv(index=False).encode("utf-8-sig"),
                    "jadwal_skenario.csv",
                    "text/csv"
                )


# =====================================================
# FOOTER
# =====================================================

st.markdown(
    """
    <div class="footer">
        MAECO • Prototype Hackathon UNS • Data awal simulasi
    </div>
    """,
    unsafe_allow_html=True
)
