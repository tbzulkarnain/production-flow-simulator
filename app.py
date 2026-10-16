import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Production Flow Simulator: Batch vs One-Piece Flow",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 Production Flow Simulator: Batch vs. One-Piece Flow")
st.markdown(
    """
Aplikasi simulasi interaktif untuk memvisualisasikan perbandingan alur produksi **Batch Production** 
dan **One-Piece Flow** secara langsung (*real-time animated schematic*).
"""
)

# --- SIDEBAR: KONTROL SIMULASI & PARAMETER ---
st.sidebar.header("⚙️ Pengaturan Parameter Produksi")

# 1. Parameter Order & Batch Size
total_qty = st.sidebar.number_input(
    "Total Order (Unit)", min_value=1, max_value=50, value=6, step=1
)
batch_size = st.sidebar.number_input(
    "Ukuran Batch (Batch Flow)",
    min_value=1,
    max_value=total_qty,
    value=3,
    step=1,
)
sim_speed = st.sidebar.slider(
    "Kecepatan Simulasi", min_value=0.5, max_value=3.0, value=1.0, step=0.1
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ Stasiun Kerja & Cycle Time")
st.sidebar.markdown(
    "Atur nama proses dan *cycle time* (dalam detik/menit) per unit:"
)

# 2. Tabel Stasiun Kerja Dinamis
default_stations = pd.DataFrame(
    {
        "Nama Stasiun": ["Station 1", "Station 2", "Station 3"],
        "Batch CT (menit)": [10, 10, 10],
        "OPF CT (menit)": [1, 1, 1],
    }
)

edited_stations = st.data_editor(
    default_stations, num_rows="dynamic", key="station_editor"
)

# Validasi input
if edited_stations.empty:
    st.error("Harap masukkan minimal 1 stasiun kerja!")
    st.stop()

stations_data = edited_stations.to_dict(orient="records")

# --- MENYUSUN KODE HTML / JS ANIMASI SKEMATIK ---
html_code = f"""
<!DOCTYPE html>
<html lang="id">
<head>

  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    :root {{
      --bg-color: #f8fafc;
      --card-bg: #ffffff;
      --border-color: #e2e8f0;
      --primary: #4f46e5;
      --purple-block: #6366f1;
      --purple-dark: #4338ca;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --success: #10b981;
      --warning: #f59e0b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }}
    body {{ background: var(--bg-color); color: var(--text-main); padding: 10px; }}
    
    .sim-container {{
      display: flex;
      flex-direction: column;
      gap: 15px;
    }}
    .sim-panel {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 15px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .panel-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      border-bottom: 2px solid #f1f5f9;
      padding-bottom: 8px;
    }}
    .panel-title {{
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    
    canvas {{
      width: 100%;
      height: 220px;
      background: #fafafa;
      border-radius: 8px;
      border: 1px dashed #cbd5e1;
      display: block;
    }}
    
    .stats-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
      margin-top: 10px;
    }}
    .stat-card {{
      background: #f1f5f9;
      padding: 10px;
      border-radius: 8px;
      text-align: center;
    }}
    .stat-val {{
      font-size: 1.2rem;
      font-weight: 700;
      color: var(--primary);
    }}
    .stat-lbl {{
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    
    .controls {{
      display: flex;
      gap: 10px;
      margin-bottom: 15px;
    }}
    .btn {{
      padding: 8px 16px;
      border-radius: 6px;
      border: none;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .btn-primary {{ background: var(--primary); color: white; }}
    .btn-primary:hover {{ opacity: 0.9; }}
    .btn-secondary {{ background: #e2e8f0; color: #334155; }}

</head>
<body>

  <div class="controls">
    <button class="btn btn-primary" id="startBtn">▶ Jalankan / Reset Simulasi</button>
  </div>

  <div class="sim-container">
    <!-- PANEL BATCH FLOW -->
    <div class="sim-panel">
      <div class="panel-header">
        <div class="panel-title">📦 Batch Production (Batch Size: <span id="batchSizeLbl">{batch_size}</span>)</div>
        <div style="font-size: 0.85rem; color: var(--text-muted);" id="batchTimeElapsed">Waktu Selesai: 0 min</div>
      </div>
      <canvas id="batchCanvas"></canvas>
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-val" id="batchWip">0 unit</div>
          <div class="stat-lbl">Rata-rata WIP</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" id="batchFirstPiece">-</div>
          <div class="stat-lbl">First Piece Out</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" id="batchTotalTime">-</div>
          <div class="stat-lbl">Total Lead Time</div>
        </div>
      </div>
    </div>

    <!-- PANEL ONE-PIECE FLOW -->
    <div class="sim-panel">
      <div class="panel-header">
        <div class="panel-title">⚡ One-Piece Production (Single-Piece Flow)</div>
        <div style="font-size: 0.85rem; color: var(--text-muted);" id="opfTimeElapsed">Waktu Selesai: 0 min</div>
      </div>
      <canvas id="opfCanvas"></canvas>
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-val" id="opfWip" style="color: var(--success);">0 unit</div>
          <div class="stat-lbl">Rata-rata WIP</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" id="opfFirstPiece" style="color: var(--success);">-</div>
          <div class="stat-lbl">First Piece Out</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" id="opfTotalTime" style="color: var(--success);">-</div>
          <div class="stat-lbl">Total Lead Time</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const totalQty = {total_qty};
    const batchSize = {batch_size};
    const simSpeed = {sim_speed};
    const stationsData = {stations_data};

    // Responsive Canvas
    function setupCanvas(canvasId) {{
      const canvas = document.getElementById(canvasId);
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      const ctx = canvas.getContext('2d');
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
      return {{ canvas, ctx, width: rect.width, height: rect.height }};
    }}

    // State Simulasi
    let isRunning = false;
    let simTime = 0;
    let animFrame = null;

    // Draw Operator Desk & Schematic
    function drawDiagram(ctx, width, height, stations, isBatch, currentItems) {{
      ctx.clearRect(0, 0, width, height);

      const numStations = stations.length;
      const margin = 60;
      const usableWidth = width - (margin * 2);
      const stepX = usableWidth / (numStations > 1 ? (numStations - 1) : 1);
      const centerY = height / 2;

      // Draw Stations & Connectors (Arrows)
      stations.forEach((st, idx) => {{
        const x = margin + (idx * stepX);

        // Panah Penghubung
        if (idx < numStations - 1) {{
          const nextX = margin + ((idx + 1) * stepX);
          ctx.beginPath();
          ctx.strokeStyle = "#cbd5e1";
          ctx.lineWidth = 3;
          ctx.moveTo(x + 45, centerY);
          ctx.lineTo(nextX - 45, centerY);
          ctx.stroke();

          // Arrow head
          ctx.beginPath();
          ctx.fillStyle = "#cbd5e1";
          ctx.arc(nextX - 45, centerY, 5, 0, Math.PI * 2);
          ctx.fill();
        }}

        // Meja & Operator Desk
        ctx.fillStyle = "#ffffff";
        ctx.strokeStyle = "#475569";
        ctx.lineWidth = 2;
        ctx.strokeRect(x - 35, centerY - 25, 70, 50);
        ctx.fillRect(x - 35, centerY - 25, 70, 50);

        // Operator (Top view circle/head)
        ctx.beginPath();
        ctx.arc(x, centerY + 10, 10, 0, Math.PI * 2);
        ctx.fillStyle = "#1e293b";
        ctx.fill();

        ctx.beginPath();
        ctx.arc(x, centerY + 20, 15, Math.PI, Math.PI * 2);
        ctx.strokeStyle = "#1e293b";
        ctx.lineWidth = 3;
        ctx.stroke();

        // Station Label & Cycle Time Label
        ctx.fillStyle = "#0f172a";
        ctx.font = "bold 12px system-ui";
        ctx.textAlign = "center";
        ctx.fillText(st["Nama Stasiun"], x, centerY + 50);

        const ctVal = isBatch ? st["Batch CT (menit)"] : st["OPF CT (menit)"];
        ctx.fillStyle = "#64748b";
        ctx.font = "11px system-ui";
        ctx.fillText(ctVal + " min", x, centerY - 35);
      }});

      // Draw Purple Work Blocks (WIP / Products)
      currentItems.forEach(item => {{
        ctx.fillStyle = "#6366f1";
        ctx.fillRect(item.x, item.y, 14, 8);
        ctx.strokeStyle = "#4338ca";
        ctx.lineWidth = 1;
        ctx.strokeRect(item.x, item.y, 14, 8);
      }});
    }}

    function runSimulationLoop() {{
      const batchSys = setupCanvas('batchCanvas');
      const opfSys = setupCanvas('opfCanvas');

      function animate() {{
        simTime += 0.05 * simSpeed;

        // Visual Mock Items Position Generator based on SimTime
        const batchItems = [];
        const opfItems = [];

        // Generasi visual tumpukan balok berdasarkan tipe alur
        stationsData.forEach((st, idx) => {{
          const stepX = (batchSys.width - 120) / (stationsData.length - 1 || 1);
          const stX = 60 + (idx * stepX);
          const centerY = batchSys.height / 2;

          // Batch flow items (Menumpuk banyak di samping meja)
          if (simTime > idx * 2 && simTime < (idx + 1) * 8) {{
            for(let b=0; b<batchSize; b++) {{
              batchItems.push({{ x: stX - 55 + (b % 2)*16, y: centerY - 15 + Math.floor(b/2)*10 }});
            }}
          }}

          // One-piece flow items (Mengalir 1 per 1 mulus)
          if (simTime > idx * 1.5 && simTime < (idx + 1) * 4) {{
            opfItems.push({{ x: stX - 7, y: centerY - 20 }});
          }}
        }});

        drawDiagram(batchSys.ctx, batchSys.width, batchSys.height, stationsData, true, batchItems);
        drawDiagram(opfSys.ctx, opfSys.width, opfSys.height, stationsData, false, opfItems);

        // Calc metrics display update
        const bLeadTime = stationsData.reduce((a,b) => a + (b["Batch CT (menit)"] * batchSize), 0);
        const oLeadTime = stationsData.reduce((a,b) => a + b["OPF CT (menit)"], 0) + (totalQty - 1) * Math.max(...stationsData.map(s=>s["OPF CT (menit)"]));

        document.getElementById('batchTotalTime').innerText = bLeadTime + " min";
        document.getElementById('batchFirstPiece').innerText = (stationsData[0]["Batch CT (menit)"] * batchSize) + " min";
        document.getElementById('batchWip').innerText = (totalQty * 0.8).toFixed(0) + " unit";

        document.getElementById('opfTotalTime').innerText = oLeadTime + " min";
        document.getElementById('opfFirstPiece').innerText = stationsData.reduce((a,b) => a + b["OPF CT (menit)"], 0) + " min";
        document.getElementById('opfWip').innerText = "1 unit";

        document.getElementById('batchTimeElapsed').innerText = "Estimasi Selesai: " + bLeadTime + " min";
        document.getElementById('opfTimeElapsed').innerText = "Estimasi Selesai: " + oLeadTime + " min";

        if (simTime < 15 && isRunning) {{
          animFrame = requestAnimationFrame(animate);
        }}
      }}

      isRunning = true;
      simTime = 0;
      if (animFrame) cancelAnimationFrame(animFrame);
      animate();
    }}

    document.getElementById('startBtn').addEventListener('click', runSimulationLoop);
    window.addEventListener('load', runSimulationLoop);
  </script>
</body>
</html>
"""

# Tampilkan Komponen Visualisasi di Streamlit
components.html(html_code, height=750, scrolling=True)
