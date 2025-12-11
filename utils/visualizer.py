# visualizer.py

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

def plot_cluster_summary(result_df: pd.DataFrame, k: int):
    """Plot ringkasan data dan status proses."""
    st.subheader("Ringkasan Data")
    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Siswa", len(result_df))
    col2.metric("Jumlah Fitur", len([col for col in result_df.columns if col != 'ClusterID']))
    col3.metric("Jumlah Cluster", k)
    
    st.subheader("Status Proses")
    st.progress(100, text=f"Selesai. {k} Cluster terbentuk.")

def plot_decision_matrix(df_scaled: pd.DataFrame):
    """Plot matriks keputusan (data terstandarisasi)."""
    st.subheader("Matriks Keputusan (Data Terstandarisasi)")
    st.dataframe(df_scaled, use_container_width=True)

def plot_recommendation_ranking(cluster_id: int, majors: dict, scores: list):
    """Plot ranking rekomendasi jurusan."""
    st.subheader("Ranking Rekomendasi")
    for i, (major, score) in enumerate(zip(majors[cluster_id], scores), 1):
        st.markdown(f"**{i}. {major}** <span style='float:right;'>{score:.2f}</span>", unsafe_allow_html=True)

def plot_recommendation_score_bar(scores: list, majors_list: list):
    """Plot bar chart skor rekomendasi."""
    st.subheader("Skor Rekomendasi")
    fig, ax = plt.subplots(figsize=(6, 4))
    bar_colors = ['blue', 'green', 'red', 'purple']
    ax.bar(range(len(scores)), scores, color=bar_colors[:len(scores)])
    ax.set_xticks(range(len(scores)))
    ax.set_xticklabels(majors_list, rotation=45, ha='right')
    ax.set_ylim(0, 1.2)
    ax.set_title("Skor Rekomendasi per Jurusan")
    st.pyplot(fig)

def plot_competency_profile(features: list, cluster_mean: list):
    """Plot radar chart profil kompetensi."""
    st.subheader("Profil Kompetensi")
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