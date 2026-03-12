import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Rekap", layout="wide")

st.title("📊 Dashboard Monitoring Kompetensi")

# Ambil URL dari Secrets (Pastikan nama 'spreadsheet' sesuai di Secrets Anda)
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    url = st.secrets.connections.gsheets.spreadsheet
    # Ubah link agar bisa dibaca langsung sebagai CSV
    csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit', '/export?format=csv')
    
    try:
        df = pd.read_csv(csv_url)
        
        # --- Tampilan Utama ---
        st.metric("Total Operator Terdaftar", len(df))
        
        # Grafik Per Line
        fig = px.bar(df, x='Line', title="Jumlah Peserta per Line", color='Line')
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabel Data Mentah
        st.subheader("📋 Tabel Data Lengkap")
        st.dataframe(df)
        
    except Exception as e:
        st.error(f"Gagal memuat data. Pastikan Google Sheets sudah 'Anyone with link can View'. Error: {e}")
else:
    st.error("Konfigurasi Google Sheets tidak ditemukan di Secrets.")
