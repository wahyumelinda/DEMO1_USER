import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time

st.set_page_config(page_title="Tambah Data ke Sheet ALL", page_icon="📝", layout="wide")

st.markdown(
        """
        <h1 style='text-align: center; color: white; background-color: #A9DFBF; padding: 15px; border-radius: 10px;'>
            ➕ Tambah Data Preventive
        </h1>
        """,
        unsafe_allow_html=True
    )

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxTyxQcbH8j9WU4z7wJ0kdyrZHW634jdRePF7O6G6mKum1sPYOnWB8vjQvWXsBINebK/exec"

# URL dari Apps Script Web App
API_URL = "https://script.google.com/macros/s/AKfycbwa3o66ObBb656Iye9vZkBp2-M1LUJdHdL8RKCadDCnFDhyGombHV5B7-KvaY2XOD7w1g/exec"

# Pilihan sheet yang bisa ditampilkan
option = st.selectbox("📂 Pilih Data yang Ingin Dilihat:", ["Data Preventive", "Data SPK"])

# Ambil data sesuai pilihan
if option == "Data Preventive":
    response = requests.get(f"{API_URL}?action=get_all_data")
    expected_columns = [
        "ID", "BU", "Line", "Produk", "Nomor Mesin", "Mesin", "Tanggal Pengerjaan",
        "Mulai", "Selesai", "Masalah", "Tindakan Perbaikan", "Deskripsi",
        "Quantity", "PIC", "Kondisi", "Alasan", "SPV", "Last Update SPV", 
        "Approve", "Reason", "SM", "Last Update SM"
    ]
elif option == "Data SPK":
    response = requests.get(f"{API_URL}?action=get_data")
    expected_columns = [
        "ID", "BU", "Line", "Produk", "Nomor Mesin", "Mesin",
        "Masalah", "Tindakan Perbaikan", "Tanggal Pengerjaan", "PIC", "Last Update"
    ]

# Cek apakah API berhasil mendapatkan data
if response.status_code == 200:
    all_data = response.json()
    
    if isinstance(all_data, list) and len(all_data) > 0:
        df = pd.DataFrame(all_data)
        df = df[[col for col in expected_columns if col in df.columns]]

        # Pastikan nama kolom tanggal sesuai
        if "Tanggal Pengerjaan" in df.columns:
            df["Tanggal Pengerjaan"] = pd.to_datetime(df["Tanggal Pengerjaan"], errors='coerce').dt.date
            df = df.rename(columns={"Tanggal Pengerjaan": "Tanggal"})
        else:
            st.error("Kolom 'Tanggal Pengerjaan' tidak ditemukan dalam data API!")

        # === Fungsi untuk Filter ===
        def filter_data(df):
            st.sidebar.header("Filter Data (Opsional)")
            
            # Filter berdasarkan PIC
            pic_options = df["PIC"].dropna().unique().tolist()
            selected_pic = st.sidebar.multiselect("Pilih PIC", pic_options)
            
            # Filter berdasarkan rentang tanggal
            min_date, max_date = df["Tanggal"].min(), df["Tanggal"].max()
            date_range = st.sidebar.date_input("Pilih Rentang Tanggal", [min_date, max_date], min_value=min_date, max_value=max_date)
            
            # Terapkan filter
            df_filtered = df.copy()
            if selected_pic:
                df_filtered = df_filtered[df_filtered["PIC"].isin(selected_pic)]
            if len(date_range) == 2:
                start_date, end_date = date_range
                df_filtered = df_filtered[(df_filtered["Tanggal"] >= start_date) & (df_filtered["Tanggal"] <= end_date)]
            
            return df_filtered
        
        df_filtered = filter_data(df)
        
        # === Pagination ===
        items_per_page = 10
        total_pages = max(1, -(-len(df_filtered) // items_per_page))
        page_number = st.sidebar.number_input("Pilih Halaman", min_value=1, max_value=total_pages, value=1, step=1)
        
        start_idx = (page_number - 1) * items_per_page
        end_idx = start_idx + items_per_page
        df_paginated = df_filtered.iloc[start_idx:end_idx]
        
        # === Tampilkan Data ===
        st.subheader(f"{option} (Menampilkan Halaman {page_number} dari {total_pages})")
        st.dataframe(df_paginated, use_container_width=True)
        st.caption(f"Menampilkan {len(df_paginated)} dari {len(df_filtered)} data yang tersedia.")
        
         # === Tambahkan Fitur Expander untuk Detail Tindakan Perbaikan ===
        if "ID" in df_filtered.columns:
            selected_id_expander = st.selectbox("🔍 Lihat Detail Tindakan Perbaikan Berdasarkan ID", df_filtered["ID"].unique())
            selected_id_expander = str(selected_id_expander)
            tindakan_perbaikan_filtered = df_filtered[df_filtered["ID"] == selected_id_expander]["Tindakan Perbaikan"]
            if tindakan_perbaikan_filtered.empty:
                st.error("⚠ Tidak ada tindakan perbaikan untuk ID ini.")
            else:
                with st.expander("Detail Tindakan Perbaikan"):
                    st.write(tindakan_perbaikan_filtered.iloc[0])

    else:
        st.warning("Data tidak tersedia atau kosong dari API.")
else:
    st.error(f"Gagal mengambil data dari API. Status code: {response.status_code}")

def get_spk_data():
    try:
        response = requests.get(APPS_SCRIPT_URL, params={"action": "get_spk"}, timeout=20)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil data SPK: {e}")
        return []

def get_database_sp():
    try:
        response = requests.get(APPS_SCRIPT_URL, params={"action": "get_DatabaseSP"}, timeout=20)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil Database SP: {e}")
        return []

def get_all_data():
    try:
        response = requests.get(APPS_SCRIPT_URL, params={"action": "get_ALL"}, timeout=20)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil Database SP: {e}")
        return []
    
def add_data_to_all(form_data):
    try:
        response = requests.post(APPS_SCRIPT_URL, json=form_data, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}

def add_data_to_sparepart(form_data):
    try:
        response = requests.post(APPS_SCRIPT_URL, json=form_data, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}

# mengambil data SPK dan data Sparepart
spk_data = get_spk_data()
database_sp = get_database_sp()
all_data = get_all_data()

if spk_data:
    df_spk = pd.DataFrame(spk_data)
    df_all = pd.DataFrame(all_data) if all_data else pd.DataFrame(columns=["ID"])

    st.markdown("### 🖱️ Pilih ID SPK")
    id_options = df_spk["ID"].unique().tolist()
    selected_id = st.selectbox("Pilih ID SPK", id_options)

    existing_ids = df_all["ID"].astype(str).tolist()
    if str(selected_id) in existing_ids:
        st.error(f"⚠ ID_SPK '{selected_id}' sudah ada di Sheet ALL! Tidak bisa ditambahkan lagi.")
        st.stop()  # Hentikan eksekusi agar form tidak muncul

    # Ambil data dari SPK berdasarkan ID yang dipilih
    selected_row = df_spk[df_spk["ID"] == selected_id].iloc[0]
    
    # Format tanggal
    try:
        tanggal_pengerjaan = pd.to_datetime(selected_row["Tanggal Pengerjaan"], errors='coerce').date()
    except Exception:
        tanggal_pengerjaan = ""

    # Buat DataFrame dengan kolom di atas
    spk_info = pd.DataFrame([{
        "BU": selected_row["BU"],
        "Line": selected_row["Line"],
        "Produk": selected_row["Produk"],
        "Nomor Mesin": selected_row["Nomor Mesin"],
        "Mesin": selected_row["Mesin"],
        "Masalah": selected_row["Masalah"],
        "Tanggal": tanggal_pengerjaan,
        "PIC": selected_row["PIC"]
    }])

    # Tampilkan sebagai tabel
    st.markdown("#### Data dari SPK")
    st.dataframe(spk_info, use_container_width=True) 

    st.markdown("#### Tambahkan Data ke Sheet ALL")
    mulai = st.time_input("Jam Mulai", value=time(0, 0))
    selesai = st.time_input("Jam Selesai", value=time(0, 0))
    tindakan = st.text_area("Tindakan Perbaikan")

    bu_filter = selected_row['BU']
    if database_sp:
        df_database_sp = pd.DataFrame(database_sp)
        if {"BU", "Deskripsi", "UOM"}.issubset(df_database_sp.columns):
            filtered_db = df_database_sp[df_database_sp['BU'] == bu_filter]
            unique_descriptions = filtered_db[['Deskripsi', 'UOM']].drop_duplicates()['Deskripsi'].tolist()
        else:
            st.error("Kolom 'BU', 'Deskripsi', atau 'UOM' tidak ditemukan dalam database SP!")
            unique_descriptions = []
    else:
        st.warning("Database Sparepart kosong!")
        unique_descriptions = []

    # Pilih deskripsi sparepart
    selected_items = st.multiselect("Pilih Deskripsi Sparepart", unique_descriptions)

    if selected_items:
        # Ambil UOM untuk setiap item yang dipilih
        uom_values = [
            filtered_db.loc[filtered_db['Deskripsi'] == item, 'UOM'].values[0] 
            if not filtered_db.loc[filtered_db['Deskripsi'] == item, 'UOM'].empty 
            else "UNKNOWN"
            for item in selected_items
        ]

        # Buat DataFrame dengan Item, UOM, dan Quantity
        data = {'Item': selected_items, 'UOM': uom_values, 'Quantity': [0] * len(selected_items)}
        df = pd.DataFrame(data)

        # Gunakan st.data_editor dengan 'disabled' agar hanya Quantity yang bisa diedit
        edited_df = st.data_editor(df, key="data_editor", disabled=["Item", "UOM"])
    else:
        st.write("Silakan pilih deskripsi untuk melanjutkan.")

    submitted = st.button("Tambah Data")

    if submitted:
        if selesai <= mulai:
            st.error("Waktu selesai harus lebih besar dari waktu mulai.")
        else:
            mulai_str = mulai.strftime("%H:%M")
            selesai_str = selesai.strftime("%H:%M")

            quantities = edited_df['Quantity'].tolist() if selected_items else []

            if len(selected_items) == len(quantities):
                data_to_send = {
                    "action": "add_data",
                    "ID_SPK": str(selected_id),  # Ubah ke string
                    "BU": str(selected_row['BU']),
                    "Line": str(selected_row['Line']),
                    "Produk": str(selected_row['Produk']),
                    "Nomor": str(selected_row['Nomor Mesin']),
                    "Mesin": str(selected_row['Mesin']),
                    "Tanggal": str(tanggal_pengerjaan),
                    "Mulai": str(mulai.strftime("%H:%M")),
                    "Selesai": str(selesai.strftime("%H:%M")),
                    "Masalah": str(selected_row['Masalah']),
                    "Tindakan": str(tindakan),
                    "Deskripsi": ", ".join(map(str, selected_items)),  
                    "Quantity": ", ".join(map(str, quantities)),  
                    "PIC": str(selected_row['PIC'])
                }

                st.subheader("🔍 **Overview Data yang Akan Dikirim**")
                df_preview = pd.DataFrame([data_to_send])
                st.dataframe(df_preview, use_container_widht=True)
                
                if st.button("➕ Konfirmasi Tambah Data"):
                    st.session_state.show_confirmation = True  
                
                if st.session_state.get("show_confirmation", False):
                    st.warning("⚠️ Apakah Anda yakin ingin menambahkan data ini?")
                
                col1, col2 = st.columns(2)
                with col1:
                    confirm = st.button("✅ Ya, Tambah Data")
                with col2:
                    cancel = st.button("❌ Batal")

                if confirm:
                    response = add_data_to_all(data_to_send)
                    if response.get("status") == "success":
                        st.toast("✅ Data berhasil ditambahkan ke Sheet ALL!")
                        st.session_state.show_confirmation = False  
                        st.rerun()
                    else:
                        st.error(f"❌ Gagal menambahkan data: {response.get('error', 'Tidak diketahui')}")
                elif cancel:
                    st.session_state.show_confirmation = False  
                    st.info("✅ Data tidak jadi dikirim.")
                    st.rerun()

                # Tambahkan data sparepart ke Sheet SPAREPART
                for item, qty in zip(selected_items, quantities):
                    uom_value = filtered_db.loc[filtered_db['Deskripsi'] == item, 'UOM'].values
                    uom_final = uom_value[0] if len(uom_value) > 0 else "UNKNOWN"

                    sparepart_data = {
                        "action": "add_data_to_sparepart",
                        "ID_SPK": selected_id,
                        "Deskripsi": item,
                        "Quantity": qty,
                        "UOM": filtered_db.loc[filtered_db['Deskripsi'] == item, 'UOM'].values[0] if not filtered_db.empty else "UNKNOWN"
                    }

                    sparepart_response = add_data_to_sparepart(sparepart_data)
                    if sparepart_response.get("status") == "success":
                        st.success(f"Data sparepart '{item}' berhasil ditambahkan! ✅")
                    else:
                        st.error(f"Gagal menambahkan '{item}': {sparepart_response.get('error', 'Tidak diketahui')}")

            else:
                st.error("Jumlah deskripsi dan kuantitas tidak sesuai!")
else:
    st.warning("⚠ Tidak ada data SPK yang tersedia.")

