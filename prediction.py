
"""
Model demonstrasi berbasis data sintetis.
Ganti dengan data aktual UMKM jika sudah tersedia.
"""

import numpy as np

from sklearn.ensemble import RandomForestRegressor


# =========================================
# JENIS PRODUKSI
# =========================================

JENIS = [
    "Batik Cap",
    "Batik Tulis",
    "Sablon/Printing"
]


# =========================================
# TAHAP PRODUKSI
# =========================================

TAHAP = {

    "Batik Cap": [
        ("Persiapan malam", "Kompor malam", 800, 1.0, 1),
        ("Pengecapan", "—", 0, 0.8, 2),
        ("Pewarnaan", "Pompa air", 300, 0.7, 2),
        ("Pengeringan/curing", "Oven curing", 1500, 0.6, 1),
        ("Finishing", "—", 0, 0.5, 2)
    ],

    "Batik Tulis": [
        ("Persiapan malam", "Kompor malam", 800, 1.0, 1),
        ("Pencantingan", "—", 0, 2.0, 2),
        ("Pewarnaan", "Pompa air", 300, 1.0, 2),
        ("Pengeringan", "Oven curing", 1500, 0.7, 1),
        ("Finishing", "—", 0, 0.6, 2)
    ],

    "Sablon/Printing": [
        ("Persiapan bahan", "—", 0, 0.5, 1),
        ("Printing", "—", 0, 1.0, 2),
        ("Pengeringan/curing", "Oven curing", 1500, 0.8, 1),
        ("Finishing", "—", 0, 0.4, 1)
    ]

}


# =========================================
# MELATIH MODEL RANDOM FOREST
# =========================================

def _train():

    rng = np.random.default_rng(42)

    X = []
    y = []

    factor = [1.0, 1.8, 0.75]

    for idx in range(3):

        for qty in range(10, 1001, 10):

            X.append([
                idx,
                qty
            ])

            y.append(
                0.35 +
                factor[idx] * (qty / 100) * 1.2 +
                rng.normal(0, 0.08)
            )

    model = RandomForestRegressor(
        n_estimators=80,
        random_state=42
    )

    return model.fit(
        np.array(X),
        np.array(y)
    )


# Membuat model ketika file diimpor
MODEL = _train()


# =========================================
# FUNGSI PREDIKSI DURASI
# =========================================

def prediksi_durasi(jenis, kuantitas):

    if jenis not in JENIS:
        raise ValueError(
            f"Jenis produksi '{jenis}' tidak tersedia."
        )

    idx = JENIS.index(jenis)

    scale = max(
        0.2,
        float(
            MODEL.predict(
                np.array([
                    [idx, int(kuantitas)]
                ])
            )[0]
        )
    )

    hasil = []

    for name, machine, watt, base, workers in TAHAP[jenis]:

        durasi = max(
            0.5,
            round(base * scale, 2)
        )

        hasil.append((
            name,
            machine,
            watt,
            durasi,
            workers
        ))

    return hasil
