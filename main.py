import streamlit as st
import pandas as pd

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

        # Nama dan Minat Akademik
        name = st.text_input("Nama Lengkap", value=st.session_state.get("temp_name", ""))
        academic = st.selectbox("Minat Akademik", list(ACADEMIC_CODES.keys()))

        # Daftar Keterampilan
        st.subheader("Daftar Keterampilan")
        cols = st.columns(2)
        for i, skill in enumerate(SKILL_LIST):
            cols[i % 2].checkbox(skill, key=f"skill_{i}")

        # Ekstrakurikuler yang Diikuti
        st.subheader("Ekstrakurikuler yang Diikuti")
        for i, ex in enumerate(st.session_state.extracurricular_inputs):
            c1, c2, c3 = st.columns([3, 2, 2])
            ex["activity"] = c1.selectbox(
                "Ekskul",
                [""] + list(ACTIVITY_CODES.keys()),
                key=f"act_{i}",
                index=0 if not ex["activity"] else list(ACTIVITY_CODES.keys()).index(ex["activity"]) + 1
            )
            ex["contribution"] = c2.slider(
                "Kontribusi", 1, 5, ex["contribution"],
                key=f"cont_{i}"
            )
            ex["achievement"] = c3.slider(
                "Prestasi", 1, 5, ex["achievement"],
                key=f"ach_{i}"
            )

        # Tombol Kelola Ekstrakurikuler (DI LUAR FORM → AMAN!)
        st.markdown("### Kelola Ekstrakurikuler")
        col1, col2 = st.columns(2)
        if col1.button("➕ Tambah Ekstrakurikuler Yang Diikuti"):
            st.session_state.extracurricular_inputs.append(
                {"activity": "", "contribution": 3, "achievement": 3}
            )
            st.rerun()
        if col2.button("❌ Hapus Ekskul Terakhir Yang Diikuti") and len(st.session_state.extracurricular_inputs) > 1:
            st.session_state.extracurricular_inputs.pop()
            st.rerun()

        # Ekstrakurikuler Utama
        st.subheader("Ekstrakurikuler Utama")
        main_act = st.selectbox("Pilih Ekskul Utama", list(ACTIVITY_CODES.keys()))

        # Tombol Submit (BUKAN di dalam st.form!)
        if st.button("Simpan & Proses"):
            # Validasi
            valid = [e for e in st.session_state.extracurricular_inputs if e["activity"]]

            if not name.strip():
                st.error("Nama wajib diisi!")
            elif not valid:
                st.error("Minimal satu ekstrakurikuler!")
            else:
                # Ambil keterampilan yang diceklis
                skills = [
                    SKILL_LIST[i]
                    for i in range(len(SKILL_LIST))
                    if st.session_state[f"skill_{i}"]
                ]

                # Simpan profil
                profile = {
                    "email": st.session_state.current_email,
                    "name": name,
                    "minat": academic,
                    "ekskul": main_act,
                    "skill": ", ".join(skills),
                    "club_count": len(valid),
                    "contribution": sum(e["contribution"] for e in valid) / len(valid),
                    "achievement": sum(e["achievement"] for e in valid) / len(valid)
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

        train_df = pd.read_csv("data/sample_data.csv")

        vectors = []
        for _, row in train_df.iterrows():
            vectors.append(student_to_vector(row))

        vectors.append(student_to_vector(profile))
        df_vectors = pd.DataFrame(vectors)

        result_df, _, sse = run_kmeans(df_vectors, k=3)
        cluster_id = int(result_df["ClusterID"].iloc[-1])

        st.session_state.cluster_result = {
            "name": profile["name"],
            "cluster_id": cluster_id,
            "sse": sse
        }

        st.success(f"✅ Kamu masuk ke Cluster #{cluster_id}")

        if st.button("Lihat Rekomendasi"):
            goto("result")
            st.rerun()

    # ==================================================
    # HASIL REKOMENDASI
    # ==================================================
    elif st.session_state.page == "result":
        res = st.session_state.cluster_result
        st.title("🎓 Rekomendasi Jurusan")

        cluster_labels = {
            0: "Analytical",
            1: "Creative",
            2: "Leadership"
        }

        recommendations = {
            0: ["Ilmu Komputer", "Matematika", "Statistika"],
            1: ["DKV", "Sastra", "Film"],
            2: ["Manajemen", "Komunikasi", "Hubungan Internasional"]
        }

        st.subheader(f"Halo, {res['name']} 👋")
        st.write(f"Kamu termasuk tipe **{cluster_labels[res['cluster_id']]}**")

        st.markdown("### Rekomendasi Jurusan:")
        for jurusan in recommendations[res["cluster_id"]]:
            st.markdown(f"• {jurusan}")

        st.metric("Nilai SSE", f"{res['sse']:.3f}")

        if st.button("Isi Ulang Profil"):
            goto("input")
            st.rerun()