import pandas as pd
import os

CSV_PATH = "data/students.csv"

def save_student_to_csv(student):
    print("🔥 save_student_to_csv DIPANGGIL")
    print(student)

    if not student:
        print("❌ student kosong")
        return

    os.makedirs("data", exist_ok=True)

    df = pd.DataFrame([student])

    if not os.path.exists(CSV_PATH):
        print("🆕 Membuat file students.csv")
        df.to_csv(CSV_PATH, index=False)
    else:
        print("➕ Append ke students.csv")
        df.to_csv(CSV_PATH, mode="a", header=False, index=False)

    print("✅ BERHASIL SIMPAN")
