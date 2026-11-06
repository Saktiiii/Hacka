def hitung_ekonomi(pesanan, hasil, tarif_kwh, jumlah_pekerja, upah_per_pekerja=100000):
    revenue = int((pesanan["Kuantitas"] * pesanan["Harga Jual"]).sum()) if not pesanan.empty else 0
    energy = float((hasil["Daya (Watt)"] * hasil["Durasi Terjadwal (Jam)"]).sum()/1000) if hasil is not None and not hasil.empty else 0
    electricity = energy * int(tarif_kwh)
    wages = int(jumlah_pekerja) * int(upah_per_pekerja)
    return {"Pendapatan": revenue, "Energi (kWh)": energy, "Biaya Listrik": electricity,
            "Upah Harian": wages, "Estimasi Profit": revenue-electricity-wages}
