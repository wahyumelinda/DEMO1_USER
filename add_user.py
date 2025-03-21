import streamlit as st
import pandas as pd
import requests

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby3UD6yKJdcAb3t5J9bfA8pshHoWizwwqfKXN7PoHbTfVo5VhCtHcp6bUIcSRTsN6GR/exec"

# Fungsi untuk mengambil data dari Google Sheets
def get_all_data():
    try:
        response = requests.get(APPS_SCRIPT_URL, params={"action": "get_ALL"}, timeout=20)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil data: {e}")
        return []

# Fungsi untuk mengambil database sparepart
def get_sparepart_database():
    try:
        response = requests.get(APPS_SCRIPT_URL, params={"action": "get_SP_database"}, timeout=20)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil database sparepart: {e}")
        return []

# Fungsi untuk mengupdate data ke Google Sheets
def update_user_data(form_data):
    try:
        response = requests.post(APPS_SCRIPT_URL, json=form_data, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}

st.title("🔧 Update Data Pengguna")

data_all = get_all_data()
df_all = pd.DataFrame(data_all)

database_sp = get_sparepart_database()

df_all.columns = [
    "ID", "BU", "Line", "Produk", "Nomor Mesin", "Mesin", "Tanggal Pengerjaan",
    "Pengerjaan Mulai", "Pengerjaan Selesai", "Masalah", "Tindakan Perbaikan",
    "Pemakaian Sparepart", "PIC", "Kondisi", "Alasan", "SPV", "Last Update SPV",
    "Approve", "Reason", "SM", "Last Update SM"
]

if not df_all.empty:
    editable_df = df_all[(df_all["Approve"] == "Revise") | (df_all["Kondisi"].isin(["On Progress", ""]))]
    if not editable_df.empty:
        st.markdown("### ✏️ Pilih Data untuk Diperbarui")
        id_options = editable_df["ID"].unique().tolist()
        selected_id = st.selectbox("Pilih ID SPK", id_options)
        selected_row = editable_df[editable_df["ID"] == selected_id].iloc[0]

        st.markdown("#### 📝 Form Update Data")
        mulai = st.time_input("Jam Mulai", value=pd.to_datetime(selected_row.get("Pengerjaan Mulai", "00:00"), format="%H:%M").time())
        selesai = st.time_input("Jam Selesai", value=pd.to_datetime(selected_row.get("Pengerjaan Selesai", "00:00"), format="%H:%M").time())
        tindakan = st.text_area("Tindakan Perbaikan", value=selected_row.get("Tindakan Perbaikan", ""))

        st.markdown("#### 🔧 Update Deskripsi Sparepart")
        bu_filter = selected_row["BU"]

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

        selected_items = st.multiselect("Pilih Deskripsi Sparepart", unique_descriptions)

        if selected_items:
            uom_values = [
                filtered_db.loc[filtered_db['Deskripsi'] == item, 'UOM'].values[0] 
                if not filtered_db.loc[filtered_db['Deskripsi'] == item, 'UOM'].empty 
                else "UNKNOWN"
                for item in selected_items
            ]

            data = {'Item': selected_items, 'UOM': uom_values, 'Quantity': [0] * len(selected_items)}
            df_sparepart = pd.DataFrame(data)
            edited_sparepart_df = st.data_editor(df_sparepart, key="sparepart_editor", disabled=["Item", "UOM"])
        else:
            edited_sparepart_df = pd.DataFrame(columns=["Item", "UOM", "Quantity"])

        if st.button("🔄 Update Data"):
            if selesai <= mulai:
                st.error("Waktu selesai harus lebih besar dari waktu mulai.")
            else:
                update_data = {
                    "action": "update_user_data",
                    "ID_SPK": selected_id,
                    "Mulai": mulai.strftime("%H:%M"),
                    "Selesai": selesai.strftime("%H:%M"),
                    "Tindakan": tindakan,
                    "Deskripsi": ", ".join(edited_sparepart_df["Item"].tolist()),
                    "UOM": ", ".join(edited_sparepart_df["UOM"].tolist()),
                    "Quantity": ", ".join(map(str, edited_sparepart_df["Quantity"].tolist()))
                }

                response = update_user_data(update_data)
                if response.get("status") == "success":
                    st.success("✅ Data berhasil diperbarui!")
                    st.rerun()
                else:
                    st.error(f"❌ Gagal memperbarui data: {response.get('error', 'Tidak diketahui')}")
    else:
        st.info("Tidak ada data yang bisa diperbarui.")
else:
    st.warning("Tidak ada data tersedia.")
