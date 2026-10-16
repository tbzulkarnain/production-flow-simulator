import math
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
Aplikasi interaktif untuk memvisualisasikan dan membandingkan performa lini produksi antara **Batch Flow** dan **One-Piece Flow** menggunakan animasi grafik interaktif.
"""
)

# --- SIDEBAR: KONFIGURASI PARAMETER ---
st.sidebar.header("⚙️ Pengaturan Parameter")

total_order = st.sidebar.number_input(
    "Total Order (Pcs / Unit)", min_value=1, max_value=50, value=6, step=1
)
batch_size = st.sidebar.number_input(
    "Ukuran Batch (untuk Batch Flow)",
    min_value=1,
    max_value=total_order,
    value=3,
    step=1,
)
sim_speed = st.sidebar.slider(
    "Kecepatan Animasi (detik)",
    min_value=0.1,
    max_value=1.0,
    value=0.3,
    step=0.1,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ Stasiun Kerja & Cycle Time")

default_stations = pd.DataFrame(
    {
        "Nama Proses": ["1. Cutting", "2. Sewing", "3. Assembly", "4. Packing"],
        "Cycle Time (detik)": [2, 3, 2, 1],
    }
)

stations_df = st.data_editor(
    default_stations, num_rows="dynamic", key="station_editor"
)

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


# --- FUNGSI PERHITUNGAN LOGIC ---
def calculate_metrics(total_qty, b_size, c_times):
    num_batches = math.ceil(total_qty / b_size)
    per_station_time = sum(c_times)
    lt_batch = per_station_time * b_size * num_batches
    wip_batch = total_qty * (num_stations / 2)

    first_pc_opf = sum(c_times)
    max_ct = max(c_times)
    lt_opf = first_pc_opf + (total_qty - 1) * max_ct
    wip_opf = num_stations

    return lt_batch, wip_batch, lt_opf, wip_opf, first_pc_opf


# --- EKSEKUSI JIKA TOMBOL DIKLIK ---
if run_sim:
    st.markdown("---")
    st.subheader("📊 Live Animated Visual Simulation")
    st.markdown(
        "Grafik di bawah ini memvisualisasikan pergerakan unit produk dari **Stasiun ke Stasiun** seiring berjalannya waktu simulasi."
    )

    # Placeholder untuk grafik animasi
    chart_placeholder = st.empty()

    # Mempersiapkan data frame untuk animasi Plotly Scatter
    # Kita buat simulasi frame pergerakan waktu
    num_batches = math.ceil(total_order / batch_size)
    max_steps = max(10, num_stations + total_order + 3)

    anim_data = []

    # Generasi data posisi unit untuk Batch Flow & One-Piece Flow per detik/step waktu
    for t in range(max_steps):
        # 1. Batch Flow Simulation Data
        for u in range(1, total_order + 1):
            batch_id = (u - 1) // batch_size
            # Batch bergerak perlahan stasiun demi stasiun
            stasiun_pos = min(
                num_stations - 1, max(0, t - (batch_id * sum(cycle_times) // 2))
            )
            anim_data.append(
                {
                    "Waktu (detik)": t,
                    "Unit": f"Unit {u}",
                    "Stasiun": stations[stasiun_pos],
                    "Metode": "Batch Flow",
                    "Posisi_Index": stasiun_pos,
                }
            )

        # 2. One-Piece Flow Simulation Data
        for u in range(1, total_order + 1):
            # One-piece mengalir cepat satu per satu
            stasiun_pos = min(num_stations - 1, max(0, t - (u - 1)))
            anim_data.append(
                {
                    "Waktu (detik)": t,
                    "Unit": f"Unit {u}",
                    "Stasiun": stations[stasiun_pos],
                    "Metode": "One-Piece Flow",
                    "Posisi_Index": stasiun_pos,
                }
            )

    df_anim = pd.DataFrame(anim_data)

    # Jalankan animasi frame demi frame di Streamlit menggunakan Plotly
    for t_step in range(max_steps):
        df_filtered = df_anim[df_anim["Waktu (detik)"] == t_step]

        fig = px.scatter(
            df_filtered,
            x="Stasiun",
            y="Unit",
            color="Metode",
            symbol="Metode",
            title=f"Simulasi Produksi pada Detik ke-{t_step}",
            range_x=[-0.5, num_stations - 0.5],
            range_y=[-0.5, total_order + 0.5],
            size_max=15,
            color_discrete_map={
                "Batch Flow": "#ff7f0e",
                "One-Piece Flow": "#2ca02c",
            },
        )
        fig.update_traces(marker=dict(size=14))
        fig.update_layout(transition_duration=100)

        chart_placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(sim_speed)

    # --- HITUNG HASIL AKHIR & METRIK ---
    lt_batch, wip_batch, lt_opf, wip_opf, first_pc_opf = calculate_metrics(
        total_order, batch_size, cycle_times
    )

    st.markdown("---")
    st.subheader("📈 Hasil Perbandingan & Metrik Akhir")

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown("#### 📦 Metode: Batch Flow")
        st.metric(
            label="Total Lead Time", value=f"{lt_batch} detik / unit selesai"
        )
        st.metric(
            label="Rata-rata WIP (Work in Process)",
            value=f"{wip_batch:.1f} unit",
            delta="Tinggi (Menumpuk)",
            delta_color="inverse",
        )
        st.info(
            "⚠️ Barang tertahan lama dalam batch sebelum bisa diproses ke stasiun berikutnya."
        )

    with m_col2:
        st.markdown("#### ⚡ Metode: One-Piece Flow")
        st.metric(
            label="Total Lead Time",
            value=f"{lt_opf} detik",
            delta=f"-{lt_batch - lt_opf} detik lebih cepat",
        )
        st.metric(
            label="Rata-rata WIP (Work in Process)",
            value=f"{wip_opf:.1f} unit",
            delta="Sangat Rendah (Lean)",
        )
        st.success(
            f"✨ Unit pertama selesai hanya dalam **{first_pc_opf} detik**! Aliran mulus tanpa antrean."
        )

else:
    st.info(
        "👆 Atur parameter di sidebar, lalu klik tombol **Jalankan Simulasi** untuk melihat animasi pergerakan produk secara visual."
    )
