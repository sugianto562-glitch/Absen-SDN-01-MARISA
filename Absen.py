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
import base64 # 💡 BARU: Import untuk Base64

# ==============================================================================
# ⚙️ KONFIGURASI AIRTABLE (WAJIB DIISI)
# ==============================================================================
AIRTABLE_API_KEY = st.secrets["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID = "appJSVM6gP8cuSnKZ" 
AIRTABLE_TABLE_NAME = "Table 1"        

def kirim_ke_airtable(data_dict):
    """Fungsi untuk mengirim data ke Airtable."""
    # (Fungsi ini tidak diubah)
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
    # (Fungsi ini tidak diubah)
    # ...
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

# --- PENTING: Style Dasar CSS (TANPA LOGIKA 'menu') dipindahkan ke atas
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
    # (Fungsi ini tidak diubah)
    # ...
    try:
        if not os.path.exists(filename): raise FileNotFoundError
        df = pd.read_csv(filename, dtype={'NISN': str}) 
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
    # ⚠️ PERUBAHAN: Menambahkan 'logo_base64' dan 'bg_base64'
    defaults = {
        "nama_sekolah": "SDN 01 MARISA", 
        "alamat_sekolah": "Jl. Pendidikan, Marisa", 
        "logo_path": "logo_default.png", 
        "background_image": None,
        "logo_base64": None, # Akan menyimpan string Base64 logo
        "bg_base64": None    # Akan menyimpan string Base64 background
    }
    if not os.path.exists(FILE_SETTINGS): return defaults
    try:
        with open(FILE_SETTINGS, 'r') as f: return {**defaults, **json.load(f)}
    except: return defaults

config = load_settings()

def buat_link_wa(nomor, pesan):
    # (Fungsi ini tidak diubah)
    # ...
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

# 💡 PERBAIKAN: Ambil Base64 dari config
bg_base64_url = config.get('bg_base64')
logo_base64_url = config.get('logo_base64')

# Pindahkan LOGIC menu ke dalam sidebar
with st.sidebar:
    # ⚠️ PERUBAHAN: Menggunakan Base64 untuk logo
    if logo_base64_url:
        st.markdown(f'<img src="{logo_base64_url}" width="100">', unsafe_allow_html=True)
    elif os.path.exists(config.get('logo_path', '')):
        st.image(config['logo_path'], width=100) # Fallback jika Base64 belum tersimpan
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

# ⚠️ LOGIKA BACKGROUND DENGAN BASE64
if st.session_state['logged_in']:
    if menu == "🖥️ Absensi (Scan)":
        # Untuk menu scan, gunakan background putih polos
        bg_style = ".stApp {background-image: none; background-color: #ffffff;}"
    elif bg_base64_url:
        # 💡 GUNAKAN BASE64 URL DI CSS
        bg_style = f".stApp {{background-image: linear-gradient(rgba(255,255,255,0.8), rgba(255,255,255,0.8)), url('{bg_base64_url}'); background-size: cover; background-attachment: fixed;}}"
    else:
        # Gunakan background-color default jika tidak ada gambar
        bg_style = ".stApp {background-image: none; background-color: #f0f2f6;}"
    
    # Terapkan CSS background
    st.markdown(f"""<style>{bg_style}</style>""", unsafe_allow_html=True)
# -------------------------------------------------------------

st.markdown("""<div class="footer"><marquee direction="right" scrollamount="6"><span>Sistem Informasi Sekolah Digital — Designed with ❤️ by <b>Sugianto (SDN 01 MARISA)</b></span></marquee></div>""", unsafe_allow_html=True)


# --- A. MENU SCAN ABSENSI ---
if menu == "🖥️ Absensi (Scan)":
    # (Logika di menu ini tidak diubah)
    # ... (kode menu A)
    
# --- B. MENU LAPORAN & PERSENTASE ---
elif menu == "📊 Laporan & Persentase":
    # (Logika di menu ini tidak diubah)
    # ... (kode menu B)

# --- C. MENU DATA MASTER ---
elif menu == "📂 Data Master":
    # (Logika di menu ini tidak diubah)
    # ... (kode menu C)

# --- D. MENU UPLOAD FOTO ---
elif menu == "📸 Upload Foto":
    # (Logika di menu ini tidak diubah)
    # ... (kode menu D)

# --- F. MENU LINK WA WALI MURID ---
elif menu == "🔗 Link WA Wali Murid":
    # (Logika di menu ini sudah mencakup perbaikan Attribute dan Name Error)
    st.title("🔗 Kirim Pesan WA ke Wali Murid")
    st.info("Fitur ini membantu Anda mengirimkan pesan WhatsApp (WA) kepada wali murid per kelas secara cepat (satu per satu).")

    df_s = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
    
    if df_s.empty:
        st.warning("Data Master Siswa kosong. Silakan isi Data Master terlebih dahulu.")
    else:
        kelas_pilih = st.selectbox("Pilih Kelas:", ["-- Pilih Semua --"] + sorted(df_s['Kelas'].unique().tolist()))
        
        if kelas_pilih != "-- Pilih Semua --":
            df_filter = df_s[df_s['Kelas'] == kelas_pilih].copy()
            st.markdown(f"### Daftar Siswa Kelas {kelas_pilih}")
        else:
            df_filter = df_s.copy()
            st.markdown("### Daftar Seluruh Siswa")

        st.markdown("---")
        pesan_default = f"Assalamualaikum, Bapak/Ibu Wali Murid.\nKami dari {config['nama_sekolah']} ingin menyampaikan informasi: ...."
        pesan_input = st.text_area("Tulis Pesan yang Akan Dikirim:", value=pesan_default, height=150)

        if not df_filter.empty:
            
            data_tampil = df_filter[['Nama', 'Kelas', 'No_HP']].copy()
            data_tampil['No_HP'] = data_tampil['No_HP'].apply(lambda x: str(x).replace(".0", "").strip() if pd.notna(x) else "")
            
            def generate_wa_link_button(row):
                nomor = row['No_HP']
                # 💡 PERBAIKAN 'nommor' sudah diimplementasikan di sini (menggunakan 'nomor')
                if len(str(nomor).replace(" ", "")) > 8:
                    pesan_personalized = f"Kepada Wali dari ananda {row['Nama']} ({row['Kelas']}),\n\n{pesan_input}"
                    link = buat_link_wa(nomor, pesan_personalized)
                    if link:
                        return f"[📲 Kirim WA](<{link}>)"
                return "❌ No HP Invalid/Kosong"

            data_tampil['Link WA'] = data_tampil.apply(generate_wa_link_button, axis=1)

            # 💡 PERBAIKAN: Memastikan column_config dihilangkan untuk menghindari AttributeError
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
                
                # 💡 PERUBAHAN: Konversi ke Base64 dan simpan di config
                config['logo_path'] = target_logo
                config['logo_base64'] = get_image_as_base64(target_logo)
                
                with open(FILE_SETTINGS, 'w') as f: json.dump(config, f)
                st.success("Logo berhasil diganti!")
                st.rerun()
    
    with col_set3:
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
                
                # 💡 PERUBAHAN: Konversi ke Base64 dan simpan di config
                config['background_image'] = target_bg
                config['bg_base64'] = get_image_as_base64(target_bg)
                
                with open(FILE_SETTINGS, 'w') as f: json.dump(config, f)
                st.success("Latar belakang berhasil diganti!")
                st.rerun()
