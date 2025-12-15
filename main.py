# main.py (FINAL - TANPA FORM, PAKAI TABEL DINAMIS)
import streamlit as st
import pandas as pd
from config import ACADEMIC_CODES, ACTIVITY_CODES, SKILL_LIST
from utils.data_processor import student_to_vector
from models.kmeans_model import run_kmeans
from utils.auth import register_user, authenticate_user

# === Session State ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_email' not in st.session_state:
    st.session_state.current_email = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'student_profile' not in st.session_state:
    st.session_state.student_profile = None
if 'cluster_result' not in st.session_state:
    st.session_state.cluster_result = None
if 'extracurricular_inputs' not in st.session_state:
    st.session_state.extracurricular_inputs = [{'activity': '', 'contribution': 3, 'achievement': 3}]

def goto(page):
    st.session_state.page = page

# === LOGIN / REGISTER ===
if not st.session_state.logged_in:
    if st.session_state.page == 'login':
        st.title("🔐 Login")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="user@example.com")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if authenticate_user(email, password):
                    st.session_state.logged_in = True
                    st.session_state.current_email = email
                    goto('input')
                    st.rerun()
                else:
                    st.error("Email atau password salah!")
        if st.button("Daftar akun baru"):
            goto('register')
    elif st.session_state.page == 'register':
        st.title("📝 Daftar Akun Baru")
        with st.form("register_form"):
            email = st.text_input("Email", placeholder="user@example.com")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Konfirmasi Password", type="password")
            if st.form_submit_button("Daftar"):
                if not email or not password:
                    st.error("Email dan password wajib diisi!")
                elif password != confirm:
                    st.error("Password tidak cocok!")
                elif register_user(email, password):
                    st.success("Akun berhasil dibuat! Silakan login.")
                    goto('login')
                    st.rerun()
                else:
                    st.error("Email sudah terdaftar!")
        if st.button("Kembali ke Login"):
            goto('login')
else:
    st.sidebar.title(f"Selamat datang, {st.session_state.current_email}")
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # === INPUT PROFIL ===
    if st.session_state.page == 'input':
        st.title("Input Profil Siswa")

        name = st.text_input("Nama Lengkap", placeholder="Contoh: Gita Lewar")
        academic = st.selectbox("Minat Akademik", options=list(ACADEMIC_CODES.keys()))

        # Keterampilan
        st.subheader("Daftar Keterampilan")
        selected_skills = []
        cols = st.columns(2)
        for i, skill in enumerate(SKILL_LIST):
            if cols[i % 2].checkbox(skill, key=f"skill_{i}"):
                selected_skills.append(skill)

        # Ekstrakurikuler Dinamis
        st.subheader("Ekstrakurikuler yang Diikuti")
        for i in range(len(st.session_state.extracurricular_inputs)):
            cols = st.columns([3, 2, 2, 1])
            # Baca nilai saat ini dari session state
            current = st.session_state.extracurricular_inputs[i]
            
            # Buat selectbox
            act = cols[0].selectbox(
                "", 
                options=[""] + list(ACTIVITY_CODES.keys()),
                index=0 if current["activity"] == "" else list(ACTIVITY_CODES.keys()).index(current["activity"]) + 1,
                key=f"act_{i}",
                label_visibility="collapsed"
            )
            contrib = cols[1].slider("", 1, 5, current["contribution"], key=f"cont_{i}", label_visibility="collapsed")
            achiev = cols[2].slider("", 1, 5, current["achievement"], key=f"ach_{i}", label_visibility="collapsed")
            
            # SIMPAN KEMBALI ke session state
            st.session_state.extracurricular_inputs[i] = {
                "activity": act,
                "contribution": contrib,
                "achievement": achiev
            }
            
            if cols[3].button("🗑️", key=f"del_{i}"):
                st.session_state.extracurricular_inputs.pop(i)
                #st.rerun()

        if st.button("+ Tambah Ekstrakurikuler"):
            st.session_state.extracurricular_inputs.append({'activity': '', 'contribution': 3, 'achievement': 3})
            #st.rerun()

        # Ekstrakurikuler Utama
        st.subheader("Ekstrakurikuler Utama")
        main_act = st.selectbox("Pilih Ekstrakurikuler Utama", options=list(ACTIVITY_CODES.keys()))

        # Simpan & Proses (BUKAN form_submit_button!)
        if st.button("Simpan & Proses"):
            if not name.strip():
                st.error("Nama wajib diisi!")
            else:
                valid = [e for e in st.session_state.extracurricular_inputs if e["activity"] != ""]
                if not valid:
                    st.error("Harap tambahkan minimal satu ekstrakurikuler yang valid!")
                else:
                    avg_contrib = sum(e["contribution"] for e in valid) / len(valid)
                    avg_achiev = sum(e["achievement"] for e in valid) / len(valid)
                    club_count = len(valid)
                    skills_string = ", ".join(selected_skills)

                    st.session_state.student_profile = {
                    'name': name,
                    'minat': academic,               # ← string "IPA", bukan kode
                    'ekskul': main_act,              # ← string "OSIS", bukan kode
                    'skill': skills_string,          # ← string, bukan list
                    'club_count': club_count,
                    'contribution': avg_contrib,
                    'achievement': avg_achiev
                }
                    goto('process')
                    st.rerun()

   # === PROSES CLUSTERING ===
    elif st.session_state.page == 'process':
        st.title("⚙️ Proses Pengelompokan (K-Means)")
        prof = st.session_state.student_profile
        if prof:
            try:
                # 1. Muat data latih
                train_df = pd.read_csv("data/sample_data.csv")
                
                # 2. Ubah semua data latih ke vektor
                train_vectors = []
                for _, row in train_df.iterrows():
                    vec = student_to_vector({
                        "minat": row["minat"],
                        "ekskul": row["ekskul"],
                        "skill": row["skill"],
                        "club_count": row["club_count"],
                        "contribution": row["contribution"],
                        "achievement": row["achievement"]
                    })
                    train_vectors.append(vec)
                
                # 3. Ubah data siswa baru ke vektor
                new_vector = student_to_vector(prof)
                
                # 4. Gabungkan
                all_vectors = train_vectors + [new_vector]
                all_df = pd.DataFrame(all_vectors)
                
                # 5. Jalankan K-Means
                result_df, centroids, sse = run_kmeans(all_df, k=3)
                
                # 6. Ambil cluster ID untuk data terakhir (data siswa baru)
                new_cluster_id = result_df['ClusterID'].iloc[-1]
                
                st.session_state.cluster_result = {
                    'name': prof['name'],
                    'cluster_id': int(new_cluster_id),
                    'sse': sse,
                    'vector': new_vector
                }
                st.success(f"✅ Berhasil! Masuk ke **Cluster #{new_cluster_id}**")
                if st.button("Lihat Rekomendasi"):
                    goto('result')
                    st.rerun()
            except Exception as e:
                st.error(f"Error saat proses clustering: {str(e)}")
        else:
            st.warning("Tidak ada data siswa.")
            if st.button("Kembali ke Input"):
                goto('input')

   # === HASIL ===
    elif st.session_state.page == 'result':
        st.title("🎓 Rekomendasi Jurusan/Karier")
        
        # Pastikan cluster_result ada dan valid
        if not hasattr(st.session_state, 'cluster_result') or st.session_state.cluster_result is None:
            st.error("Belum ada hasil. Harap proses data terlebih dahulu.")
            if st.button("Kembali ke Input"):
                goto('input')
            st.stop()
        
        res = st.session_state.cluster_result
        
        # Validasi tambahan
        if 'name' not in res or 'cluster_id' not in res:
            st.error("Data hasil tidak lengkap. Silakan ulangi proses.")
            if st.button("Coba Lagi"):
                goto('input')
            st.stop()
        
        # Tampilkan hasil
        cluster_labels = {0: "Analytical", 1: "Creative", 2: "Leadership"}
        majors = {
            0: ["Ilmu Komputer", "Matematika", "Statistika"],
            1: ["DKV", "Sastra", "Film"],
            2: ["Manajemen", "Komunikasi", "Hubungan Internasional"]
        }
        cid = res['cluster_id']
        st.subheader(f"Selamat, **{res['name']}**!")
        st.write(f"Kamu termasuk dalam kelompok **{cluster_labels[cid]}**")
        for m in majors[cid]:
            st.markdown(f"🔹 {m}")
        st.metric("SSE", f"{res['sse']:.3f}")
        if st.button("Coba Lagi"):
            goto('input')
        #st.rerun()