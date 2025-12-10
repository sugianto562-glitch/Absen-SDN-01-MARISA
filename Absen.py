import streamlit as st
from streamlit_webrtc import webrtc_streamer, RTCConfiguration, WebRtcMode
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import urllib.parse
from PIL import Image
import io
import cv2
import av
import numpy as np
from pyzbar.pyzbar import decode
from pyairtable import Api
import base64 

# ==============================================================================
# ⚙️ KONFIGURASI AIRTABLE (WAJIB DIISI)
# ==============================================================================
# Hati-hati: Key ini harus aman di Streamlit Cloud menggunakan st.secrets
AIRTABLE_API_KEY = st.secrets["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID = "appJSVM6gP8cuSnKZ" 
AIRTABLE_TABLE_NAME = "Table 1"        

def kirim_ke_airtable(data_dict):
    """Fungsi untuk mengirim data ke Airtable."""
    try:
        if "patXXXX" in AIRTABLE_API_KEY:
            st.warning("⚠️ Airtable API Key masih placeholder. Tidak mengirim.")
            return False 
        
        api = Api(AIRTABLE_API_KEY)
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
        table.create(data_dict)
        return True
    except Exception as e:
        print(f"Error Airtable: {e}")
        return False

# --- 0. FUNGSI KAMERA (Callback) ---
def video_frame_callback(frame):
    """Fungsi callback untuk memproses frame video (scan QR/Barcode)."""
    img = frame.to_ndarray(format="bgr24")
    decoded_objects = decode(img)
    
    if 'nisn_scan' not in st.session_state:
        st.session_state['nisn_scan'] = None
        
    for obj in decoded_objects:
        data = obj.data.decode("utf-8")
        st.session_state['nisn_scan'] = data
        
        points = obj.polygon
        if len(points) == 4: pts = points
        else: pts = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
        
        n = len(pts)
        for j in range(0, n):
            cv2.line(img, pts[j], pts[(j + 1) % n], (0, 255, 0), 3)
        cv2.putText(img, data, (pts[0].x, pts[0].y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
    return av.VideoFrame.from_ndarray(img, format="bgr24")

# 💡 FUNGSI BARU: Mengubah Gambar menjadi Base64 untuk CSS
def get_image_as_base64(file_path):
    """Mengonversi file gambar lokal ke string Base64 (Data URL)."""
    if not file_path or not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        # Mendapatkan MIME type dari file
        mime_type = "image/png" if file_path.endswith(".png") else "image/jpeg"
        return f"data:{mime_type};base64,{data}"
    except Exception as e:
        print(f"Error converting to base64: {e}")
        return None

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Sistem SDN 01 MARISA", page_icon="🏫", layout="wide")

# --- PENTING: Style Dasar CSS (TANPA LOGIKA 'menu')
st.markdown("""
    <style>
    /* Mengoptimalkan tampilan teks secara umum */
    .stApp, p, h1, h2, h3, h4, label, .stMarkdown, span {
        color: #000000 !important; 
        text-shadow: none !important;
    }
    /* Style Dasar untuk background (akan di-override nanti) */
    .stApp { 
        background-color: #f0f2f6; 
    }
    
    /* Perbaikan Footer agar lebih responsif di HP */
    .footer {
        position: fixed; 
        left: 0; 
        bottom: 0; 
        width: 100%; 
        background-color: #000000 !important; 
        color: #ffffff !important; 
        text-align: center; 
        padding: 5px 10px; 
        z-index: 999;
    }
    .footer p, .footer span { 
        color: #ffffff !important; 
        font-size: 12px; 
    }
    .footer marquee {
        display: block;
        overflow: hidden;
        white-space: nowrap;
    }

    /* Memastikan input field terlihat jelas */
    .stTextInput input {
        background-color: #ffffff !important; 
        color: #000000 !important; 
        border: 2px solid #000000 !important; 
        font-weight: bold;
    }
    
    /* Mengatur radio button */
    div[role="radiogroup"] {
        background-color: #ffffff !important; 
        color: #000000 !important; 
        border: 1px solid #000000; 
        padding: 5px; 
        border-radius: 5px;
    }
    
    /* Styling tombol */
    .stDownloadButton, .stButton>button {
        background-color: #007bff; 
        color: white !important; 
        border: none; 
        padding: 10px 20px; 
        text-align: center; 
        text-decoration: none; 
        display: inline-block; 
        font-size: 16px; 
        margin: 4px 2px; 
        cursor: pointer; 
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SETUP DATABASE & FOLDER ---
FILE_ABSEN = 'database_absen.csv'
FILE_SISWA = 'master_siswa.csv' 
FILE_SETTINGS = 'settings.json'
FOLDER_FOTO = 'foto_siswa' 

if not os.path.exists(FOLDER_FOTO): os.makedirs(FOLDER_FOTO)

DAFTAR_KELAS = ["1A", "1B", "1C", "2A", "2B", "2C", "3A", "3B", "3C", "4A", "4B", "5A", "5B", "6A", "6B", "Guru/Staf"]

def init_csv(filename, columns):
    """Inisialisasi file CSV jika belum ada atau kosong."""
    try:
        if not os.path.exists(filename): raise FileNotFoundError
        df = pd.read_csv(filename, dtype={'NISN': str}) # Pastikan NISN dibaca sebagai string
        for col in columns:
            if col not in df.columns: df[col] = ""
        df.to_csv(filename, index=False)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df = pd.DataFrame(columns=columns)
        df.to_csv(filename, index=False)

init_csv(FILE_ABSEN, ['Tanggal', 'Jam', 'NISN', 'Nama', 'Kelas', 'Keterangan'])
init_csv(FILE_SISWA, ['NISN', 'Nama', 'Kelas', 'No_HP']) 

def load_settings():
    """Memuat atau membuat pengaturan sekolah."""
    defaults = {
        "nama_sekolah": "SDN 01 MARISA", 
        "alamat_sekolah": "Jl. Pendidikan, Marisa", 
        "logo_path": "logo_default.png", 
        "background_image": None,
        "logo_base64": None, 
        "bg_base64": None    
    }
    if not os.path.exists(FILE_SETTINGS): return defaults
    try:
        with open(FILE_SETTINGS, 'r') as f: return {**defaults, **json.load(f)}
    except: return defaults

config = load_settings()

def buat_link_wa(nomor, pesan):
    """Membuat tautan WhatsApp."""
    nomor = str(nomor).strip().replace(".0", "").replace("-", "").replace(" ", "").replace("+", "")
    if nomor.startswith("0"): nomor = "62" + nomor[1:]
    if len(nomor) > 8:
        return f"https://api.whatsapp.com/send?phone={nomor}&text={urllib.parse.quote(pesan)}"
    return None 

# --- 3. LOGIC LOGIN ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'nisn_scan' not in st.session_state: st.session_state['nisn_scan'] = None
if 'scan_main_key' not in st.session_state: st.session_state['scan_main_key'] = 0 

def login_screen():
    # Style login screen khusus
    st.markdown("""<style>.stApp {background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=2070"); background-size: cover;}</style>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align:center; color:white !important;'>🔐 LOGIN SISTEM</h2>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='text-align:center; color:#00a8cc !important;'>{config['nama_sekolah']}</h4>", unsafe_allow_html=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("MASUK", type="primary", use_container_width=True):
                if u == "admin" and p == "40500714":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else: st.error("Gagal Login")

if not st.session_state['logged_in']:
    login_screen()
    st.stop()

# --- 4. TAMPILAN UTAMA ---

bg_base64_url = config.get('bg_base64')
logo_base64_url = config.get('logo_base64')

# Pindahkan LOGIC menu ke dalam sidebar
with st.sidebar:
    # Menampilkan logo (menggunakan Base64 jika ada)
    if logo_base64_url:
        st.markdown(f'<img src="{logo_base64_url}" width="100">', unsafe_allow_html=True)
    elif os.path.exists(config.get('logo_path', '')):
        st.image(config['logo_path'], width=100) 
    else: 
        st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=80)
        
    st.title(config['nama_sekolah'])
    st.write(config['alamat_sekolah'])
    st.markdown("---")
    
    menu = st.radio("MENU UTAMA", ["🖥️ Absensi (Scan)", "📊 Laporan & Persentase", "📂 Data Master", "📸 Upload Foto", "🔗 Link WA Wali Murid", "⚙️ Pengaturan"])
    
    st.markdown("---")
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

# LOGIKA BACKGROUND DENGAN BASE64
if st.session_state['logged_in']:
    if menu == "🖥️ Absensi (Scan)":
        bg_style = ".stApp {background-image: none; background-color: #ffffff;}"
    elif bg_base64_url:
        # Menggunakan Base64 URL untuk background
        bg_style = f".stApp {{background-image: linear-gradient(rgba(255,255,255,0.8), rgba(255,255,255,0.8)), url('{bg_base64_url}'); background-size: cover; background-attachment: fixed;}}"
    else:
        bg_style = ".stApp {background-image: none; background-color: #f0f2f6;}"
    
    st.markdown(f"""<style>{bg_style}</style>""", unsafe_allow_html=True)


st.markdown("""<div class="footer"><marquee direction="right" scrollamount="6"><span>Sistem Informasi Sekolah Digital — Designed with ❤️ by <b>Sugianto (SDN 01 MARISA)</b></span></marquee></div>""", unsafe_allow_html=True)


# --- A. MENU SCAN ABSENSI ---
if menu == "🖥️ Absensi (Scan)":
    
    # Atur waktu WITA
    now = datetime.now() + timedelta(hours=8)
    
    # Gunakan st.columns secara hati-hati di HP (rasio 3,1 akan menjadi stacked)
    c1, c2 = st.columns([3,1])
    c1.title("Absen Digital SDN 01 MARISA")
    c1.markdown(f"#### 📆 {now.strftime('%A, %d %B %Y')}")
    time_placeholder = c2.empty()
    time_placeholder.metric("Jam (WITA)", now.strftime("%H:%M:%S"))
    st.divider()
    
    # --- Modifikasi: Bagian Kamera Dihilangkan, Diganti Instruksi Scan ---
    st.markdown("### 🖱️ Gunakan Alat Scan Barcode")
    st.info("Arahkan kartu ke *alat scan barcode* Anda. Hasil scan (NISN) akan muncul di kotak di bawah.")
    
    # 3. AREA INPUT MANUAL / HASIL SCAN
    st.markdown("### 👇 INPUT MANUAL / HASIL SCAN")
    
    # Ambil hasil scan jika ada (meskipun webrtc tidak aktif, input manual tetap dapat bekerja)
    nisn_from_scan = st.session_state['nisn_scan'] if st.session_state['nisn_scan'] else ""
    
    with st.container(border=True):
        st.write("🔴 STATUS:")
        # Ubah horizontal=True menjadi false untuk tampilan vertikal yang lebih baik di HP
        mode_absen = st.radio("Pilih Mode:", ["DATANG (Hadir)", "PULANG"], horizontal=False, label_visibility="collapsed")
        st.write("⌨️ MASUKKAN NISN:")
        
        # Kolom input ini akan menerima input dari scanner fisik (berfungsi seperti keyboard)
        nisn_input = st.text_input("Arahkan Scanner ke Barcode Siswa/Ketik NISN lalu Enter:", value=nisn_from_scan, key=f"scan_main_{st.session_state['scan_main_key']}").strip()

    if nisn_input:
        df_siswa = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
        siswa = df_siswa[df_siswa['NISN'] == nisn_input]
        
        if not siswa.empty:
            nama_s = siswa.iloc[0]['Nama']
            kelas_s = siswa.iloc[0]['Kelas']
            hp_s = siswa.iloc[0]['No_HP']
            ket_fix = "Hadir" if "DATANG" in mode_absen else "Pulang"
            
            df_absen = pd.read_csv(FILE_ABSEN, dtype={'NISN': str})
            
            sudah_absen = df_absen[
                (df_absen['Tanggal'] == now.strftime("%Y-%m-%d")) & 
                (df_absen['NISN'] == nisn_input) & 
                (df_absen['Keterangan'] == ket_fix)
            ]
            
            if not sudah_absen.empty: 
                st.warning(f"⚠️ {nama_s} Sudah absen {ket_fix} hari ini!")
            else:
                # 1. SIAPKAN DATA BARU
                data_baru = {
                    'Tanggal': now.strftime("%Y-%m-%d"), 
                    'Jam': now.strftime("%H:%M:%S"), 
                    'NISN': nisn_input, 
                    'Nama': nama_s, 
                    'Kelas': kelas_s, 
                    'Keterangan': ket_fix
                }
                
                # 2. SIMPAN LOKAL (Gunakan 'Kelas')
                df_absen = pd.concat([df_absen, pd.DataFrame([data_baru])], ignore_index=True)
                df_absen.to_csv(FILE_ABSEN, index=False)
                
                # 3. KIRIM KE AIRTABLE (Gunakan 'Class Name')
                dt_kirim = data_baru.copy()
                dt_kirim['Class Name'] = dt_kirim.pop('Kelas') # Ganti 'Kelas' menjadi 'Class Name' untuk Airtable
                
                with st.spinner("Mengirim ke Airtable..."):
                    sukses = kirim_ke_airtable(dt_kirim)
                    if sukses: st.toast("✅ Tersimpan di Airtable!", icon="☁️")
                    else: st.warning("⚠️ Tersimpan Lokal, Gagal Airtable.")

                # 4. TAMPILKAN HASIL SUKSES
                c_foto, c_teks = st.columns([1,3])
                with c_foto:
                    path_foto = f"{FOLDER_FOTO}/{nisn_input}.jpg"
                    if os.path.exists(path_foto): st.image(path_foto, use_column_width=True) 
                    else: st.image("https://via.placeholder.com/150?text=No+Image", use_column_width=True)
                with c_teks:
                    st.success(f"✅ SUKSES: {nama_s}")
                    st.markdown(f"{ket_fix} | Pukul: {now.strftime('%H:%M')}")
                    pesan = f"Assalamualaikum. Siswa a.n {nama_s} ({kelas_s}) telah {ket_fix.upper()} pada pukul {now.strftime('%H:%M')}."
                    link_wa = buat_link_wa(hp_s, pesan)
                    if link_wa: 
                        st.link_button("📲 KIRIM WA", link_wa)

            # Reset hasil scan di session state dan update key agar input manual reset
            st.session_state['nisn_scan'] = None
            st.session_state['scan_main_key'] += 1
            st.rerun() # Rerun agar input text kosong lagi setelah proses
            
        else: 
            st.error("❌ Data Siswa Tidak Ditemukan!")
            st.session_state['nisn_scan'] = None # Reset scan jika NISN tidak ditemukan
            st.session_state['scan_main_key'] += 1
            st.rerun()

    st.markdown("---")
    with st.expander("📝 Input Siswa Tidak Hadir (Sakit/Izin/Alpa)"):
        with st.form("manual"):
            df_s = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
            if not df_s.empty: 
                pilih = st.selectbox("Nama Siswa:", df_s['NISN'] + " - " + df_s['Nama'] + " (" + df_s['Kelas'] + ")")
                nisn_m = pilih.split(" - ")[0]
            else: 
                pilih = ""
                nisn_m = ""
                
            ket = st.selectbox("Keterangan:", ["Sakit", "Izin", "Alpa"])
            
            if st.form_submit_button("Simpan Data Manual"):
                if pilih and nisn_m:
                    data_siswa = df_s[df_s['NISN']==nisn_m].iloc[0]
                    nm = data_siswa['Nama']
                    kls = data_siswa['Kelas']
                    df_a = pd.read_csv(FILE_ABSEN, dtype={'NISN': str})
                    
                    sudah_absen_manual = df_a[
                        (df_a['Tanggal'] == now.strftime("%Y-%m-%d")) & 
                        (df_a['NISN'] == nisn_m) & 
                        (df_a['Keterangan'] == ket)
                    ]
                    
                    if not sudah_absen_manual.empty:
                        st.warning(f"⚠️ {nm} sudah diinput {ket} hari ini.")
                    else:
                        # 1. SIMPAN LOKAL (Gunakan 'Kelas' untuk CSV)
                        b = {'Tanggal': now.strftime("%Y-%m-%d"), 'Jam': now.strftime("%H:%M:%S"), 'NISN': nisn_m, 'Nama': nm, 'Kelas': kls, 'Keterangan': ket}
                        df_a = pd.concat([df_a, pd.DataFrame([b])], ignore_index=True)
                        df_a.to_csv(FILE_ABSEN, index=False)
                        
                        # 2. KIRIM KE AIRTABLE (Gunakan 'Class Name')
                        data_airtable = b.copy()
                        data_airtable['Class Name'] = data_airtable.pop('Kelas')
                        
                        sukses = kirim_ke_airtable(data_airtable)
                        if sukses: st.toast("✅ Tersimpan di Airtable!", icon="☁️")
                        else: st.warning("⚠️ Tersimpan Lokal, Gagal Airtable.")
                        
                        st.success(f"Tersimpan: {nm} - {ket}")
                else:
                    st.error("Pilih siswa terlebih dahulu.")


# --- B. MENU LAPORAN & PERSENTASE ---
elif menu == "📊 Laporan & Persentase":
    st.title("📊 Laporan & Download Data")
    # Di HP, kolom akan di-stacked (vertikal)
    col_tgl, col_space = st.columns([1, 2])
    with col_tgl: tgl = st.date_input("Pilih Tanggal Laporan:", datetime.now())
    
    df_a = pd.read_csv(FILE_ABSEN, dtype={'NISN': str})
    df_s = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
    data_harian = df_a[df_a['Tanggal'] == tgl.strftime("%Y-%m-%d")]
    
    if not df_s.empty:
        total_siswa = df_s.groupby('Kelas').size().reset_index(name='Total_Siswa')
        
        if not data_harian.empty:
            rekap = data_harian.groupby(['Kelas', 'Keterangan']).size().unstack(fill_value=0).reset_index()
            
            for k in ['Hadir', 'Sakit', 'Izin', 'Alpa', 'Pulang']:
                if k not in rekap.columns: rekap[k] = 0
            
            final = pd.merge(total_siswa, rekap, on='Kelas', how='left').fillna(0)
            
            # Hitung Sakit/Izin/Alpa
            final['Total_Non_Hadir'] = final['Sakit'] + final['Izin'] + final['Alpa']

            # Hitung persentase terhadap Total Siswa
            final['Hadir%'] = (final['Hadir'] / final['Total_Siswa'] * 100).round(1)
            final['Sakit%'] = (final['Sakit'] / final['Total_Siswa'] * 100).round(1)
            final['Izin%'] = (final['Izin'] / final['Total_Siswa'] * 100).round(1)
            final['Alpa%'] = (final['Alpa'] / final['Total_Siswa'] * 100).round(1)
            
            final['Ket_Hadir'] = final['Hadir%'].astype(str) + "%"
            final['Ket_Sakit'] = final['Sakit%'].astype(str) + "%"
            final['Ket_Izin'] = final['Izin%'].astype(str) + "%"
            final['Ket_Alpa'] = final['Alpa%'].astype(str) + "%"
            
            cols_int = ['Total_Siswa', 'Hadir', 'Sakit', 'Izin', 'Alpa', 'Pulang']
            for col in cols_int:
                if col in final.columns:
                    final[col] = final[col].astype(int)
            
            st.markdown("### 1. Rekapitulasi Per Kelas & Persentase")
            
            # Memastikan DataFrame dapat digulir jika terlalu lebar
            st.dataframe(
                final[['Kelas', 'Total_Siswa', 
                       'Hadir', 'Ket_Hadir', 
                       'Sakit', 'Ket_Sakit', 
                       'Izin', 'Ket_Izin', 
                       'Alpa', 'Ket_Alpa']], 
                use_container_width=True, 
                hide_index=True
            )
            
            st.markdown("### 2. Detail Siswa Absen Hari Ini")
            
            # Tampilkan semua data absensi harian (Hadir, Pulang, Sakit, Izin, Alpa)
            st.dataframe(data_harian[['Jam', 'Nama', 'Kelas', 'Keterangan']], use_container_width=True, hide_index=True)
            
            st.divider()
            
            # Download Button
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                final[['Kelas', 'Total_Siswa', 'Hadir', 'Hadir%', 'Sakit', 'Sakit%', 'Izin', 'Izin%', 'Alpa', 'Alpa%']].to_excel(writer, sheet_name='Rekap_Persentase', index=False)
                data_harian.to_excel(writer, sheet_name='Detail_Absensi_Harian', index=False)
                df_s.to_excel(writer, sheet_name='Data_Siswa_Master', index=False)
                
            st.download_button("⬇️ DOWNLOAD LAPORAN EXCEL", data=buffer.getvalue(), file_name=f"Laporan_{tgl.strftime('%d-%m-%Y')}.xlsx", mime="application/vnd.ms-excel", type="primary", use_container_width=True)
        
        else: st.info(f"Belum ada data absensi pada tanggal {tgl.strftime('%d-%m-%Y')}.")
    else: st.warning("Data Master Siswa Kosong.")

# --- C. MENU DATA MASTER ---
elif menu == "📂 Data Master":
    st.title("Data Master Siswa")
    tab1, tab2 = st.tabs(["➕ Tambah Data", "✏️ Edit / Hapus"])
    with tab1:
        with st.form("add"):
            # Kolom akan di-stacked di HP
            c1, c2 = st.columns(2)
            n_nisn = c1.text_input("NISN (Scan/Ketik)").strip()
            n_nama = c2.text_input("Nama")
            n_kelas = c1.selectbox("Kelas", DAFTAR_KELAS)
            n_hp = c2.text_input("No HP")
            if st.form_submit_button("Simpan"):
                df = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
                if n_nisn in df['NISN'].values: st.error("NISN Sudah Ada!")
                else:
                    new = {'NISN': n_nisn, 'Nama': n_nama, 'Kelas': n_kelas, 'No_HP': n_hp}
                    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
                    df.to_csv(FILE_SISWA, index=False)
                    st.success("Tersimpan!")
                    st.rerun()
    with tab2:
        df = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
        if not df.empty:
            list_siswa_dengan_kelas = df['NISN'] + " - " + df['Nama'] + " (" + df['Kelas'] + ")"
            # Selectbox yang responsif
            pilih = st.selectbox("Cari Siswa:", list_siswa_dengan_kelas)
            nisn_pilih = pilih.split(" - ")[0]
            data = df[df['NISN'] == nisn_pilih].iloc[0]
            
            # Kolom akan di-stacked di HP, ini baik untuk tata letak
            col_foto, col_edit = st.columns([1, 2])

            with col_foto:
                st.markdown("##### Foto Siswa")
                path_foto = f"{FOLDER_FOTO}/{nisn_pilih}.jpg"
                if os.path.exists(path_foto):
                    st.image(path_foto, use_column_width=True)
                else:
                    st.warning("Foto belum diunggah.")
                    st.image("https://via.placeholder.com/150?text=No+Image", use_column_width=True)
                
            with col_edit:
                with st.form("edit"):
                    st.markdown(f"##### Edit Data NISN: {nisn_pilih}")
                    e_nama = st.text_input("Nama", data['Nama'])
                    # Cari index kelas yang sesuai, default ke 0 jika tidak ada
                    kelas_index = DAFTAR_KELAS.index(data['Kelas']) if data['Kelas'] in DAFTAR_KELAS else 0
                    e_kelas = st.selectbox("Kelas", DAFTAR_KELAS, index=kelas_index)
                    e_hp = st.text_input("HP", str(data['No_HP']).replace(".0", "")) # Hilangkan .0 jika ada
                    c_sv, c_del = st.columns(2)
                    if c_sv.form_submit_button("Update Data", type="primary"):
                        df.loc[df['NISN'] == nisn_pilih, ['Nama', 'Kelas', 'No_HP']] = [e_nama, e_kelas, e_hp]
                        df.to_csv(FILE_SISWA, index=False)
                        st.success("Update Berhasil")
                        st.rerun()
                    if c_del.form_submit_button("Hapus Siswa", type="secondary"):
                        df = df[df['NISN'] != nisn_pilih]
                        df.to_csv(FILE_SISWA, index=False)
                        # Hapus juga fotonya jika ada
                        if os.path.exists(path_foto):
                            os.remove(path_foto)
                        st.success(f"Siswa dengan NISN {nisn_pilih} berhasil dihapus.")
                        st.rerun()
        else:
            st.info("Data Master Siswa masih kosong. Silakan tambahkan data di tab Tambah Data.")

# --- D. MENU UPLOAD FOTO ---
elif menu == "📸 Upload Foto":
    st.title("📸 Upload Foto Siswa")
    df_s = pd.read_csv(FILE_SISWA, dtype={'NISN':str})
    if not df_s.empty:
        list_siswa = df_s['NISN'] + " - " + df_s['Nama'] + " (" + df_s['Kelas'] + ")"
        cari_siswa = st.selectbox("Cari Siswa:", list_siswa)
        if cari_siswa:
            nisn_target = cari_siswa.split(" - ")[0]
            nama_target = cari_siswa.split(" - ")[1].split(" (")[0]
            path_now = f"{FOLDER_FOTO}/{nisn_target}.jpg"
            col_kiri, col_kanan = st.columns([1, 2])
            with col_kiri:
                st.write("Foto Saat Ini:")
                st.markdown(f"*NISN: {nisn_target}*")
                if os.path.exists(path_now): st.image(path_now, use_column_width=True)
                else: st.warning("Belum ada foto")
            with col_kanan:
                st.markdown("<br>", unsafe_allow_html=True) # Jaga jarak agar sejajar
                file_foto = st.file_uploader(f"Upload foto baru untuk {nama_target}", type=['jpg', 'png', 'jpeg'])
                if file_foto is not None:
                    if st.button("💾 Simpan Foto", type="primary"):
                        image = Image.open(file_foto).convert('RGB')
                        image.thumbnail((400, 400))
                        image.save(os.path.join(FOLDER_FOTO, f"{nisn_target}.jpg"))
                        st.success("Foto berhasil disimpan!")
                        st.rerun()
    else: st.warning("Data Master Kosong.")

# --- F. MENU LINK WA WALI MURID ---
elif menu == "🔗 Link WA Wali Murid":
    st.title("🔗 Kirim Pesan WA ke Wali Murid")
    st.info("Fitur ini membantu Anda mengirimkan pesan WhatsApp (WA) kepada wali murid per kelas secara cepat (satu per satu).")

    df_s = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
    
    if df_s.empty:
        st.warning("Data Master Siswa kosong. Silakan isi Data Master terlebih dahulu.")
    else:
        # 1. Pilih Kelas
        kelas_pilih = st.selectbox("Pilih Kelas:", ["-- Pilih Semua --"] + sorted(df_s['Kelas'].unique().tolist()))
        
        if kelas_pilih != "-- Pilih Semua --":
            df_filter = df_s[df_s['Kelas'] == kelas_pilih].copy()
            st.markdown(f"### Daftar Siswa Kelas {kelas_pilih}")
        else:
            df_filter = df_s.copy()
            st.markdown("### Daftar Seluruh Siswa")

        # 2. Input Pesan
        st.markdown("---")
        pesan_default = f"Assalamualaikum, Bapak/Ibu Wali Murid.\nKami dari {config['nama_sekolah']} ingin menyampaikan informasi: ...."
        pesan_input = st.text_area("Tulis Pesan yang Akan Dikirim:", value=pesan_default, height=150)

        # 3. Tampilkan Daftar Siswa dengan Link WA
        if not df_filter.empty:
            
            data_tampil = df_filter[['Nama', 'Kelas', 'No_HP']].copy()
            data_tampil['No_HP'] = data_tampil['No_HP'].apply(lambda x: str(x).replace(".0", "").strip() if pd.notna(x) else "")
            
            def generate_wa_link_button(row):
                nomor = row['No_HP']
                if len(str(nomor).replace(" ", "")) > 8:
                    pesan_personalized = f"Kepada Wali dari ananda {row['Nama']} ({row['Kelas']}),\n\n{pesan_input}"
                    link = buat_link_wa(nomor, pesan_personalized)
                    if link:
                        return f"[📲 Kirim WA](<{link}>)"
                return "❌ No HP Invalid/Kosong"

            data_tampil['Link WA'] = data_tampil.apply(generate_wa_link_button, axis=1)

            st.dataframe(
                data_tampil[['Nama', 'Kelas', 'No_HP', 'Link WA']],
                hide_index=True,
                use_container_width=True
            )

        else:
            st.info(f"Tidak ada siswa ditemukan di kelas {kelas_pilih}.")


# --- E. MENU PENGATURAN ---
elif menu == "⚙️ Pengaturan":
    st.title("Pengaturan Sekolah")
    
    col_set1, col_set2, col_set3 = st.columns(3)
    
    with col_set1:
        st.markdown("### Identitas Sekolah")
        with st.form("setting_sekolah"):
            new_nama = st.text_input("Nama Sekolah", config['nama_sekolah'])
            new_alamat = st.text_input("Alamat Sekolah", config['alamat_sekolah'])
            if st.form_submit_button("Simpan Identitas", type="primary"):
                config['nama_sekolah'] = new_nama
                config['alamat_sekolah'] = new_alamat
                with open(FILE_SETTINGS, 'w') as f: json.dump(config, f)
                st.success("Identitas tersimpan!")
                st.rerun()

    with col_set2:
        st.markdown("### Logo Sekolah")
        # Menampilkan logo yang sudah ada
        if logo_base64_url:
            st.markdown(f'<img src="{logo_base64_url}" width="100">', unsafe_allow_html=True)
        elif os.path.exists(config.get('logo_path', '')):
            st.image(config['logo_path'], width=100)
            
        up_logo = st.file_uploader("Ganti Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'], key="up_logo")
        
        if up_logo is not None:
            if st.button("Upload & Ganti Logo", type="primary", key="btn_logo"):
                img = Image.open(up_logo)
                target_logo = "logo_sekolah.png"
                img.save(target_logo) # Simpan file lokal (sebagai backup)
                
                # Konversi ke Base64 dan simpan di config
                config['logo_path'] = target_logo
                config['logo_base64'] = get_image_as_base64(target_logo)
                
                with open(FILE_SETTINGS, 'w') as f: json.dump(config, f)
                st.success("Logo berhasil diganti!")
                st.rerun()
    
    with col_set3:
        # Menambahkan fitur Pengaturan Background
        st.markdown("### Latar Belakang")
        # Menampilkan background yang sudah ada (menggunakan Base64 jika tersedia)
        if bg_base64_url:
            st.write("Latar Belakang Saat Ini:")
            # Tampilkan sebagai image di markdown untuk preview
            st.markdown(f'<img src="{bg_base64_url}" style="width:100%; height:auto;">', unsafe_allow_html=True)
        else:
            st.info("Belum ada gambar latar belakang.")

        up_bg = st.file_uploader("Ganti Latar Belakang (JPG/PNG)", type=['jpg', 'png', 'jpeg'], key="up_bg")

        if up_bg is not None:
            if st.button("Upload & Terapkan Latar Belakang", type="primary", key="btn_bg"):
                img = Image.open(up_bg).convert('RGB')
                target_bg = "background_img.jpg" 
                img.thumbnail((1000, 1000)) 
                img.save(target_bg) # Simpan file lokal (sebagai backup)
                
                # Konversi ke Base64 dan simpan di config
                config['background_image'] = target_bg
                config['bg_base64'] = get_image_as_base64(target_bg)
                
                with open(FILE_SETTINGS, 'w') as f: json.dump(config, f)
                st.success("Latar belakang berhasil diganti!")
                st.rerun()

