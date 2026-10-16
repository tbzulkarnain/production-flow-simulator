import time
import pandas as pd
import plotly.express as px
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Batch Flow vs One-Piece Flow Simulator",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 Production Flow Simulator: Batch vs. One-Piece Flow")
st.markdown(
    """
Aplikasi interaktif untuk memvisualisasikan dan membandingkan performa lini produksi antara **Batch Flow** dan **One-Piece Flow** berdasarkan stasiun kerja, *cycle time*, dan ukuran batch.
"""
)

# --- SIDEBAR: KONFIGURASI PARAMETER ---
st.sidebar.header("⚙️ Pengaturan Parameter")

# 1. Parameter Order & Batch
total_order = st.sidebar.number_input(
    "Total Order (Pcs / Unit)", min_value=1, max_value=100, value=10, step=1
)
batch_size = st.sidebar.number_input(
    "Ukuran Batch (untuk Batch Flow)",
    min_value=1,
    max_value=total_order,
    value=5,
    step=1,
)
sim_speed = st.sidebar.slider(
    "Kecepatan Animasi Simulasi (detik/step)",
    min_value=0.05,
    max_value=1.0,
    value=0.2,
    step=0.05,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ Stasiun Kerja & Cycle Time")
st.sidebar.markdown(
    "Atur nama proses dan waktu siklus (*cycle time* dalam detik) per unit untuk setiap stasiun."
)

# 2. Tabel Dinamis untuk Stasiun Kerja
default_stations = pd.f_data = pd.DataFrame(
    {
        "Nama Proses": ["1. Cutting", "2. Sewing", "3. Assembly", "4. Packing"],
        "Cycle Time (detik)": [2, 3, 2, 1],
    }
)

stations_df = st.data_editor(
    default_stations, num_rows="dynamic", key="station_editor"
)

# Validasi input stasiun
if stations_df.empty or any(stations_df["Cycle Time (detik)"] <= 0):
    st.error(
        "Harap masukkan minimal 1 stasiun kerja dengan Cycle Time > 0 detik."
    )
    st.stop()

stations = stations_df["Nama Proses"].tolist()
cycle_times = stations_df["Cycle Time (detik)"].tolist()
num_stations = len(stations)

# --- TOMBOL UTAMA SIMULASI ---
col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    run_sim = st.button(
        "▶ Jalankan Simulasi", type="primary", use_container_width=True
    )


# --- FUNGSI SIMULASI LOGIC ---
def calculate_batch_flow_schedule(
    total_qty, b_size, c_times
):  # pylint: disable=unused-argument
    """Menghitung metrik & timeline untuk Batch Flow"""
    # Jumlah batch
    import math

    num_batches = math.ceil(total_qty / b_size)

    # Sederhana: estimasi lead time total dan WIP
    # Batch flow menumpuk WIP di tengah
    per_station_time = sum(c_times)
    total_lead_time = (
        per_station_time * b_size * (num_batches)
    )  # Estimasi kasar logika batch
    avg_wip = total_qty * (num_stations / 2)  # WIP cenderung tinggi
    return total_lead_time, avg_wip, num_batches


def calculate_opf_schedule(total_qty, c_times):
    """Menghitung metrik & timeline untuk One-Piece Flow"""
    # Unit pertama selesai setelah lewat semua stasiun pertama kali
    first_piece_time = sum(c_times)
    # Unit berikutnya selesai setiap max(cycle_time)
    max_ct = max(c_times)
    total_lead_time = first_piece_time + (total_qty - 1) * max_ct
    avg_wip = num_stations  # WIP sangat rendah dan konstan
    return total_lead_time, avg_wip, first_piece_time


# --- EKsekusi JIKA TOMBOL DIKLIK / STATE AKTIF ---
if run_sim:
    st.markdown("---")
    st.subheader("🔴 vs 🟢 Live Simulation Comparison")

    # Layout Side-by-Side untuk Visualisasi Jalur
    col_batch_view, col_opf_view = st.columns(2)

    with col_batch_view:
        st.markdown("### 📦 **Batch Flow (Ukuran Batch: {})**".format(batch_size))
        batch_placeholder = st.empty()

    with col_opf_view:
        st.markdown("### ⚡ **One-Piece Flow (Single Piece)**")
        opf_placeholder = st.empty()

    # Simulasi Langkah Step-by-Step (Visual Emoji Animation)
    # Kita simulasikan pergerakan unit/batch secara visual sederhana di Streamlit
    import math

    num_batches = math.ceil(total_order / batch_size)

    # --- Simulasi Batch Flow Visual Loop ---
    for step in range(
        1, max(6, num_stations + num_batches + 2)
    ):  # Batasi iterasi animasi agar smooth
        b_text = ""
        for s_idx, s_name in enumerate(stations):
            # Simulasi posisi barang di batch flow
            if s_idx < step:
                b_text += f"- **{s_name}**: 📦 Sedang proses 1 Batch penuh\n"
            else:
                b_text += f"- **{s_name}**: ⏳ Menunggu antrean batch\n"

        batch_placeholder.markdown(b_text)

        # --- Simulasi One-Piece Flow Visual Loop ---
        o_text = ""
        for s_idx, s_name in enumerate(stations):
            if s_idx < step:
                o_text += (
                    f"- **{s_name}**: 🟢 Unit 1, 2, 3 mengalir kontinu\n"
                )
            else:
                o_text += f"- **{s_name}**: ⏳ Standby\n"

        opf_placeholder.markdown(o_text)
        time.sleep(sim_speed)

    # --- HITUNG HASIL AKHIR ---
    lt_batch, wip_batch, _ = calculate_batch_flow_schedule(
        total_order, batch_size, cycle_times
    )
    lt_opf, wip_opf, first_pc_opf = calculate_opf_schedule(
        total_order, cycle_times
    )

    st.markdown("---")
    st.subheader("📊 Hasil Perbandingan & Metrik Akhir")

    # Tampilkan Metrik Side-by-Side
    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown("#### 📦 Metode: Batch Flow")
        st.metric(
            label="Total Lead Time (Waktu Selesai Semua)",
            value=f"{lt_batch} detik",
        )
        st.metric(
            label="Rata-rata WIP (Work in Process)",
            value=f"{wip_batch:.1f} unit",
            delta="Tinggi (Banyak Tertahan)",
            delta_value="inverse",
        )
        st.info(
            "⚠️ **Karakteristik:** Terjadi penumpukan barang di depan mesin (*bottleneck*), barang pertama baru selesai di waktu yang lama."
        )

    with m_col2:
        st.markdown("#### ⚡ Metode: One-Piece Flow")
        st.metric(
            label="Total Lead Time (Waktu Selesai Semua)",
            value=f"{lt_opf} detik",
            delta=f"-{lt_batch - lt_opf} detik lebih cepat",
        )
        st.metric(
            label="Rata-rata WIP (Work in Process)",
            value=f"{wip_opf:.1f} unit",
            delta="Sangat Rendah (Lean)",
        )
        st.success(
            f"✨ **Karakteristik:** Unit pertama selesai dalam **{first_pc_opf} detik** saja! Aliran mulus tanpa antrean menumpuk."
        )

    # --- GRAFIK PERBANDINGAN PLOTLY ---
    st.markdown("---")
    st.subheader("📈 Grafik Perbandingan Metrik Utama")

    comparison_data = pd.DataFrame(
        {
            "Metode": ["Batch Flow", "One-Piece Flow"],
            "Total Lead Time (detik)": [lt_batch, lt_opf],
            "Rata-rata WIP (Unit)": [wip_batch, wip_opf],
        }
    )

    fig_melted = comparison_data.melt(
        id_vars="Metode", var_name="Metrik", value_name="Nilai"
    )

    fig = px.bar(
        fig_melted,
        x="Metrik",
        y="Nilai",
        color="Metode",
        barmode="group",
        text="Nilai",
        title="Perbandingan Performa: Batch Flow vs One-Piece Flow",
        color_discrete_map={
            "Batch Flow": "#ff7f0e",
            "One-Piece Flow": "#2ca02c",
        },
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode="hide")

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info(
        "👆 Silakan atur parameter stasiun kerja di sidebar, lalu klik tombol **Jalankan Simulasi** di atas untuk melihat visualisasinya."
    )
