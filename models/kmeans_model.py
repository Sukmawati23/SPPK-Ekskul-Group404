# models/kmeans_model.py

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np

def run_kmeans(df_features: pd.DataFrame, k: int = 3):
    """
    Menjalankan K-Means Clustering pada DataFrame fitur numerik.
    
    Parameters:
    - df_features: DataFrame dengan semua fitur numerik (tanpa kolom ID/nama).
    - k: Jumlah cluster.
    
    Returns:
    - result_df: DataFrame input + kolom 'ClusterID'
    - centroids: array dari centroid (k x n_features)
    - sse: float, nilai inertia (SSE)
    """
    # Validasi: pastikan jumlah sampel >= k
    if len(df_features) < k:
        raise ValueError(f"Jumlah data ({len(df_features)}) kurang dari jumlah cluster yang diminta ({k}).")
    
    # Normalisasi
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df_features)
    
    # K-Means
    kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(scaled_data)
    
    # Tambahkan label ke data asli
    result_df = df_features.copy()
    result_df['ClusterID'] = labels
    
    return result_df, kmeans.cluster_centers_, kmeans.inertia_