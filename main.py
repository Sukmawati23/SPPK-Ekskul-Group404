import streamlit as st
import pandas as pd
import os

from config import ACADEMIC_CODES, ACTIVITY_CODES, SKILL_LIST
from utils.data_processor import student_to_vector
from models.kmeans_model import run_kmeans
from utils.auth import register_user, authenticate_user
from utils.storage import save_student_to_csv

# ==========================================================
# SESSION STATE INIT
# ==========================================================
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

# ==========================================================
# LOGIN / REGISTER
# ==========================================================
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
            if not email or not password:
                st.error("Email dan password wajib diisi!")
            elif password != confirm:
                st.error("Password tidak cocok!")
            elif register_user(email, password):
                st.success("Akun berhasil dibuat! Silakan login.")
                goto("login")
                st.rerun()
            else:
                st.error("Email sudah terdaftar!")

        if st.button("Kembali ke Login"):
            goto("login")
            st.rerun()

# ==========================================================
# SETELAH LOGIN
# ==========================================================
else:
    st.sidebar.title(f"👤 {st.session_state.current_email}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    # ======================================================
    # INPUT PROFIL
    # ======================================================
    if st.session_state.page == "input":
        st.title("Input Profil Siswa")

        with st.form("profil_form"):
            name = st.text_input("Nama Lengkap")
            academic = st.selectbox("Minat Akademik", list(ACADEMIC_CODES.keys()))

            # ===== KETERAMPILAN =====
            st.subheader("Daftar Keterampilan")
            cols = st.columns(2)
            for i, skill in enumerate(SKILL_LIST):
                cols[i % 2].checkbox(skill, key=f"skill_{i}")

            # ===== EKSTRAKURIKULER =====
            st.subheader("Ekstrakurikuler yang Diikuti")
            for i, ex in enumerate(st.session_state.extracurricular_inputs):
                cols = st.columns([3, 2, 2])
                ex["activity"] = cols[0].selectbox(
                    "", [""] + list(ACTIVITY_CODES.keys()),
                    key=f"act_{i}", label_visibility="collapsed"
                )
                ex["contribution"] = cols[1].slider(
                    "", 1, 5, ex["contribution"],
                    key=f"cont_{i}", label_visibility="collapsed"
                )
                ex["achievement"] = cols[2].slider(
                    "", 1, 5, ex["achievement"],
                    key=f"ach_{i}", label_visibility="collapsed"
                )

            st.subheader("Ekstrakurikuler Utama")
            main_act = st.selectbox(
                "Pilih Ekstrakurikuler Utama",
                list(ACTIVITY_CODES.keys())
            )

            submitted = st.form_submit_button("Simpan & Proses")

        # ➕ Tambah ekskul (DI LUAR FORM)
        if st.button("➕ Tambah Ekstrakurikuler"):
            st.session_state.extracurricular_inputs.append(
                {"activity": "", "contribution": 3, "achievement": 3}
            )
            st.rerun()

        if submitted:
            valid = [e for e in st.session_state.extracurricular_inputs if e["activity"]]

            if not name.strip():
                st.error("Nama wajib diisi!")
            elif not valid:
                st.error("Harap tambahkan minimal satu ekstrakurikuler yang valid!")
            else:
                selected_skills = [
                    SKILL_LIST[i]
                    for i in range(len(SKILL_LIST))
                    if st.session_state[f"skill_{i}"]
                ]

                st.session_state.student_profile = {
                    "email": st.session_state.current_email,
                    "name": name,
                    "minat": academic,
                    "ekskul": main_act,
                    "skill": ", ".join(selected_skills),
                    "club_count": len(valid),
                    "contribution": sum(e["contribution"] for e in valid) / len(valid),
                    "achievement": sum(e["achievement"] for e in valid) / len(valid)
                }

                save_student_to_csv(st.session_state.student_profile)

                goto("process")
                st.rerun()

    # ======================================================
    # PROSES CLUSTERING
    # ======================================================
    elif st.session_state.page == "process":
        st.title("⚙️ Proses Pengelompokan (K-Means)")

        prof = st.session_state.student_profile
        if not prof:
            st.warning("Tidak ada data siswa.")
            goto("input")
            st.rerun()

        train_df = pd.read_csv("data/sample_data.csv")

        vectors = []
        for _, row in train_df.iterrows():
            vectors.append(student_to_vector(row))

        vectors.append(student_to_vector(prof))
        df = pd.DataFrame(vectors)

        result_df, _, sse = run_kmeans(df, k=3)
        cid = int(result_df["ClusterID"].iloc[-1])

        st.session_state.cluster_result = {
            "name": prof["name"],
            "cluster_id": cid,
            "sse": sse
        }

        st.success(f"✅ Berhasil! Masuk ke **Cluster #{cid}**")
        if st.button("Lihat Rekomendasi"):
            goto("result")
            st.rerun()

    # ======================================================
    # HASIL
    # ======================================================
    elif st.session_state.page == "result":
        res = st.session_state.cluster_result
        st.title("🎓 Rekomendasi Jurusan/Karier")

        cluster_labels = {
            0: "Analytical",
            1: "Creative",
            2: "Leadership"
        }
        majors = {
            0: ["Ilmu Komputer", "Matematika", "Statistika"],
            1: ["DKV", "Sastra", "Film"],
            2: ["Manajemen", "Komunikasi", "Hubungan Internasional"]
        }

        st.subheader(f"Selamat, **{res['name']}**!")
        st.write(f"Kamu termasuk dalam kelompok **{cluster_labels[res['cluster_id']]}**")

        for m in majors[res["cluster_id"]]:
            st.markdown(f"🔹 {m}")

        st.metric("SSE", f"{res['sse']:.3f}")

        if st.button("Coba Lagi"):
            goto("input")
            st.rerun()
