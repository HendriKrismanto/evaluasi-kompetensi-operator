import streamlit as st
import requests
import random
import plotly.graph_objects as go
import pandas as pd
from fpdf import FPDF
import io

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- 1. FUNGSI KIRIM KE GOOGLE FORM ---
def simpan_ke_google_form(data_dict):
    # GANTI 'viewform' menjadi 'formResponse' (PENTING!)
    url = "https://docs.google.com/forms/d/e/1FAIpQLScpvddBqUfr5gJdkciljnpvZeFPkLkwxhLMswI26b8Rdhty6g/formResponse"

    # Fungsi pembantu untuk membersihkan teks (letakkan di dalam simpan_ke_google_form)
    def clean_text(text):
        if text is None: return ""
        # 1. Pastikan jadi string
        t = str(text)
        # 2. Hapus karakter enter/newline yang bikin error di URL
        t = t.replace("\n", " ").replace("\r", " ")
        # 3. Hapus spasi berlebih di awal/akhir
        return t.strip()
    
    # Gunakan Entry ID yang Anda dapatkan dari link pre-filled
    payload = {
        "entry.1519304593": data_dict.get('Nama'),
        "entry.553093979": data_dict.get('NIK'),
        "entry.443486013": str(data_dict.get('Tanggal')),
        "entry.790869993": data_dict.get('Line'),
        "entry.1284202058": data_dict.get('Team'),
        "entry.1725984221": data_dict.get('Lama Bekerja'),
        
        # HAPUS awalan 'Skor_' jika di session_state hanya bernama kategori saja
        "entry.1076580018": data_dict.get('Work Element', 0),
        "entry.100503982": data_dict.get('Pengetahuan Proses', 0),
        "entry.2025127947": data_dict.get('Pengetahuan Produk', 0),
        "entry.619176562": data_dict.get('Jenis NG', 0),
        "entry.562062916": data_dict.get('Efek NG', 0),
        
        # Pastikan data_dict memiliki key ini sebelum memanggil fungsi simpan
        "entry.870916734": clean_text(data_dict.get('UrutanRanking')),
        "entry.1145430443": clean_text(data_dict.get('FokusTraining')), 
    }
    
    try:
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            st.success("✅ Data Berhasil Disimpan ke Database!")
        else:
            st.error(f"❌ Gagal Simpan. Kode: {r.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error Koneksi: {e}")

def kirim_email_pdf(pdf_bytes, user_data):
    # Mengambil data dari Secrets yang baru Anda isi
    sender = st.secrets["email_sender"]
    password = st.secrets["email_password"]
    receiver = st.secrets["email_receiver"]
    
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"Laporan Kompetensi: {user_data.get('Nama')} ({user_data.get('NIK')})"
    
    body = f"Terlampir laporan evaluasi kompetensi untuk operator:\n\nNama: {user_data.get('Nama')}\nNIK: {user_data.get('NIK')}\nLine: {user_data.get('Line')}"
    msg.attach(MIMEText(body, 'plain'))
    
    # Lampirkan PDF
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= Laporan_{user_data.get('NIK')}.pdf")
    msg.attach(part)
    
    try:
        # Koneksi ke server Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        st.info("📩 Salinan laporan otomatis telah dikirim ke Admin.")
    except Exception as e:
        st.error(f"⚠️ Gagal mengirim laporan: {e}")

def check_password():
    """Returns True if the user had the correct password."""

    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            st.session_state["role"] = "admin" # Set sebagai admin jika password ini benar
            del st.session_state["password"]
        elif st.session_state["password"] == "JID12345": # Contoh password operator
            st.session_state["password_correct"] = True
            st.session_state["role"] = "operator" # Set sebagai operator
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
        
        # """Checks whether a password entered by the user is correct."""
        # if st.session_state["password"] == st.secrets["password"]:
        #     st.session_state["password_correct"] = True
        #     del st.session_state["password"]  # Hapus password dari session_state
        # else:
        #     st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Tampilan Form Login
        st.markdown("### 🔒 Akses Terbatas")
        st.text_input("Masukkan Password Operator", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("😕 Password salah")
        return False
    else:
        return True

# --- CEK LOGIN ---
if not check_password():
    st.stop()  # Berhenti di sini jika belum login

# 2. DI SINI TEMPATNYA (Tepat setelah login berhasil)
if "role" in st.session_state and st.session_state["role"] == "operator":
    st.markdown("""
        <style>
            /* Mengsembunyikan menu navigasi di sidebar */
            [data-testid="stSidebarNav"] {display: none;}
            
            /* (Opsional) Mengsembunyikan tombol 'X' penutup sidebar */
            [data-testid="collapsedControl"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

# --- 1. DATA PERNYATAAN ---
BANK_SOAL = {
    'Work Element': [
        "Saya menjalankan proses sesuai urutan WE", "Saya hafal langkah langkah pekerjaan sesuai WE",
        "Saya tahu kapan menggunakan tangan kanan dan kiri sesuai WE", "Saya tahu posisi meletakkan part di atas mesin",
        "Saya hafal OPL di proses saya", "Saya membaca ulang WE setiap 1 minggu sekali", "Saya membaca ulang WE setiap 1 bulan sekali"
    ],
    'Pengetahuan Proses': [
        "Saya tahu fungsi mesin yang saya operasikan", "Saya paham parameter penting yang harus diperhatikan di mesin",
        "Saya tahu maksud display (grafik) yang muncul di monitor mesin saya", "Saya paham gejala yang muncul bila mesin mulai abnormal",
        "Saya paham jenis-jenis alarm pada mesin saya", "Saya paham pokayoke di proses saya", "Saya paham interlock di proses saya"
    ],
    'Pengetahuan Produk': [
        "Saya tahu fungsi produk jadi yang dibuat di line saya", "Saya tahu fungsi part yang dihasilkan dari proses saya",
        "Saya paham yang merupakan 'Customer Assembly Point'", "Saya tahu part apa saja yang terlibat di proses saya",
        "Saya dapat membedakan part-part mirip yang jalan di proses saya", "Saya tahu aturan memegang produk jadi yang benar",
        "Saya paham special characteristic yang ada di proses saya"
    ],
    'Jenis NG': [
        "Saya paham jenis-jenis NG yang dapat terjadi di proses saya", "Saya paham jenis-jenis NG yang terjadi di proses sebelum saya",
        "Saya tahu penyebab terjadinya NG di proses saya", "Saya tahu customer claim yang pernah terjadi di proses saya",
        "Saya paham karakteristik Quality yang otomatis dicek oleh mesin", "Saya paham poin-poin yang harus dicek secara visual / feeling",
        "Saya paham Q-Point yang ada di proses saya"
    ],
    'Efek NG': [
        "Saya paham efek NG yang saya buat di proses selanjutnya", "Saya paham efek NG yang saya buat di customer",
        "Saya tahu apa yang dimaksud Performance NG", "Saya tahu jenis-jenis noise yang muncul ketika proses saya bermasalah",
        "Saya tahu efek NG dari proses dengan special characteristic 'C'", "Saya tahu efek NG dari proses dengan special characteristic 'S'",
        "Saya tahu biaya yang ditimbulkan dari menghasilkan produk NG"
    ]
}

if 'used_questions' not in st.session_state:
    st.session_state.used_questions = {cat: [] for cat in BANK_SOAL.keys()}

MAX_BLOCKS = 12

# --- 2. MANAJEMEN SESI ---
if 'step' not in st.session_state:
    st.session_state.step = 0  # Mulai dari 0 untuk Form Data Diri
    st.session_state.user_data = {} # Simpan data diri di sini
    st.session_state.scores = {cat: 0 for cat in BANK_SOAL.keys()}
    st.session_state.weakness_statements = [] # Untuk rekomendasi training
    st.session_state.finished = False

def proses_pilihan(m_idx, l_idx, current_block):
    if m_idx == l_idx:
        st.error("⚠️ Kesalahan: Pilihan 'Paling Sesuai' dan 'Paling Tidak Sesuai' tidak boleh sama!")
    else:
        st.session_state.scores[current_block[m_idx]['cat']] += 1
        st.session_state.scores[current_block[l_idx]['cat']] -= 1
        # Simpan teks pernyataan yang paling tidak sesuai
        st.session_state.weakness_statements.append({
            'cat': current_block[l_idx]['cat'],
            'text': current_block[l_idx]['text']
        })
        
        if st.session_state.step < MAX_BLOCKS:
            st.session_state.step += 1
        else:
            st.session_state.finished = True
        st.rerun()

# --- 3. FUNGSI GENERATOR PDF ---
def buat_pdf(scores, fig, user_data, weakness_statements):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- Header & Profil ---
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 10, "LAPORAN KOMPETENSI OPERATOR", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(5)

    pdf.set_font("helvetica", 'B', 11)
    pdf.cell(0, 7, "Profil Operator:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", '', 10)

    for k, v in user_data.items():
        pdf.cell(40, 6, f"{k}", 0)
        pdf.cell(5, 6, ":", 0)
        pdf.cell(0, 6, f"{str(v)}", 0, new_x="LMARGIN", new_y="NEXT")
    
    # --- Radar Chart (Reset X setelah Gambar) ---
    img_bytes = fig.to_image(format="png")
    with open("temp_radar.png", "wb") as f:
        f.write(img_bytes)
    
    pdf.image("temp_radar.png", x=45, y=pdf.get_y() + 5, w=120)
    pdf.set_y(pdf.get_y() + 125)
    pdf.set_x(pdf.l_margin) # Reset X ke margin kiri

    # --- Tabel Skor & Persentase ---
    pdf.set_font("helvetica", 'B', 11)
    pdf.cell(90, 8, "Kategori Kompetensi", 1, new_x="RIGHT", new_y="TOP", align='C')
    pdf.cell(45, 8, "Skor Pts", 1, new_x="RIGHT", new_y="TOP", align='C')
    pdf.cell(45, 8, "Persentase", 1, new_x="LMARGIN", new_y="NEXT", align='C')
    
    pdf.set_font("helvetica", '', 10)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for cat, score in sorted_scores:
        pct = int(((score + 12) / 24) * 100)
        pdf.cell(90, 8, f" {cat}", 1, new_x="RIGHT", new_y="TOP")
        pdf.cell(45, 8, str(score), 1, new_x="RIGHT", new_y="TOP", align='C')
        pdf.cell(45, 8, f"{pct}%", 1, new_x="LMARGIN", new_y="NEXT", align='C')

    # --- Rekomendasi Training (Gunakan Lebar Statis) ---
    pdf.ln(10)
    if pdf.get_y() > 220: pdf.add_page()
        
    pdf.set_font("helvetica", 'B', 11)
    pdf.cell(0, 8, "Rekomendasi Training (Prioritas):", new_x="LMARGIN", new_y="NEXT")
    
    if weakness_statements:
        df_weak = pd.DataFrame(weakness_statements)
        weak_counts = df_weak['cat'].value_counts()
        for cat, count in weak_counts.items():
            pdf.set_font("helvetica", 'B', 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 7, f" Kategori: {cat} (Muncul {count}x)", border=0, new_x="LMARGIN", new_y="NEXT", align='L', fill=True)
            
            pdf.set_font("helvetica", '', 9)
            items = df_weak[df_weak['cat'] == cat]['text'].unique()
            for item in items:
                # Gunakan lebar tetap (misal 180) alih-alih 0 untuk kestabilan
                pdf.set_x(pdf.l_margin + 5)
                pdf.multi_cell(180, 6, f"- {item}", border=0)
            pdf.ln(2)
    
    # Output sebagai bytes untuk Streamlit
    return pdf.output()

# --- 4. TAMPILAN ANTARMUKA ---
st.markdown("<h1 style='font-size: 36px; text-align: left;'>🎯 Evaluasi Mandiri Kompetensi Operator</h1>", unsafe_allow_html=True)

# STEP 0: FORM DATA DIRI
if st.session_state.step == 0:
    st.subheader("📝 Data Diri Operator")
    with st.form("form_data"):
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("Nama Lengkap")
            nik = st.text_input("NIK")
            tanggal = st.date_input("Tanggal Evaluasi")
        with col2:
            line = st.selectbox("Line", ["C-EPS 1", "C-EPS 2", "C-EPS 3"])
            team = st.selectbox("Team", ["A", "B"])
            lama_kerja = st.number_input("Lama Bekerja (Tahun)", min_value=0, step=1)
        
        submit_data = st.form_submit_button("Mulai Evaluasi 🚀")
        
        if submit_data:
            if nama and nik:
                st.session_state.user_data = {
                    "Nama": nama, "NIK": nik, "Tanggal": tanggal,
                    "Line": line, "Team": team, "Lama Bekerja": lama_kerja
                }
                st.session_state.step = 1
                st.rerun()
            else:
                st.error("Mohon isi Nama dan NIK terlebih dahulu!")

# STEP LANJUTAN: PERTANYAAN (Modifikasi sedikit pada range step)
elif not st.session_state.finished:
    st.write(f"### Blok {st.session_state.step} dari {MAX_BLOCKS}")
    st.progress(st.session_state.step / MAX_BLOCKS)

    # --- LOGIKA PENGACAKAN DINAMIS (REVISI) ---
    # Gunakan kombinasi NIK dan Step agar urutan UNIK per operator
    # Jika NIK belum ada (saat refresh), gunakan seed random murni
    user_nik = st.session_state.user_data.get('NIK', 'random')
    random.seed(f"{user_nik}_{st.session_state.step}")
    
    # --- 1. LOGIKA PENGACAKAN MERATA (REVISI) ---
    # Gunakan seed berdasarkan step agar pilihan konsisten jika halaman refresh
    # random.seed(st.session_state.step)
    
    cats = list(BANK_SOAL.keys())
    block = []
    
    # Ambil NIK sebagai dasar pengacakan agar konsisten per orang
    user_nik = st.session_state.user_data.get('NIK', '0')
    
    for c in cats:
        # 1. Ambil daftar soal asli
        soal_list = list(BANK_SOAL[c])
        
        # 2. Acak daftar soal tersebut KHUSUS untuk NIK ini
        # Ini membuat Operator A punya urutan (1,3,2..) dan Operator B (4,1,3..)
        random.seed(user_nik) 
        random.shuffle(soal_list)
        
        # 3. Ambil soal berdasarkan urutan langkah (step) dari daftar yang sudah diacak
        # Tetap menggunakan rumus cycle (%) agar merata
        idx = (st.session_state.step - 1) % len(soal_list)
        
        block.append({'cat': c, 'text': soal_list[idx]})
    
    # 4. Terakhir, acak posisi tampilan di layar (Most-Least) agar tidak monoton
    # Gunakan seed gabungan agar posisi tidak berubah jika halaman refresh
    random.seed(f"{user_nik}_{st.session_state.step}")
    random.shuffle(block)
    
    with st.container(border=True):
        st.markdown(
            "**Pilih satu pernyataan yang PALING menggambarkan Anda:**  \n"
            "(Paling paham / Paling mengerti)"
        )
        m_sel = st.radio("Most (+)", range(5), format_func=lambda i: block[i]['text'], key=f"m_{st.session_state.step}")
        
        st.divider()

        st.markdown(
            "**Pilih satu pernyataan yang PALING TIDAK menggambarkan Anda:**  \n"
            "(Paling TIDAK paham / Paling TIDAK mengerti)"
        )
               
        l_sel = st.radio("Least (-)", range(5), format_func=lambda i: block[i]['text'], key=f"l_{st.session_state.step}")

    if st.button("Simpan & Lanjutkan ➡️", use_container_width=True):
        proses_pilihan(m_sel, l_sel, block)

else:
    st.header("📊 Profil Kompetensi Operator")

    # --- A. PERHITUNGAN DATA (WAJIB DI ATAS AGAR TOMBOL BISA MEMBACA DATA) ---
    sorted_scores = sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True)
    ranking_str = ", ".join([f"{c}({s}pts)" for c, s in sorted_scores])
    
    rekomendasi_list = []
    training_summary = ""
    if st.session_state.weakness_statements:
        df_weak = pd.DataFrame(st.session_state.weakness_statements)
        if not df_weak.empty:
            weak_counts = df_weak['cat'].value_counts()
            for cat, count in weak_counts.items():
                items_list = df_weak[df_weak['cat'] == cat]['text'].unique()
                items_str = "/".join(items_list)
                rekomendasi_list.append(f"[{cat}]: {items_str}")
            training_summary = " | ".join(rekomendasi_list)

    # Persiapan Gambar Radar untuk PDF/Submit
    categories = list(st.session_state.scores.keys())
    values = list(st.session_state.scores.values())
    radar_values = values + [values[0]]
    radar_cats = categories + [categories[0]]
    fig = go.Figure(data=go.Scatterpolar(r=radar_values, theta=radar_cats, fill='toself', line_color='teal'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[-12, 12])))

    # --- B. DISPLAY 1: TOMBOL SUBMIT & PDF (PALING ATAS) ---
    c_sub1, c_sub2 = st.columns(2)
    with c_sub1:
        if st.button("💾 Submit Data", use_container_width=True):
            hasil_akhir = {
                **st.session_state.user_data,
                **st.session_state.scores,
                "UrutanRanking": ranking_str,
                "FokusTraining": training_summary
            }
            simpan_ke_google_form(hasil_akhir)
            pdf_file = buat_pdf(st.session_state.scores, fig, st.session_state.user_data, st.session_state.weakness_statements)
            kirim_email_pdf(bytes(pdf_file), st.session_state.user_data)
            st.success("✅ Data Berhasil Dikirim!")

    with c_sub2:
        pdf_out = buat_pdf(st.session_state.scores, fig, st.session_state.user_data, st.session_state.weakness_statements)
        st.download_button("📥 Download PDF Laporan", data=bytes(pdf_out), file_name=f"Laporan_{st.session_state.user_data.get('Nama')}.pdf", use_container_width=True)

    st.divider()

    # --- C. DISPLAY 2: INFORMASI OPERATOR ---
    with st.expander("📝 Informasi Operator", expanded=True):
        col1, col2 = st.columns(2)
        d = st.session_state.user_data
        col1.markdown(f"**Nama:** {d.get('Nama')}\n\n**NIK:** {d.get('NIK')}\n\n**Tanggal:** {d.get('Tanggal')}")
        col2.markdown(f"**Line:** {d.get('Line')}\n\n**Team:** {d.get('Team')}\n\n**Lama Kerja:** {d.get('Lama Bekerja')} Thn")

    # --- D. DISPLAY 3: RADAR CHART ---
    st.plotly_chart(fig, use_container_width=True)

    # --- E. DISPLAY 4: SKOR & RANKING ---
    st.subheader("🏆 Skor & Ranking Kompetensi")
    st.info(f"**Urutan Kekuatan:** {ranking_str}")
    
    cols = st.columns(len(sorted_scores))
    for i, (cat, score) in enumerate(sorted_scores):
        persentase = int(((score + 12) / 24) * 100)
        cols[i].metric(label=cat, value=f"{persentase}%", delta=f"{score} pts")

    # --- F. DISPLAY 5: REKOMENDASI TRAINING ---
    st.subheader("📚 Rekomendasi Training")
    if st.session_state.weakness_statements:
        for cat, count in weak_counts.items():
            items_list = df_weak[df_weak['cat'] == cat]['text'].unique()
            with st.expander(f"⚠️ {cat} ({count} poin)", expanded=True):
                for item in items_list:
                    st.write(f"- {item}")

    # --- G. DISPLAY 6: DOWNLOAD CSV (PALING BAWAH) ---
    st.divider()
    full_data = {**st.session_state.user_data, **st.session_state.scores, "UrutanRanking": ranking_str, "FokusTraining": training_summary}
    df_export = pd.DataFrame([full_data])
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("📂 Download CSV Detail", csv, f"Data_{st.session_state.user_data.get('Nama')}.csv", "text/csv", use_container_width=True)
