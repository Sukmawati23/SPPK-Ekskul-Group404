# models/kmeans_model.py

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np

def run_kmeans(df_features: pd.DataFrame, k: int = 3):
    if len(df_features) < k:
        # Jika data kurang dari k, gunakan k = jumlah data
        k = len(df_features)
        if k == 0:
            raise ValueError("Tidak ada data untuk dikelompokkan.")
        elif k == 1:
            # Jika hanya 1 data, beri cluster ID 0
            result_df = df_features.copy()
            result_df['ClusterID'] = 0
            return result_df, np.array([]), 0.0
    
    # Normalisasi & K-Means
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df_features)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(scaled_data)
    
    result_df = df_features.copy()
    result_df['ClusterID'] = labels
    return result_df, kmeans.cluster_centers_, kmeans.inertia_