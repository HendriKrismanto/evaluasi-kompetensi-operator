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

            # Skor & ranking kompetensi
            st.subheader("🏆 Skor & Ranking Kompetensi Tim (Avg)")
            
            # 1. Hitung rata-rata skor tim untuk setiap kategori
            avg_scores_dict = df[categories].mean().to_dict()
            
            # 2. Urutkan dari yang tertinggi untuk Ranking
            sorted_avg = sorted(avg_scores_dict.items(), key=lambda x: x[1], reverse=True)
            
            # 3. Buat string Ranking untuk tampilan
            ranking_team_str = ", ".join([f"{c} ({s:.1f} pts)" for c, s in sorted_avg])
            st.info(f"**Urutan Kekuatan Tim:** {ranking_team_str}")
            
            # 4. Tampilkan Metrics Persentase (Sama dengan tampilan operator)
            cols_metrics = st.columns(len(sorted_avg))
            for i, (cat, score) in enumerate(sorted_avg):
                # Rumus persentase yang sama: ((score + 12) / 24) * 100
                persentase_avg = int(((score + 12) / 24) * 100)
                cols_metrics[i].metric(
                    label=cat, 
                    value=f"{persentase_avg}%", 
                    delta=f"{score:.1f} pts avg"
                )

            st.divider()

            # Poin 4: Pareto Training
            # --- Poin 4: Pareto Rekomendasi Training (Berdasarkan Pernyataan) ---
            st.subheader("📉 Top 10 Materi Training Paling Dibutuhkan")
            
            if 'Fokus_Training' in df.columns:
                # 1. Ambil semua teks, bersihkan, dan pecah berdasarkan separator | atau /
                # Kita asumsikan formatnya: [Kategori]: Pernyataan1/Pernyataan2 | [Kategori]: ...
                all_text = df['Fokus_Training'].fillna("").str.cat(sep=' | ')
                
                # Membersihkan teks dari label kategori [Kategori]: agar fokus ke pernyataannya
                import re
                clean_text = re.sub(r'\[.*?\]:', '', all_text)
                
                # Pecah menjadi list pernyataan individu
                raw_items = [item.strip() for item in clean_text.replace('|', '/').split('/') if item.strip()]
                
                if raw_items:
                    # 2. Hitung frekuensi tiap pernyataan
                    item_counts = pd.Series(raw_items).value_counts().reset_index()
                    item_counts.columns = ['Materi_Training', 'Jumlah_Operator']
                    
                    # Ambil 10 besar saja agar grafik tidak terlalu penuh
                    top_10_training = item_counts.head(10)

                    # 3. Visualisasi Grafik Batang Horizontal (lebih mudah dibaca untuk teks panjang)
                    fig_pareto = px.bar(
                        top_10_training, 
                        y='Materi_Training', 
                        x='Jumlah_Operator',
                        orientation='h',
                        title="Materi yang Paling Sering Muncul sebagai Kelemahan",
                        text_auto=True,
                        # color='Jumlah_Operator',
                        # color_continuous_scale='Reds'
                    )
                    
                    fig_pareto.update_layout(
                        yaxis={'categoryorder':'total ascending'},
                        # showlegend=False,
                        height=500,
                        margin=dict(l=50, r=20, t=50, b=50)
                    )
                    st.plotly_chart(fig_pareto, use_container_width=True)
                else:
                    st.info("Belum ada data kelemahan spesifik yang tercatat.")
            
            st.divider()

            # Poin 5: Tabel Database
            st.subheader("📋 Tabel Database Lengkap")
            # Menampilkan kolom penting saja di tabel utama
            st.dataframe(df[['Nama', 'NIK', 'Line', 'Team', 'Urutan_Ranking', 'Fokus_Training']], use_container_width=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
        st.write("Cek Nama Kolom Sheets Anda:", df.columns.tolist())

