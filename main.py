# main.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from config import ACADEMIC_CODES, ACTIVITY_CODES, SKILL_LIST
from utils.data_processor import student_to_vector
from models.kmeans_model import run_kmeans
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

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
        
        # --- Muat dataset sampel ---
        try:
            sample_df = pd.read_csv('data/sample_data.csv')
            st.info(f"Dataset sampel dimuat. Jumlah data: {len(sample_df)}")
        except FileNotFoundError:
            st.error("File 'data/sample_data.csv' tidak ditemukan. Pastikan file tersebut ada di folder 'data/'.")
            st.stop()
        
        # --- Konversi semua data sampel menjadi vektor ---
        sample_vectors = []
        for _, row in sample_df.iterrows():
            profile = {
                'minat': row['minat'],
                'ekskul': row['ekskul'],
                'skill': row['skill'],
                'club_count': row['club_count'],
                'contribution': row['contribution'],
                'achievement': row['achievement']
            }
            vec = student_to_vector(profile)
            sample_vectors.append(vec)
        
        # Buat DataFrame dari vektor-vektor sampel
        feature_names = [
            'Minat_Code', 'Ekskul_Code',
            'Skill_Public_Speaking', 'Skill_Analisis_Data', 'Skill_Menulis',
            'Skill_Leadership', 'Skill_Desain', 'Skill_Negosiasi',
            'Contribution', 'Achievement', 'Club_Count'
        ]
        
        df_sample = pd.DataFrame(sample_vectors, columns=feature_names)
        
        # --- Tampilkan Matriks Keputusan (Data Terstandarisasi) ---
        st.subheader("Matriks Keputusan (Data Terstandarisasi)")
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(df_sample)
        df_scaled = pd.DataFrame(scaled_features, columns=feature_names)
        
        # Tambahkan kolom ID berdasarkan index default (Aman!)
        df_scaled['ID'] = [f"S{i+1:03d}" for i in range(len(df_scaled))]
        
        # Pindahkan kolom ID ke paling kiri
        df_scaled = df_scaled[['ID'] + [col for col in df_scaled.columns if col != 'ID']]
        
        st.dataframe(df_scaled, use_container_width=True)
        
        # --- Parameter dan Tombol Hitung ---
        st.subheader("Parameter")
        k = st.slider("Jumlah Cluster (k)", min_value=2, max_value=5, value=3, step=1)
        
        if st.button("🚀 Hitung Cluster", type="primary"):
            with st.spinner("Menghitung..."):
                # Jalankan K-Means pada dataset sampel
                result_df, centroids, sse = run_kmeans(df_sample, k=k)
                
                # Prediksi cluster untuk siswa baru
                scaled_new_student = scaler.transform([student_to_vector(prof)])
                kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
                kmeans.fit(scaled_features)
                predicted_cluster = kmeans.predict(scaled_new_student)[0]
                
                # Simpan hasil
                st.session_state.cluster_result = {
                    'name': prof['name'],
                    'cluster_id': int(predicted_cluster),
                    'sse': sse,
                    'vector': student_to_vector(prof),
                    'features': feature_names,
                    'k': k,
                    'centroids': centroids,
                    'df_sample': df_sample,
                    'scaled_features': scaled_features,
                    'scaler': scaler
                }
                
                st.success(f"Berhasil! Masuk ke **Cluster #{predicted_cluster}**")
                st.rerun()
        
        # --- Ringkasan Data ---
        st.subheader("Ringkasan Data")
        col1, col2, col3 = st.columns(3)
        col1.metric("Jumlah Siswa", len(sample_df))
        col2.metric("Jumlah Fitur", len(feature_names))
        col3.metric("Jumlah Cluster", k)
        
        # --- Status Proses ---
        st.subheader("Status Proses")
        st.progress(100, text=f"Selesai. {k} Cluster terbentuk.")
        
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
        
        # --- Header Cluster ---
        st.markdown(f"## Selamat, **{res['name']}**!")
        st.markdown(f"Kamu termasuk dalam **{cluster_labels[cid]}**")
        st.markdown("---")
        
        # --- Kolom Utama ---
        col1, col2, col3 = st.columns(3)
        
        # Kolom 1: Ranking Rekomendasi
        with col1:
            st.subheader("Ranking Rekomendasi")
            # Buat skor rekomendasi berdasarkan jarak ke centroid
            scaler = res['scaler']
            kmeans = KMeans(n_clusters=res['k'], random_state=42, n_init='auto')
            kmeans.fit(res['scaled_features'])
            
            # Skor rekomendasi adalah 1/(jarak ke centroid)
            distances = kmeans.transform(scaler.transform([res['vector']]))
            scores = 1 / (distances[0] + 1e-6)  # Tambahkan epsilon untuk menghindari pembagian nol
            sorted_indices = np.argsort(scores)[::-1]  # Urutkan dari tertinggi
            
            for i, idx in enumerate(sorted_indices[:4], 1):  # Ambil 4 jurusan teratas
                major_name = majors[cid][idx % len(majors[cid])]  # Ambil nama jurusan
                score = scores[idx]
                st.markdown(f"**{i}. {major_name}** <span style='float:right;'>{score:.2f}</span>", unsafe_allow_html=True)
        
        # Kolom 2: Skor Rekomendasi (Bar Chart)
        with col2:
            st.subheader("Skor Rekomendasi")
            fig, ax = plt.subplots(figsize=(6, 4))
            bar_colors = ['blue', 'green', 'red', 'purple']
            ax.bar(range(len(scores)), scores, color=bar_colors[:len(scores)])
            ax.set_xticks(range(len(scores)))
            ax.set_xticklabels([majors[cid][i % len(majors[cid])] for i in range(len(scores))], rotation=45, ha='right')
            ax.set_ylim(0, 1.2)
            ax.set_title("Skor Rekomendasi per Jurusan")
            st.pyplot(fig)
        
        # Kolom 3: Profil Kompetensi (Radar Chart)
        with col3:
            st.subheader("Profil Kompetensi")
            # Ambil fitur siswa baru
            features = res['vector']
            # Ambil rata-rata fitur dari cluster ideal
            cluster_mean = np.mean(res['df_sample'][res['df_sample']['ClusterID'] == cid], axis=0)
            
            # Plot radar chart
            categories = ['Minat', 'Ekskul', 'Skill1', 'Skill2', 'Skill3', 'Skill4', 'Skill5', 'Skill6', 'Kontribusi', 'Prestasi', 'Jml Klub']
            N = len(categories)
            
            angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
            angles += angles[:1]
            
            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            
            # Plot profil siswa
            values = features.tolist()
            values += values[:1]
            ax.plot(angles, values, 'o-', linewidth=2, label='Anda')
            ax.fill(angles, values, alpha=0.25)
            
            # Plot profil ideal cluster
            values_ideal = cluster_mean.tolist()
            values_ideal += values_ideal[:1]
            ax.plot(angles, values_ideal, 'o--', linewidth=2, label='Ideal Cluster')
            ax.fill(angles, values_ideal, alpha=0.1)
            
            ax.set_thetagrids(np.degrees(angles[:-1]), categories)
            ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
            ax.set_title("Perbandingan Profil Kompetensi")
            st.pyplot(fig)
        
        # --- Total Error (SSE) ---
        st.markdown("---")
        st.metric("Total Error (SSE)", f"{res['sse']:.3f}")
        
        # --- Tombol Aksi ---
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔄 Coba Lagi"):
                goto('input')
                st.rerun()
        with col_btn2:
            if st.button("📥 Unduh Laporan"):
                st.info("Fitur unduh laporan belum tersedia. Silakan salin hasil manual.")
        
    else:
        st.error("Belum ada hasil. Harap proses data terlebih dahulu.")