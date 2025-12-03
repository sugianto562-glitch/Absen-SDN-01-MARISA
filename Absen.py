import streamlit as st
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

# --- Import Library Kamera & Airtable ---
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
from pyairtable import Api

# ==============================================================================
# ⚙️ KONFIGURASI AIRTABLE (WAJIB DIISI)
# ==============================================================================
AIRTABLE_API_KEY = "patXXXXXXXXXXXX..."       # Ganti dengan Token Anda
AIRTABLE_BASE_ID = "appXXXXXXXXXXXX..."       # Ganti dengan Base ID Anda
AIRTABLE_TABLE_NAME = "Table 1"               # Ganti dengan Nama Tabel

def kirim_ke_airtable(data_dict):
    try:
        if "patXXXX" in AIRTABLE_API_KEY: return False 
        api = Api(AIRTABLE_API_KEY)
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
        table.create(data_dict)
        return True
    except Exception as e:
        print(f"Error Airtable: {e}")
        return False

# --- 0. FUNGSI KAMERA (Callback) ---
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    decoded_objects = decode(img)
    for obj in decoded_objects:
        data = obj.data.decode("utf-8")
        points = obj.polygon
        if len(points) == 4: pts = points
        else: pts = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
        n = len(pts)
        for j in range(0, n):
            cv2.line(img, pts[j], pts[(j + 1) % n], (0, 255, 0), 3)
        cv2.putText(img, data, (pts[0].x, pts[0].y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return av.VideoFrame.from_ndarray(img, format="bgr24")

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Sistem SDN 01 MARISA", page_icon="🏫", layout="wide")

st.markdown("""
    <style>
    .stApp, p, h1, h2, h3, h4, label, .stMarkdown, span {color: #000000 !important; text-shadow: none !important;}
    .stApp { background-color: #f0f2f6; }
    .footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #000000 !important; color: #ffffff !important; text-align: center; padding: 10px; z-index: 999;}
    .footer p, .footer span { color: #ffffff !important; }
    .stTextInput input {background-color: #ffffff !important; color: #000000 !important; border: 2px solid #000000 !important; font-weight: bold;}
    div[role="radiogroup"] {background-color: #ffffff !important; color: #000000 !important; border: 1px solid #000000; padding: 5px; border-radius: 5px;}
    </style>
""", unsafe_allow_html=True)

# --- 2. SETUP DATABASE & FOLDER (MODIFIKASI ANTI ERROR) ---
FILE_ABSEN = 'database_absen.csv'
FILE_SISWA = 'master_siswa.csv' 
FILE_SETTINGS = 'settings.json'
FOLDER_FOTO = 'foto_siswa' 

if not os.path.exists(FOLDER_FOTO): os.makedirs(FOLDER_FOTO)

DAFTAR_KELAS = ["1A", "1B", "1C", "2A", "2B", "2C", "3A", "3B", "3C", "4A", "4B", "5A", "5B", "6A", "6B", "Guru/Staf"]

# --- FUNGSI INI SUDAH DIPERBAIKI AGAR KEBAL FILE KOSONG ---
def init_csv(filename, columns):
    try:
        # Cek apakah file ada
        if not os.path.exists(filename):
            raise FileNotFoundError
        
        # Coba baca file
        df = pd.read_csv(filename)
        
        # Cek kelengkapan kolom
        for col in columns:
            if col not in df.columns: df[col] = ""
        df.to_csv(filename, index=False)
        
    except (FileNotFoundError, pd.errors.EmptyDataError):
        # Jika file tidak ada ATAU kosong/rusak, buat baru
        df = pd.DataFrame(columns=columns)
        df.to_csv(filename, index=False)

init_csv(FILE_ABSEN, ['Tanggal', 'Jam', 'NISN', 'Nama', 'Kelas', 'Keterangan'])
init_csv(FILE_SISWA, ['NISN', 'Nama', 'Kelas', 'No_HP']) 

def load_settings():
    defaults = {"nama_sekolah": "SDN 01 MARISA", "alamat_sekolah": "Jl. Pendidikan, Marisa", "logo_path": "logo_default.png"}
    if not os.path.exists(FILE_SETTINGS): return defaults
    try:
        with open(FILE_SETTINGS, 'r') as f: return json.load(f)
    except: return defaults

config = load_settings()

def buat_link_wa(nomor, pesan):
    nomor = str(nomor).strip().replace(".0", "").replace("-", "").replace(" ", "").replace("+", "")
    if nomor.startswith("0"): nomor = "62" + nomor[1:]
    return f"https://api.whatsapp.com/send?phone={nomor}&text={urllib.parse.quote(pesan)}"

# --- 3. LOGIC LOGIN ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

def login_screen():
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
st.markdown("""<style>.stApp {background-image: none; background-color: #ffffff;}</style>""", unsafe_allow_html=True)

with st.sidebar:
    logo_file = config.get('logo_path', 'logo_default.png')
    if os.path.exists(logo_file): st.image(logo_file, width=100)
    else: st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=80)
    st.title(config['nama_sekolah'])
    st.write(config['alamat_sekolah'])
    st.markdown("---")
    menu = st.radio("MENU UTAMA", ["🖥️ Absensi (Scan)", "📊 Laporan & Persentase", "📂 Data Master", "📸 Upload Foto", "⚙️ Pengaturan"])
    st.markdown("---")
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

st.markdown("""<div class="footer"><marquee direction="right" scrollamount="6"><span>Sistem Informasi Sekolah Digital — Designed with ❤️ by <b>Sugianto (SDN 01 MARISA)</b></span></marquee></div>""", unsafe_allow_html=True)

# --- A. MENU SCAN ABSENSI ---
if menu == "🖥️ Absensi (Scan)":
    now = datetime.now() + timedelta(hours=8)
    c1, c2 = st.columns([3,1])
    c1.title("Scan Absensi")
    c1.markdown(f"#### 📆 {now.strftime('%A, %d %B %Y')}")
    c2.metric("Jam (WITA)", now.strftime("%H:%M:%S"))
    st.divider()
    
    col_cam, col_input = st.columns([1, 1])
    with col_cam:
        # KONFIGURASI STUN SERVER
        rtc_configuration = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
        webrtc_streamer(key="barcode-scanner", mode=WebRtcMode.SENDRECV, rtc_configuration=rtc_configuration, video_frame_callback=video_frame_callback, media_stream_constraints={"video": True, "audio": False}, async_processing=True)
        st.caption("Arahkan kartu ke kamera.")

    with col_input:
        st.markdown("### 👇 INPUT MANUAL / HASIL SCAN")
        with st.container(border=True):
            st.write("🔴 STATUS:")
            mode_absen = st.radio("Pilih Mode:", ["DATANG (Hadir)", "PULANG"], horizontal=True, label_visibility="collapsed")
            st.write("⌨️ MASUKKAN NISN:")
            nisn_input = st.text_input("Ketik NISN lalu Enter:", key="scan_main").strip()

    if nisn_input:
        df_siswa = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
        siswa = df_siswa[df_siswa['NISN'] == nisn_input]
        if not siswa.empty:
            nama_s = siswa.iloc[0]['Nama']
            kelas_s = siswa.iloc[0]['Kelas']
            hp_s = siswa.iloc[0]['No_HP']
            ket_fix = "Hadir" if "DATANG" in mode_absen else "Pulang"
            df_absen = pd.read_csv(FILE_ABSEN)
            sudah_absen = df_absen[(df_absen['Tanggal'] == now.strftime("%Y-%m-%d")) & (df_absen['NISN'] == nisn_input) & (df_absen['Keterangan'] == ket_fix)]
            
            if not sudah_absen.empty: st.warning(f"⚠️ {nama_s} Sudah absen {ket_fix} hari ini!")
            else:
                baru = {'Tanggal': now.strftime("%Y-%m-%d"), 'Jam': now.strftime("%H:%M:%S"), 'NISN': nisn_input, 'Nama': nama_s, 'Kelas': kelas_s, 'Keterangan': ket_fix}
                df_absen = pd.concat([df_absen, pd.DataFrame([baru])], ignore_index=True)
                df_absen.to_csv(FILE_ABSEN, index=False)
                
                with st.spinner("Mengirim ke Airtable..."):
                    dt_kirim = {"Tanggal": now.strftime("%Y-%m-%d"), "Jam": now.strftime("%H:%M:%S"), "NISN": nisn_input, "Nama": nama_s, "Kelas": kelas_s, "Keterangan": ket_fix}
                    sukses = kirim_ke_airtable(dt_kirim)
                    if sukses: st.toast("✅ Tersimpan di Airtable!", icon="☁️")
                    else: st.warning("⚠️ Tersimpan Lokal, Gagal Airtable.")

                c_foto, c_teks = st.columns([1,3])
                with c_foto:
                    path_foto = f"{FOLDER_FOTO}/{nisn_input}.jpg"
                    if os.path.exists(path_foto): st.image(path_foto, width=150)
                    else: st.image("https://via.placeholder.com/150?text=No+Image", width=150)
                with c_teks:
                    st.success(f"✅ SUKSES: {nama_s}")
                    st.markdown(f"{ket_fix} | Pukul: {now.strftime('%H:%M')}")
                    pesan = f"Assalamualaikum. Siswa a.n {nama_s} ({kelas_s}) telah {ket_fix.upper()} pada pukul {now.strftime('%H:%M')}."
                    if str(hp_s) != "nan" and len(str(hp_s)) > 5: st.link_button("📲 KIRIM WA", buat_link_wa(hp_s, pesan))
        else: st.error("❌ Data Siswa Tidak Ditemukan!")

    st.markdown("---")
    with st.expander("📝 Input Siswa Tidak Hadir (Sakit/Izin/Alpa)"):
        with st.form("manual"):
            df_s = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
            if not df_s.empty: pilih = st.selectbox("Nama Siswa:", df_s['NISN'] + " - " + df_s['Nama'])
            else: pilih = ""
            ket = st.selectbox("Keterangan:", ["Sakit", "Izin", "Alpa"])
            if st.form_submit_button("Simpan Data Manual"):
                if pilih:
                    nisn_m = pilih.split(" - ")[0]
                    nm = df_s[df_s['NISN']==nisn_m].iloc[0]['Nama']
                    kls = df_s[df_s['NISN']==nisn_m].iloc[0]['Kelas']
                    df_a = pd.read_csv(FILE_ABSEN)
                    b = {'Tanggal': now.strftime("%Y-%m-%d"), 'Jam': now.strftime("%H:%M:%S"), 'NISN': nisn_m, 'Nama': nm, 'Kelas': kls, 'Keterangan': ket}
                    df_a = pd.concat([df_a, pd.DataFrame([b])], ignore_index=True)
                    df_a.to_csv(FILE_ABSEN, index=False)
                    kirim_ke_airtable({"Tanggal": now.strftime("%Y-%m-%d"), "Jam": now.strftime("%H:%M:%S"), "NISN": nisn_m, "Nama": nm, "Kelas": kls, "Keterangan": ket})
                    st.success(f"Tersimpan: {nm} - {ket}")

# --- B. MENU LAPORAN ---
elif menu == "📊 Laporan & Persentase":
    st.title("📊 Laporan & Download Data")
    col_tgl, col_space = st.columns([1, 2])
    with col_tgl: tgl = st.date_input("Pilih Tanggal Laporan:", datetime.now())
    
    df_a = pd.read_csv(FILE_ABSEN)
    df_s = pd.read_csv(FILE_SISWA)
    data_harian = df_a[df_a['Tanggal'] == tgl.strftime("%Y-%m-%d")]
    
    if not df_s.empty:
        total_siswa = df_s.groupby('Kelas').size().reset_index(name='Total_Siswa')
        if not data_harian.empty:
            rekap = data_harian.groupby(['Kelas', 'Keterangan']).size().unstack(fill_value=0).reset_index()
            for k in ['Hadir', 'Sakit', 'Izin', 'Alpa']:
                if k not in rekap.columns: rekap[k] = 0
            final = pd.merge(total_siswa, rekap, on='Kelas', how='left').fillna(0)
            final['Persentase_Hadir'] = (final['Hadir'] / final['Total_Siswa'] * 100).round(1)
            final['Ket_Persen'] = final['Persentase_Hadir'].astype(str) + "%"
            cols_int = ['Total_Siswa', 'Hadir', 'Sakit', 'Izin', 'Alpa']
            final[cols_int] = final[cols_int].astype(int)
            st.markdown("### 1. Rekapitulasi Per Kelas")
            st.dataframe(final[['Kelas', 'Total_Siswa', 'Hadir', 'Sakit', 'Izin', 'Alpa', 'Ket_Persen']], use_container_width=True, hide_index=True)
            st.markdown("### 2. Detail Siswa Absen Hari Ini")
            st.dataframe(data_harian[['Jam', 'Nama', 'Kelas', 'Keterangan']], use_container_width=True, hide_index=True)
            st.divider()
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                final.to_excel(writer, sheet_name='Rekap_Persentase', index=False)
                data_harian.to_excel(writer, sheet_name='Detail_Absensi', index=False)
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
    with tab2:
        df = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
        if not df.empty:
            pilih = st.selectbox("Cari Siswa:", df['NISN'] + " - " + df['Nama'])
            nisn_pilih = pilih.split(" - ")[0]
            data = df[df['NISN'] == nisn_pilih].iloc[0]
            with st.form("edit"):
                e_nama = st.text_input("Nama", data['Nama'])
                e_kelas = st.selectbox("Kelas", DAFTAR_KELAS, index=DAFTAR_KELAS.index(data['Kelas']) if data['Kelas'] in DAFTAR_KELAS else 0)
                e_hp = st.text_input("HP", str(data['No_HP']))
                c_sv, c_del = st.columns(2)
                if c_sv.form_submit_button("Update Data"):
                    df.loc[df['NISN'] == nisn_pilih, ['Nama', 'Kelas', 'No_HP']] = [e_nama, e_kelas, e_hp]
                    df.to_csv(FILE_SISWA, index=False)
                    st.success("Update Berhasil")
                    st.rerun()
                if c_del.form_submit_button("Hapus Siswa", type="primary"):
                    df = df[df['NISN'] != nisn_pilih]
                    df.to_csv(FILE_SISWA, index=False)
                    st.rerun()

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
                if os.path.exists(path_now): st.image(path_now, width=150)
                else: st.warning("Belum ada foto")
            with col_kanan:
                file_foto = st.file_uploader(f"Upload untuk {nama_target}", type=['jpg', 'png', 'jpeg'])
                if file_foto is not None:
                    if st.button("💾 Simpan Foto", type="primary"):
                        image = Image.open(file_foto).convert('RGB')
                        image.thumbnail((400, 400))
                        image.save(os.path.join(FOLDER_FOTO, f"{nisn_target}.jpg"))
                        st.success("Foto berhasil disimpan!")
                        st.rerun()
    else: st.warning("Data Master Kosong.")

# --- E. MENU PENGATURAN ---
elif menu == "⚙️ Pengaturan":
    st.title("Pengaturan Sekolah")
    col_set1, col_set2 = st.columns(2)
    with col_set1:
        st.markdown("### Identitas Sekolah")
        with st.form("setting_sekolah"):
            new_nama = st.text_input("Nama Sekolah", config['nama_sekolah'])
            new_alamat = st.text_input("Alamat Sekolah", config['alamat_sekolah'])
            if st.form_submit_button("Simpan Identitas"):
                config['nama_sekolah'] = new_nama
                config['alamat_sekolah'] = new_alamat
                with open(FILE_SETTINGS, 'w') as f: json.dump(config, f)
                st.success("Identitas tersimpan!")
                st.rerun()
    with col_set2:
        st.markdown("### Logo Sekolah")
        curr_logo = config.get('logo_path', '')
        if curr_logo and os.path.exists(curr_logo): st.image(curr_logo, width=100)
        up_logo = st.file_uploader("Ganti Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        if up_logo is not None:
            if st.button("Upload & Ganti Logo"):
                img = Image.open(up_logo)
                target_logo = "logo_sekolah.png"
                img.save(target_logo)
                config['logo_path'] = target_logo
                with open(FILE_SETTINGS, 'w') as f: json.dump(config, f)
                st.success("Logo berhasil diganti!")
                st.rerun()
