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
        # Load data dengan cache dibersihkan tiap buka (ttl=0)
        df = pd.read_csv(csv_url)

        # --- TAMBAHKAN BLOK PEMBERSIHAN KOLOM INI ---
        # Kita cari kolom yang mengandung kata kunci kategori
        mapping = {
            'Work Element': 'Work Element',
            'Pengetahuan Proses': 'Pengetahuan Proses',
            'Pengetahuan Produk': 'Pengetahuan Produk',
            'Jenis NG': 'Jenis NG',
            'Efek NG': 'Efek NG'
        }
        
        # Loop untuk mengganti nama kolom yang panjang dari Google Form
        for key in mapping.keys():
            # Cari kolom yang namanya mirip/mengandung kata kunci kategori
            cols = [c for c in df.columns if key in c]
            if cols:
                df.rename(columns={cols[0]: key}, inplace=True)
        
        if not df.empty:
            # --- Poin 1: Total Data Masuk (Metrics) ---
            total_data = len(df)
            st.metric(label="Total Operator Terdaftar", value=f"{total_data} Orang")
            st.divider()

            # Layout Kolom untuk Grafik
            row1_col1, row1_col2 = st.columns(2)

            with row1_col1:
                # --- Poin 2: Grafik Batang Peserta per Line ---
                st.subheader("🏢 Peserta per Line")
                line_counts = df['Line'].value_counts().reset_index()
                line_counts.columns = ['Line', 'Jumlah']
                fig_line = px.bar(line_counts, x='Line', y='Jumlah', 
                                  color='Line', text_auto=True,
                                  color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_line, use_container_width=True)

            with row1_col2:
                # --- Poin 3: Radar Chart Rata-rata Skor per Kategori ---
                st.subheader("🎯 Profil Kompetensi Tim (Avg)")
                
                # List kategori sesuai BANK_SOAL
                categories = ['Work Element', 'Pengetahuan Proses', 'Pengetahuan Produk', 'Jenis NG', 'Efek NG']
                
                # Hitung rata-rata skor (-12 s/d 12)
                avg_scores = df[categories].mean().tolist()
                
                # Menutup lingkaran radar (tambah titik awal ke akhir)
                radar_values = avg_scores + [avg_scores[0]]
                radar_cats = categories + [categories[0]]
                
                # Buat Radar Chart menggunakan Graph Objects (sama seperti di hal. utama)
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=radar_values,
                    theta=radar_cats,
                    fill='toself',
                    line_color='teal',
                    name='Rata-rata Tim'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[-12, 12] # Rentang skor ideal 12 blok
                        )
                    ),
                    showlegend=False,
                    height=400,
                    margin=dict(l=40, r=40, t=20, b=20)
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)

            st.divider()

            # --- Poin 4: Grafik Batang Pareto Rekomendasi Training ---
            st.subheader("📉 Pareto Rekomendasi Training (Top Priority)")
            if 'Fokus_Training' in df.columns:
                # Menggabungkan semua teks training dan menghitung frekuensi kategori
                all_text = df['Fokus_Training'].str.cat(sep=' | ')
                counts = {cat: all_text.count(cat) for cat in categories}
                
                # Buat DataFrame Pareto
                pareto_df = pd.DataFrame(list(counts.items()), columns=['Kategori', 'Count'])
                pareto_df = pareto_df.sort_values(by='Count', ascending=False)
                pareto_df['Cumulative'] = pareto_df['Count'].cumsum() / pareto_df['Count'].sum() * 100

                # Buat Chart Gabungan (Bar + Line)
                fig_pareto = go.Figure()
                fig_pareto.add_trace(go.Bar(x=pareto_df['Kategori'], y=pareto_df['Count'], name="Jumlah Keluhan", marker_color='indianred'))
                fig_pareto.add_trace(go.Scatter(x=pareto_df['Kategori'], y=pareto_df['Cumulative'], name="% Kumulatif", yaxis="y2", line=dict(color="blue", width=3)))

                fig_pareto.update_layout(
                    yaxis=dict(title="Jumlah Operator"),
                    yaxis2=dict(title="Persentase Kumulatif (%)", overlaying="y", side="right", range=[0, 110]),
                    legend=dict(x=0.8, y=1.1)
                )
                st.plotly_chart(fig_pareto, use_container_width=True)
            
            st.divider()

            # --- Poin 5: Tabel Data Lengkap ---
            st.subheader("📋 Tabel Database Lengkap")
            # Filter kolom agar tidak terlalu penuh
            cols_to_show = ['Nama', 'NIK', 'Line', 'Team', 'Lama Bekerja', 'Urutan_Ranking', 'Timestamp']
            st.dataframe(df[cols_to_show], use_container_width=True)

        else:
            st.warning("Database masih kosong. Belum ada operator yang melakukan submit.")
            
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets. Pastikan link benar dan akses sudah 'Anyone with link'. Error: {e}")
else:
    st.error("Konfigurasi [connections.gsheets] tidak ditemukan di Secrets.")

