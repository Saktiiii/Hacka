
def hitung_ekonomi(
    pesanan,
    hasil,
    tarif_kwh,
    jumlah_pekerja,
    upah_per_pekerja=100000
):
    # =========================================
    # 1. MENGHITUNG PENDAPATAN
    # =========================================

    revenue = (
        int(
            (
                pesanan["Kuantitas"] *
                pesanan["Harga Jual"]
            ).sum()
        )
        if not pesanan.empty else 0
    )

    # =========================================
    # 2. MENGHITUNG KONSUMSI ENERGI
    # =========================================

    energy = (
        float(
            (
                hasil["Daya (Watt)"] *
                hasil["Durasi Terjadwal (Jam)"]
            ).sum() / 1000
        )
        if hasil is not None and not hasil.empty else 0
    )

    # =========================================
    # 3. MENGHITUNG BIAYA LISTRIK
    # =========================================

    electricity = energy * int(tarif_kwh)

    # =========================================
    # 4. MENGHITUNG BIAYA GAJI
    # =========================================

    wages = (
        int(jumlah_pekerja) *
        int(upah_per_pekerja)
    )

    # =========================================
    # 5. MENGHITUNG ESTIMASI PROFIT
    # =========================================

    profit = revenue - electricity - wages

    return {
        "Pendapatan": revenue,
        "Energi (kWh)": energy,
        "Biaya Listrik": electricity,
        "Upah Harian": wages,
        "Estimasi Profit": profit
    }
