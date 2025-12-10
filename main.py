# main.py
import streamlit as st
import pandas as pd
from config import ACADEMIC_CODES, ACTIVITY_CODES, SKILL_LIST
from utils.data_processor import student_to_vector
from models.kmeans_model import run_kmeans

# === Session State ===
if 'page' not in st.session_state:
    st.session_state.page = 'input'
if 'student_profile' not in st.session_state:
    st.session_state.student_profile = None
if 'cluster_result' not in st.session_state:
    st.session_state.cluster_result = None

# === Navigation Helper ===
def goto(page):
    st.session_state.page = page

# === HALAMAN 1: INPUT PROFIL ===
if st.session_state.page == 'input':
    st.title("Input Profil Siswa")
    with st.form("profile_form"):
        name = st.text_input("Nama Lengkap", placeholder="Contoh: Iis Sukmawati")
        academic = st.selectbox("Minat Akademik", options=list(ACADEMIC_CODES.keys()))
        activity = st.selectbox("Ekstrakurikuler Utama", options=list(ACTIVITY_CODES.keys()))
        skills = st.multiselect("Keterampilan", options=SKILL_LIST)
        club_count = st.number_input("Jumlah Klub yang Diikuti", min_value=1, max_value=10, value=3)
        contribution = st.slider("Rata-rata Kontribusi (1–5)", 1, 5, 4)
        achievement = st.slider("Rata-rata Prestasi (1–5)", 1, 5, 4)

        if st.form_submit_button("Simpan & Proses"):
            if name.strip():
                st.session_state.student_profile = {
                    'name': name,
                    'academic_code': ACADEMIC_CODES[academic],
                    'activity_code': ACTIVITY_CODES[activity],
                    'skills': skills,
                    'club_count': club_count,
                    'contribution': contribution,
                    'achievement': achievement
                }
                goto('process')
                st.rerun()
            else:
                st.error("Nama tidak boleh kosong!")

# === HALAMAN 2: PROSES CLUSTERING ===
elif st.session_state.page == 'process':
    st.title("⚙️ Proses Pengelompokan (K-Means)")
    prof = st.session_state.student_profile
    if prof:
        st.write(f"Memproses data untuk: **{prof['name']}**")
        vector = student_to_vector(prof)
        df_input = pd.DataFrame([vector], columns=['Kontribusi', 'Prestasi', 'JumlahKlub'])

        # Jalankan K-Means
        result_df, centroids, sse = run_kmeans(df_input, k=3)

        st.session_state.cluster_result = {
            'name': prof['name'],
            'cluster_id': int(result_df['ClusterID'].iloc[0]),
            'sse': sse,
            'vector': vector
        }

        st.success(f"Berhasil! Masuk ke **Cluster #{result_df['ClusterID'].iloc[0]}**")
        if st.button("Lihat Rekomendasi"):
            goto('result')
            st.rerun()
    else:
        st.warning("Tidak ada data siswa.")
        if st.button("Kembali ke Input"):
            goto('input')

# === HALAMAN 3: HASIL REKOMENDASI ===
elif st.session_state.page == 'result':
    st.title("Rekomendasi Jurusan/Karier")
    res = st.session_state.cluster_result
    if res:
        # Mapping cluster ke label & jurusan
        cluster_labels = {0: "Analytical-Oriented", 1: "Creative-Oriented", 2: "Leadership-Oriented"}
        majors = {
            0: ["Ilmu Komputer", "Matematika", "Statistika"],
            1: ["Desain Komunikasi Visual", "Sastra", "Film & Media"],
            2: ["Manajemen", "Ilmu Komunikasi", "Hubungan Internasional"]
        }

        cid = res['cluster_id']
        st.subheader(f"Selamat, **{res['name']}**!")
        st.markdown(f"Kamu termasuk dalam **{cluster_labels[cid]}**")
        st.write("**Jurusan yang direkomendasikan:**")
        for m in majors[cid]:
            st.markdown(f"🔹 {m}")

        st.metric("Total Error (SSE)", f"{res['sse']:.3f}")
        if st.button("Coba Lagi"):
            goto('input')
            st.rerun()
    else:
        st.error("Belum ada hasil. Harap proses data terlebih dahulu.")