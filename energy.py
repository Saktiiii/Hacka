import pandas as pd

def hitung_batas_watt(kapasitas_va, faktor_daya, margin_aman=.90):
    return int(kapasitas_va * faktor_daya * margin_aman)

def buat_profil_beban(hasil, jam_mulai, jam_selesai):
    if hasil is None or hasil.empty:
        return pd.DataFrame(columns=["Waktu", "Daya (Watt)"])
    start = jam_mulai.hour * 60 + jam_mulai.minute
    finish = jam_selesai.hour * 60 + jam_selesai.minute
    rows = []
    for minute in range(start, finish, 30):
        active = hasil[(hasil["Mulai Menit"] <= minute) & (hasil["Selesai Menit"] > minute)]
        rows.append({"Waktu": f"{minute//60:02d}:{minute%60:02d}", "Daya (Watt)": int(active["Daya (Watt)"].sum())})
    return pd.DataFrame(rows)
