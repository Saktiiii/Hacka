ECOSHIFT STARTER - PROTOTIPE HACKATHON UNS

CARA MENJALANKAN (Windows):
1. Ekstrak ZIP.
2. Buka CMD/Terminal di folder EcoShift_Starter.
3. Jalankan: py -m venv venv
4. Jalankan: venv\Scripts\activate
5. Jalankan: python -m pip install -r requirements.txt
6. Jalankan: streamlit run app.py

CATATAN:
- Model durasi dan data awal masih sintetis, bukan ML tervalidasi dengan UMKM.
- Tahapan produksi di prediction.py hanya template diskusi, bukan standar semua UMKM.
- Konfirmasi daya mesin, urutan proses, kebutuhan pekerja, tarif, dan upah melalui observasi.
- VA dikonversi menjadi Watt dengan faktor daya dan margin aman 10% sebagai asumsi awal.
- Estimasi profit saat ini hanya pendapatan dikurangi listrik dan upah. Belum menghitung bahan,
  pewarna, malam, transportasi, penyusutan, pajak, dan biaya lain.
- Deadline disimpan pada data pesanan, tetapi optimasi tenggat multi-hari belum diterapkan.
- Penyimpanan masih menggunakan session_state; SQLite menjadi tahap pengembangan berikutnya.
