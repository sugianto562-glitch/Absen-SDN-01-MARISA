import streamlit as st
import pandas as pd
from datetime import datetime,timedelta
import os
import json
import urllib.parse
from PIL import Image # Library baru untuk memproses gambar

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Sistem SDN 01 MARISA", page_icon="🏫", layout="wide")

# --- 2. CSS CUSTOM ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #2c3e50; color: #white;
        text-align: center; padding: 10px; z-index: 999;
    }
    div[role="radiogroup"] {
        background-color: #ffffff; padding: 15px;
        border-radius: 10px; border-left: 6px solid #2980b9;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #2c3e50; font-weight: bold;
    }
    .stTextInput input {
        font-size: 24px; padding: 10px; text-align: center;
        border: 2px solid #2980b9; border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SETUP DATABASE & FOLDER ---
FILE_ABSEN = 'database_absen.csv'
FILE_SISWA = 'master_siswa.csv' 
FILE_SETTINGS = 'settings.json'
FOLDER_FOTO = 'foto_siswa' 

# Buat folder jika belum ada
if not os.path.exists(FOLDER_FOTO): os.makedirs(FOLDER_FOTO)

# DAFTAR KELAS
DAFTAR_KELAS = ["1A", "1B", "1C", "2A", "2B", "2C", "3A", "3B", "3C", "4A", "4B", "5A", "5B", "6A", "6B", "Guru/Staf"]

def init_csv(filename, columns):
    if not os.path.exists(filename):
        df = pd.DataFrame(columns=columns)
        df.to_csv(filename, index=False)
    else:
        df = pd.read_csv(filename)
        for col in columns:
            if col not in df.columns: df[col] = ""
        df.to_csv(filename, index=False)

init_csv(FILE_ABSEN, ['Tanggal', 'Jam', 'NISN', 'Nama', 'Kelas', 'Keterangan'])
init_csv(FILE_SISWA, ['NISN', 'Nama', 'Kelas', 'No_HP']) 

# CONFIG LOAD
def load_settings():
    defaults = {"nama_sekolah": "SDN 01 MARISA", "alamat_sekolah": "Jl. Pendidikan, Marisa", "logo_path": "logo_default.png"}
    if not os.path.exists(FILE_SETTINGS):
        return defaults
    try:
        with open(FILE_SETTINGS, 'r') as f: return json.load(f)
    except:
        return defaults

config = load_settings()

# FUNGSI WA
def buat_link_wa(nomor, pesan):
    nomor = str(nomor).strip().replace(".0", "").replace("-", "").replace(" ", "").replace("+", "")
    if nomor.startswith("0"): nomor = "62" + nomor[1:]
    return f"https://api.whatsapp.com/send?phone={nomor}&text={urllib.parse.quote(pesan)}"

# --- 4. LOGIC LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login_screen():
    st.markdown("""<style>.stApp {background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=2070"); background-size: cover;}</style>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align:center; color:white;'>🔐 LOGIN SISTEM</h2>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='text-align:center; color:#00a8cc;'>{config['nama_sekolah']}</h4>", unsafe_allow_html=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("MASUK", type="primary", use_container_width=True):
                if u == "admin" and p == "4050715":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Gagal Login")
            st.markdown("<hr><center style='color:white;'>Creativity by <b>Sugianto</b></center>", unsafe_allow_html=True)

if not st.session_state['logged_in']:
    login_screen()
    st.stop()

# --- 5. TAMPILAN UTAMA ---
st.markdown("""<style>.stApp {background-image: none; background-color: #ffffff;}</style>""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    # Logic Tampilan Logo
    logo_file = config.get('logo_path', 'logo_default.png')
    if os.path.exists(logo_file):
        st.image(logo_file, width=100)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=80)
        
    st.title(config['nama_sekolah'])
    st.write(config['alamat_sekolah'])
    st.markdown("---")
    # Menu Navigasi
    menu = st.radio("MENU UTAMA", [
        "🖥️ Absensi (Scan)", 
        "📊 Laporan & Persentase", 
        "📂 Data Master", 
        "📸 Upload Foto",  # <-- Menu Baru Ditambahkan
        "⚙️ Pengaturan"
    ])
    st.markdown("---")
    st.info("Creativity by:\n*Sugianto*\nSDN 01 MARISA")
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

# FOOTER
st.markdown("""
    <div class="footer">
            <marquee direction="right" scrollamount="6">
            Sistem Informasi Sekolah Digital — Designed with ❤️ by <b>Sugianto (SDN 01 MARISA)</b>
        </marquee>
    </div>
""", unsafe_allow_html=True)

# --- KONTEN MENU ---

# A. MENU SCAN ABSENSI
if menu == "🖥️ Absensi (Scan)":
   # Tambah 8 jam dari waktu server (UTC) ke WITA
now = datetime.now() + timedelta(hours=8)
    c1, c2 = st.columns([3,1])
    c1.title("Scan Absensi SDN 01 MARISA")
    c1.markdown(f"#### 📆 {now.strftime('%A, %d %B %Y')}")
    c2.metric("Jam", now.strftime("%H:%M:%S"))
    st.divider()
    
    st.markdown("### 👇 PILIH MODE & SCAN KARTU")
    with st.container(border=True):
        cr, ci = st.columns([1, 2])
        with cr:
            st.write("🔴 STATUS:")
            mode_absen = st.radio("Pilih:", ["DATANG (Hadir)", "PULANG"], horizontal=True, label_visibility="collapsed")
        with ci:
            st.write("⌨️ SCAN DISINI:")
            nisn_input = st.text_input("Input NISN:", key="scan_main", label_visibility="collapsed").strip()

    if nisn_input:
        df_siswa = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
        siswa = df_siswa[df_siswa['NISN'] == nisn_input]
        
        if not siswa.empty:
            nama_s = siswa.iloc[0]['Nama']
            kelas_s = siswa.iloc[0]['Kelas']
            hp_s = siswa.iloc[0]['No_HP']
            ket_fix = "Hadir" if "DATANG" in mode_absen else "Pulang"
            
            df_absen = pd.read_csv(FILE_ABSEN)
            # Cek duplikasi absen di hari yang sama (opsional)
            sudah_absen = df_absen[(df_absen['Tanggal'] == now.strftime("%Y-%m-%d")) & 
                                   (df_absen['NISN'] == nisn_input) & 
                                   (df_absen['Keterangan'] == ket_fix)]
            
            if not sudah_absen.empty:
                st.warning(f"⚠️ {nama_s} Sudah absen {ket_fix} hari ini!")
            else:
                baru = {'Tanggal': now.strftime("%Y-%m-%d"), 'Jam': now.strftime("%H:%M:%S"), 
                        'NISN': nisn_input, 'Nama': nama_s, 'Kelas': kelas_s, 'Keterangan': ket_fix}
                df_absen = pd.concat([df_absen, pd.DataFrame([baru])], ignore_index=True)
                df_absen.to_csv(FILE_ABSEN, index=False)
                
                c_foto, c_teks = st.columns([1,3])
                with c_foto:
                    path_foto = f"{FOLDER_FOTO}/{nisn_input}.jpg"
                    if os.path.exists(path_foto): st.image(path_foto, width=150)
                    else: st.image("https://via.placeholder.com/150?text=No+Image", width=150)
                
                with c_teks:
                    st.success(f"✅ SUKSES: {nama_s}")
                    st.markdown(f"*{ket_fix}* | Pukul: {now.strftime('%H:%M')}")
                    pesan = f"Assalamualaikum. Siswa a.n {nama_s} ({kelas_s}) telah {ket_fix.upper()} pada pukul {now.strftime('%H:%M')}."
                    if str(hp_s) != "nan" and len(str(hp_s)) > 5:
                        st.link_button("📲 KIRIM WA", buat_link_wa(hp_s, pesan))
        else:
            st.error("❌ Data Siswa Tidak Ditemukan!")
 # --- FITUR MANUAL (SAKIT/IZIN) ---
    st.markdown("---")
    with st.expander("📝 Input Siswa Tidak Hadir (Sakit/Izin/Alpa)"):
        with st.form("manual"):
            df_s = pd.read_csv(FILE_SISWA)
            pilih = st.selectbox("Nama Siswa:", df_s['NISN'].astype(str) + " - " + df_s['Nama'])
            ket = st.selectbox("Keterangan:", ["Sakit", "Izin", "Alpa"])
            if st.form_submit_button("Simpan Data Manual"):
                nisn_m = pilih.split(" - ")[0]
                nm = df_s[df_s['NISN']==nisn_m].iloc[0]['Nama']
                kls = df_s[df_s['NISN']==nisn_m].iloc[0]['Kelas']
                
                df_a = pd.read_csv(FILE_ABSEN)
                b = {'Tanggal': now.strftime("%Y-%m-%d"), 'Jam': now.strftime("%H:%M:%S"), 
                     'NISN': nisn_m, 'Nama': nm, 'Kelas': kls, 'Keterangan': ket}
                df_a = pd.concat([df_a, pd.DataFrame([b])], ignore_index=True)
                df_a.to_csv(FILE_ABSEN, index=False)
                st.success(f"Tersimpan: {nm} - {ket}")

# B. MENU LAPORAN
elif menu == "📊 Laporan & Persentase":
    st.title("Laporan Kehadiran")
    tgl = st.date_input("Pilih Tanggal:", datetime.now())
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
            final['% Hadir'] = (final['Hadir'] / final['Total_Siswa'] * 100).round(1).astype(str) + "%"
            
            cols = ['Total_Siswa', 'Hadir', 'Sakit', 'Izin', 'Alpa']
            final[cols] = final[cols].astype(int)
            
            st.dataframe(final, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data absensi hari ini.")
    else:
        st.warning("Data Master Siswa Kosong.")

# C. DATA MASTER
elif menu == "📂 Data Master":
    st.title("Data Master Siswa")
    tab1, tab2 = st.tabs(["➕ Tambah Data", "✏️ Edit / Hapus"])
    
    with tab1:
        with st.form("add"):
            c1, c2 = st.columns(2)
            n_nisn = c1.text_input("NISN").strip()
            n_nama = c2.text_input("Nama")
            n_kelas = c1.selectbox("Kelas", DAFTAR_KELAS)
            n_hp = c2.text_input("No HP")
            if st.form_submit_button("Simpan"):
                df = pd.read_csv(FILE_SISWA, dtype={'NISN': str})
                if n_nisn in df['NISN'].values:
                    st.error("NISN Sudah Ada!")
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

# D. UPLOAD FOTO (YANG DIPERBAIKI)
elif menu == "📸 Upload Foto":
    st.title("📸 Upload Foto Siswa")
    st.info("Pilih siswa terlebih dahulu, lalu upload foto mereka.")
    
    # 1. Pilih Siswa Dulu (Biar gak salah upload)
    df_s = pd.read_csv(FILE_SISWA, dtype={'NISN':str})
    if not df_s.empty:
        # Buat list pencarian
        list_siswa = df_s['NISN'] + " - " + df_s['Nama'] + " (" + df_s['Kelas'] + ")"
        cari_siswa = st.selectbox("Cari Siswa:", list_siswa)
        
        if cari_siswa:
            nisn_target = cari_siswa.split(" - ")[0] # Ambil NISN
            nama_target = cari_siswa.split(" - ")[1].split(" (")[0]
            
            # Tampilkan foto saat ini jika ada
            path_now = f"{FOLDER_FOTO}/{nisn_target}.jpg"
            col_kiri, col_kanan = st.columns([1, 2])
            
            with col_kiri:
                st.write("Foto Saat Ini:")
                if os.path.exists(path_now):
                    st.image(path_now, width=150, caption=nama_target)
                else:
                    st.warning("Belum ada foto")
            
            with col_kanan:
                st.write("Upload Foto Baru:")
                file_foto = st.file_uploader(f"Upload untuk {nama_target}", type=['jpg', 'png', 'jpeg'])
                
                if file_foto is not None:
                    if st.button("💾 Simpan Foto", type="primary"):
                        try:
                            # Proses Gambar menggunakan PIL
                            image = Image.open(file_foto)
                            image = image.convert('RGB') # Pastikan format warna benar
                            image.thumbnail((400, 400)) # Resize biar file tidak terlalu besar
                            
                            # Simpan dengan nama NISN.jpg
                            save_path = os.path.join(FOLDER_FOTO, f"{nisn_target}.jpg")
                            image.save(save_path)
                            
                            st.success(f"Foto {nama_target} berhasil disimpan!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Terjadi kesalahan: {e}")
    else:
        st.warning("Data siswa kosong. Silakan isi data master dulu.")

# E. PENGATURAN (YANG DIPERBAIKI)
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
        # Tampilkan logo saat ini
        curr_logo = config.get('logo_path', '')
        if curr_logo and os.path.exists(curr_logo):
            st.image(curr_logo, width=100, caption="Logo Aktif")
        
        # Upload Logo Baru
        up_logo = st.file_uploader("Ganti Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        if up_logo is not None:
            if st.button("Upload & Ganti Logo"):
                try:
                    img = Image.open(up_logo)
                    # Simpan file dengan nama tetap 'logo_sekolah.png' agar rapi
                    target_logo = "logo_sekolah.png"
                    img.save(target_logo)
                    
                    # Update config
                    config['logo_path'] = target_logo
                    with open(FILE_SETTINGS, 'w') as f: json.dump(config, f)
                    
                    st.success("Logo berhasil diganti!")
                    st.rerun()
                except Exception as e:

                    st.error(f"Gagal simpan logo: {e}")
