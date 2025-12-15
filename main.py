import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from config import ACADEMIC_CODES, ACTIVITY_CODES, SKILL_LIST
from utils.data_processor import student_to_vector
from models.kmeans_model import run_kmeans
from utils.auth import register_user, authenticate_user
from utils.storage import save_student_to_csv

# ======================================================
# INIT SESSION STATE
# ======================================================
def init_state():
    defaults = {
        "logged_in": False,
        "current_email": None,
        "page": "login",
        "student_profile": None,
        "cluster_result": None,
        "extracurricular_inputs": [
            {"activity": "", "contribution": 3, "achievement": 3}
        ]
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    for i in range(len(SKILL_LIST)):
        if f"skill_{i}" not in st.session_state:
            st.session_state[f"skill_{i}"] = False

init_state()

def goto(page):
    st.session_state.page = page

# ======================================================
# FUNGSI HITUNG SKOR REKOMENDASI
# ======================================================
def calculate_recommendation_scores(profile, cluster_id):
    cluster_to_majors = {
        0: ["Ilmu Komputer", "Matematika", "Statistika"],
        1: ["DKV", "Sastra", "Film"],
        2: ["Manajemen", "Komunikasi", "Hubungan Internasional"]
    }
    majors = cluster_to_majors.get(cluster_id, [])
    if not majors:
        return majors, [0.0] * len(majors)

    minat = profile["minat"]
    ekskul = profile["ekskul"]
    skills = set(s.strip() for s in profile["skill"].split(",") if s.strip())

    scores = []
    for major in majors:
        score = 0.0
        if cluster_id == 0:  # Analytical
            if minat == "IPA":
                score += 0.4
            if ekskul in ["Robotik", "Debat", "Jurnalistik"]:
                score += 0.2
            relevant = {"Publik Speaking", "Analisis Data", "Problem Solving", "Ketekunan"}
            score += 0.4 * len(skills & relevant) / max(len(relevant), 1)
        elif cluster_id == 1:  # Creative
            if minat in ["Bahasa", "IPS"]:
                score += 0.4
            if ekskul in ["Seni Musik", "Seni Rupa", "Teater", "Film"]:
                score += 0.2
            relevant = {"Desain", "Kreativitas", "Menulis", "Publik Speaking"}
            score += 0.4 * len(skills & relevant) / max(len(relevant), 1)
        elif cluster_id == 2:  # Leadership
            if minat in ["IPS", "Bahasa"]:
                score += 0.4
            if ekskul in ["OSIS", "Pramuka", "Paskibra", "PMR"]:
                score += 0.2
            relevant = {"Leadership", "Negosiasi", "Kolaborasi", "Publik Speaking"}
            score += 0.4 * len(skills & relevant) / max(len(relevant), 1)
        scores.append(min(score, 1.0))

    sorted_pairs = sorted(zip(majors, scores), key=lambda x: x[1], reverse=True)
    if sorted_pairs:
        sorted_majors, sorted_scores = zip(*sorted_pairs)
        return list(sorted_majors), list(sorted_scores)
    return majors, scores

# ======================================================
# LOGIN & REGISTER
# ======================================================
if not st.session_state.logged_in:
    if st.session_state.page == "login":
        st.title("🔐 Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
        if submit:
            if authenticate_user(email, password):
                st.session_state.logged_in = True
                st.session_state.current_email = email
                goto("input")
                st.rerun()
            else:
                st.error("Email atau password salah!")
        if st.button("Daftar akun baru"):
            goto("register")
            st.rerun()

    elif st.session_state.page == "register":
        st.title("📝 Daftar Akun Baru")
        with st.form("register_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Konfirmasi Password", type="password")
            submit = st.form_submit_button("Daftar")
        if submit:
            if password != confirm:
                st.error("Password tidak cocok!")
            elif register_user(email, password):
                st.success("Akun berhasil dibuat, silakan login.")
                goto("login")
                st.rerun()
            else:
                st.error("Email sudah terdaftar!")

# ======================================================
# SETELAH LOGIN
# ======================================================
else:
    st.sidebar.title(f"👤 {st.session_state.current_email}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    # ==================================================
    # INPUT PROFIL SISWA
    # ==================================================
    if st.session_state.page == "input":
        st.title("📋 Input Profil Siswa")

        name = st.text_input("Nama Lengkap")
        academic = st.selectbox("Minat Akademik", list(ACADEMIC_CODES.keys()))

        with st.expander("🛠️ Pilih Keterampilan"):
            cols = st.columns(2)
            for i, skill in enumerate(SKILL_LIST):
                cols[i % 2].checkbox(skill, key=f"skill_{i}")

        st.subheader("🎯 Ekstrakurikuler yang Diikuti")
        valid_activities = []
        for i, ex in enumerate(st.session_state.extracurricular_inputs):
            c1, c2, c3 = st.columns([3, 2, 2])
            ex["activity"] = c1.selectbox(
                "Ekskul",
                [""] + list(ACTIVITY_CODES.keys()),
                key=f"act_{i}",
                index=0 if not ex["activity"] else list(ACTIVITY_CODES.keys()).index(ex["activity"]) + 1
            )
            ex["contribution"] = c2.slider("Kontribusi", 1, 5, ex["contribution"], key=f"cont_{i}")
            ex["achievement"] = c3.slider("Prestasi", 1, 5, ex["achievement"], key=f"ach_{i}")

            if ex["activity"]:
                valid_activities.append(ex["activity"])

        st.markdown("### ➕ Kelola Ekstrakurikuler")
        col1, col2 = st.columns(2)
        if col1.button("Tambah", use_container_width=True):
            st.session_state.extracurricular_inputs.append({"activity": "", "contribution": 3, "achievement": 3})
            st.rerun()
        if col2.button("Hapus Terakhir", use_container_width=True) and len(st.session_state.extracurricular_inputs) > 1:
            st.session_state.extracurricular_inputs.pop()
            st.rerun()

        # 🔒 EKSKUL UTAMA: HANYA DARI YANG DIIKUTI
        st.subheader("🏆 Ekstrakurikuler Utama")
        if valid_activities:
            main_act = st.selectbox("Pilih Ekskul Utama", options=valid_activities, index=0)
        else:
            st.info("Silakan isi minimal satu ekstrakurikuler untuk memilih ekskul utama.")
            main_act = None

        st.divider()
        if st.button("💾 Simpan & Proses", type="primary", use_container_width=True):
            valid_inputs = [e for e in st.session_state.extracurricular_inputs if e["activity"]]
            if not name.strip():
                st.error("Nama wajib diisi!")
            elif not valid_inputs:
                st.error("Minimal satu ekstrakurikuler harus diisi!")
            elif not main_act:
                st.error("Ekskul utama wajib dipilih dari daftar yang diikuti!")
            else:
                skills = [SKILL_LIST[i] for i in range(len(SKILL_LIST)) if st.session_state[f"skill_{i}"]]
                profile = {
                    "email": st.session_state.current_email,
                    "name": name,
                    "minat": academic,
                    "ekskul": main_act,
                    "skill": ", ".join(skills),
                    "club_count": len(valid_inputs),
                    "contribution": sum(e["contribution"] for e in valid_inputs) / len(valid_inputs),
                    "achievement": sum(e["achievement"] for e in valid_inputs) / len(valid_inputs)
                }
                save_student_to_csv(profile)
                st.session_state.student_profile = profile
                goto("process")
                st.rerun()

    # ==================================================
    # PROSES CLUSTERING
    # ==================================================
    elif st.session_state.page == "process":
        st.title("⚙️ Proses Clustering (K-Means)")
        profile = st.session_state.student_profile
        if not profile:
            goto("input")
            st.rerun()

        with st.spinner("Memproses data..."):
            train_df = pd.read_csv("data/sample_data.csv")
            vectors = [student_to_vector(row) for _, row in train_df.iterrows()]
            vectors.append(student_to_vector(profile))
            df_vectors = pd.DataFrame(vectors)
            result_df, centers, sse = run_kmeans(df_vectors, k=3)
            cluster_id = int(result_df["ClusterID"].iloc[-1])
            centroid = centers[cluster_id] if centers.size > 0 else np.zeros(len(vectors[0]))

            st.session_state.cluster_result = {
                "name": profile["name"],
                "cluster_id": cluster_id,
                "sse": sse,
                "profile_vector": np.array(student_to_vector(profile)),
                "centroid": np.array(centroid)
            }

        st.success(f"✅ Kamu masuk ke Cluster **#{cluster_id}**")
        if st.button("➡️ Lihat Rekomendasi", type="primary"):
            goto("result")
            st.rerun()

    # ==================================================
    # HASIL REKOMENDASI — DENGAN SEMUA VISUALISASI
    # ==================================================
    elif st.session_state.page == "result":
        res = st.session_state.cluster_result
        profile = st.session_state.student_profile
        st.title("🎓 Rekomendasi Jurusan")

        cluster_labels = {0: "Analytical", 1: "Creative", 2: "Leadership"}
        st.subheader(f"Halo, **{res['name']}** 👋")
        st.info(f"Kamu termasuk tipe **{cluster_labels[res['cluster_id']]}**.")

        # Hitung skor
        majors, scores = calculate_recommendation_scores(profile, res["cluster_id"])

        # 🔢 Ranking
        with st.container(border=True):
            st.markdown("### 🔢 Ranking Rekomendasi")
            for i, (m, s) in enumerate(zip(majors, scores), 1):
                st.markdown(f"**{i}. {m}** — Skor: **{s:.2f}**")

        # 📊 Bar Chart
        if scores:
            st.markdown("### 📊 Skor Rekomendasi")
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            colors = plt.cm.viridis(np.linspace(0, 1, len(scores)))
            ax1.bar(majors, scores, color=colors)
            ax1.set_ylim(0, 1.1)
            ax1.set_ylabel("Skor Kesesuaian")
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig1)

        # 📈 Radar Chart — Profil Kompetensi
        st.markdown("### 📈 Profil Kompetensi Anda")
        feature_names = ["Minat", "Ekskul"] + SKILL_LIST + ["Kontribusi", "Prestasi", "Jml Klub"]
        student_vals = res["profile_vector"]
        centroid_vals = res["centroid"]

        N = len(feature_names)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]

        fig2, ax2 = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        # Profil Anda
        vals_std = student_vals.tolist()
        vals_std += vals_std[:1]
        ax2.plot(angles, vals_std, 'o-', linewidth=2, label='Anda')
        ax2.fill(angles, vals_std, alpha=0.25)
        # Rata-rata Cluster
        vals_ideal = centroid_vals.tolist()
        vals_ideal += vals_ideal[:1]
        ax2.plot(angles, vals_ideal, 'o--', linewidth=2, label='Rata-rata Cluster')
        ax2.fill(angles, vals_ideal, alpha=0.1)

        ax2.set_thetagrids(np.degrees(angles[:-1]), feature_names)
        ax2.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        ax2.set_title("Perbandingan Profil Kompetensi", pad=20)
        st.pyplot(fig2)

        # ℹ️ Detail Teknis
        with st.expander("ℹ️ Detail Clustering"):
            st.metric("Cluster ID", res["cluster_id"])
            st.metric("Nilai SSE", f"{res['sse']:.3f}")

        st.divider()
        if st.button("🔄 Isi Ulang Profil", use_container_width=True):
            goto("input")
            st.rerun()