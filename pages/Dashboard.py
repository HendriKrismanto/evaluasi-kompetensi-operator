import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. PROTEKSI HALAMAN (TAMBAHKAN DI PALING ATAS) ---
# Mengecek apakah user sudah login sebagai admin dari halaman utama
if "role" not in st.session_state or st.session_state.get("role") != "admin":
    st.set_page_config(page_title="Akses Ditolak", page_icon="🚫")
    st.error("🚫 Akses Ditolak. Halaman ini hanya dapat diakses oleh Admin.")
    st.info("Silakan login kembali di halaman utama dengan password Admin.")
    st.stop() # Menghentikan seluruh kode di bawah agar tidak jalan

# --- 2. JIKA ADMIN, LANJUTKAN SKRIP ASLI ANDA ---
st.set_page_config(page_title="Dashboard Rekap", layout="wide")

st.title("📊 Dashboard Monitoring Kompetensi")
st.divider()

# --- 3. KONEKSI & LOAD DATA ---
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    url = st.secrets.connections.gsheets.spreadsheet
    # Konversi URL ke format export CSV
    csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit', '/export?format=csv')
    
    try:
       # 1. Tarik Data
        df = pd.read_csv(csv_url)
        
        # 2. SINKRONISASI NAMA KOLOM (SESUAI DATA ANDA)
        # Kita ubah nama kolom dari Sheets ke nama standar agar grafik jalan
        mapping = {
            'Skor_Work Element': 'Work Element',
            'Skor_Pengetahuan Proses': 'Pengetahuan Proses',
            'Skor_Pengetahuan Produk': 'Pengetahuan Produk',
            'Skor_Jenis NG': 'Jenis NG',
            'Skor_Efek NG': 'Efek NG',
            'UrutanRanking': 'Urutan_Ranking',
            'FokusTraining': 'Fokus_Training'
        }
        df.rename(columns=mapping, inplace=True)
        
        # 3. DEFINISI KATEGORI UNTUK GRAFIK
        categories = ['Work Element', 'Pengetahuan Proses', 'Pengetahuan Produk', 'Jenis NG', 'Efek NG']

        # --- MULAI VISUALISASI ---
        if not df.empty:
            # Poin 1: Total Data
            st.metric(label="Total Operator Terdaftar", value=f"{len(df)} Orang")
            st.divider()

            # Layout Kolom
            row1_col1, row1_col2 = st.columns(2)

            with row1_col1:
                # Poin 2: Grafik Batang Peserta per Line
                st.subheader("🏢 Peserta per Line")
                line_counts = df['Line'].value_counts().reset_index()
                line_counts.columns = ['Line', 'Jumlah']
                fig_line = px.bar(line_counts, x='Line', y='Jumlah', color='Line', text_auto=True)
                st.plotly_chart(fig_line, use_container_width=True)

            with row1_col2:
                # Poin 3: Radar Chart Rata-rata Skor (Avg)
                st.subheader("🎯 Profil Kompetensi Tim (Avg)")
                # Hitung rata-rata skor
                avg_scores = df[categories].mean().tolist()
                radar_values = avg_scores + [avg_scores[0]]
                radar_cats = categories + [categories[0]]
                
                fig_radar = go.Figure(go.Scatterpolar(r=radar_values, theta=radar_cats, fill='toself', line_color='teal'))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[-12, 12])), height=300, margin=dict(l=30, r=30, t=30, b=30))
                st.plotly_chart(fig_radar, use_container_width=True)

            st.divider()

            # Poin 4: Pareto Training
            st.subheader("📉 Pareto Rekomendasi Training")
            if 'Fokus_Training' in df.columns:
                # Bersihkan data dari nilai kosong (NaN) sebelum diproses
                all_text = df['Fokus_Training'].fillna("").str.cat(sep=' | ')
                counts = {cat: all_text.count(cat) for cat in categories}
                pareto_df = pd.DataFrame(list(counts.items()), columns=['Kategori', 'Count']).sort_values(by='Count', ascending=False)
                
                fig_pareto = px.bar(pareto_df, x='Kategori', y='Count', title="Frekuensi Kelemahan per Kategori", color_discrete_sequence=['indianred'])
                st.plotly_chart(fig_pareto, use_container_width=True)
            
            st.divider()

            # Poin 5: Tabel Database
            st.subheader("📋 Tabel Database Lengkap")
            # Menampilkan kolom penting saja di tabel utama
            st.dataframe(df[['Nama', 'NIK', 'Line', 'Team', 'Urutan_Ranking', 'Fokus_Training']], use_container_width=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
        st.write("Cek Nama Kolom Sheets Anda:", df.columns.tolist())

