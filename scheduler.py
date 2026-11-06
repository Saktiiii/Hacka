
import math
import pandas as pd


# =========================================
# FORMAT WAKTU
# =========================================

def fmt_jam(total_menit):
    total_menit = int(total_menit) % 1440

    jam = total_menit // 60
    menit = total_menit % 60

    return f"{jam:02d}:{menit:02d}"


# =========================================
# FUNGSI PENJADWALAN PRODUKSI
# =========================================

def buat_jadwal_produksi(
    df_ops,
    batas_watt,
    sumber_daya,
    jam_mulai,
    jam_selesai,
    slot_menit=30
):

    # Memeriksa OR-Tools
    try:
        from ortools.sat.python import cp_model

    except ImportError:
        return None, (
            "OR-Tools belum terpasang. "
            "Jalankan: python -m pip install ortools"
        )

    # Memeriksa data operasi
    if df_ops.empty:
        return None, "Belum ada operasi produksi."

    # Mengubah jam menjadi menit
    start_min = (
        jam_mulai.hour * 60 +
        jam_mulai.minute
    )

    end_min = (
        jam_selesai.hour * 60 +
        jam_selesai.minute
    )

    if (
        end_min <= start_min or
        (end_min - start_min) % slot_menit != 0
    ):
        return None, (
            f"Jam operasional harus valid dan "
            f"kelipatan {slot_menit} menit."
        )

    slots = (end_min - start_min) // slot_menit

    data = df_ops.reset_index(drop=True)

    # =====================================
    # MEMBUAT MODEL OPTIMASI
    # =====================================

    model = cp_model.CpModel()

    starts = []
    ends = []
    intervals = []
    power_demands = []
    durations = []

    machine_intervals = {
        "Kompor malam": [],
        "Pompa air": [],
        "Oven curing": []
    }

    worker_intervals = []
    worker_demands = []

    previous_end = {}

    # =====================================
    # MEMBUAT VARIABEL SETIAP TAHAP
    # =====================================

    for i, row in data.iterrows():

        duration = max(
            1,
            math.ceil(
                float(row["Durasi (Jam)"]) *
                60 / slot_menit
            )
        )

        if duration > slots:
            return None, (
                f"Durasi tahap {row['Tahap']} "
                "melebihi jam operasional."
            )

        s = model.NewIntVar(
            0,
            slots - duration,
            f"start_{i}"
        )

        e = model.NewIntVar(
            duration,
            slots,
            f"end_{i}"
        )

        interval = model.NewIntervalVar(
            s,
            duration,
            e,
            f"interval_{i}"
        )

        starts.append(s)
        ends.append(e)
        intervals.append(interval)
        durations.append(duration)

        # =================================
        # BATAS DAYA LISTRIK
        # =================================

        watt = int(row["Daya (Watt)"])

        if watt > batas_watt:
            return None, (
                f"Kebutuhan daya tahap {row['Tahap']} "
                f"melampaui batas efektif {batas_watt} W."
            )

        power_demands.append(watt)

        # =================================
        # KETERSEDIAAN MESIN
        # =================================

        machine = row["Mesin"]

        if machine in machine_intervals:
            machine_intervals[machine].append(interval)

        # =================================
        # KETERSEDIAAN PEKERJA
        # =================================

        worker_intervals.append(interval)

        worker_demands.append(
            int(row["Pekerja"])
        )

        # =================================
        # URUTAN TAHAP PRODUKSI
        # =================================

        code = row["Kode"]

        if code in previous_end:
            model.Add(
                s >= previous_end[code]
            )

        previous_end[code] = e

    # =====================================
    # MEMBATASI TOTAL DAYA LISTRIK
    # =====================================

    model.AddCumulative(
        intervals,
        power_demands,
        int(batas_watt)
    )

    # =====================================
    # MEMBATASI JUMLAH PEKERJA
    # =====================================

    model.AddCumulative(
        worker_intervals,
        worker_demands,
        max(
            1,
            int(sumber_daya["pekerja"])
        )
    )

    # =====================================
    # MEMBATASI JUMLAH MESIN
    # =====================================

    capacities = {
        "Kompor malam": int(sumber_daya["kompor"]),
        "Pompa air": int(sumber_daya["pompa"]),
        "Oven curing": int(sumber_daya["oven"])
    }

    for machine, items in machine_intervals.items():

        if items:

            if capacities[machine] < 1:
                return None, (
                    f"Tidak ada {machine.lower()} "
                    "yang berfungsi."
                )

            model.AddCumulative(
                items,
                [1] * len(items),
                capacities[machine]
            )

    # =====================================
    # OPTIMASI WAKTU PRODUKSI
    # =====================================

    makespan = model.NewIntVar(
        0,
        slots,
        "makespan"
    )

    for e in ends:
        model.Add(makespan >= e)

    model.Minimize(makespan)

    # =====================================
    # MENJALANKAN SOLVER
    # =====================================

    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = 10

    status = solver.Solve(model)

    if status not in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    ):
        return None, (
            "Jadwal tidak ditemukan. Periksa listrik, "
            "mesin, pekerja, dan jam kerja."
        )

    # =====================================
    # MEMBUAT HASIL JADWAL
    # =====================================

    rows = []

    for i, row in data.iterrows():

        a = (
            start_min +
            solver.Value(starts[i]) * slot_menit
        )

        b = (
            start_min +
            solver.Value(ends[i]) * slot_menit
        )

        rows.append({
            **row.to_dict(),

            "Mulai": fmt_jam(a),
            "Selesai": fmt_jam(b),

            "Mulai Menit": a,
            "Selesai Menit": b,

            "Durasi Terjadwal (Jam)": (
                durations[i] * slot_menit / 60
            )
        })

    result = pd.DataFrame(rows)

    result = (
        result
        .sort_values(["Mulai Menit", "Kode"])
        .reset_index(drop=True)
    )

    label = (
        "optimal"
        if status == cp_model.OPTIMAL
        else "layak"
    )

    return result, (
        f"Jadwal berhasil dibuat. "
        f"Status solusi: {label}."
    )
