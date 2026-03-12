import streamlit as st
import pandas as pd
import plotly.express as px

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

# Ambil URL dari Secrets
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    url = st.secrets.connections.gsheets.spreadsheet
    csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit', '/export?format=csv')
    
    try:
        # Tambahkan ttl=0 agar data selalu fresh tiap kali dashboard dibuka
        df = pd.read_csv(csv_url)
        
        if not df.empty:
            # --- Tampilan Utama ---
            st.metric("Total Operator Terdaftar", len(df))
            
            # Grafik Per Line
            fig = px.bar(df, x='Line', title="Jumlah Peserta per Line", color='Line', barmode='group')
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabel Data Mentah
            st.subheader("📋 Tabel Data Lengkap")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Belum ada data operator yang masuk.")
            
    except Exception as e:
        st.error(f"Gagal memuat data. Error: {e}")
else:
    st.error("Konfigurasi Google Sheets tidak ditemukan di Secrets.")
