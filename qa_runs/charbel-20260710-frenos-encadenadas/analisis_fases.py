"""Evidencia Charbel 2026-07-10: inspecciona los metros 803 y 1119 (frenadas
encadenadas reportadas por el PO) sobre la vuelta de REFERENCIA usada en el
E2E "mezcla" (qa_runs/mariana-20260709-mezcla-e2e).

Corre `select_brake_phase` (fantasma/core/corners.py) con las MISMAS ventanas
que usa `extract_milestones` para C03 y C05, e imprime las fases crudas
(distancia, tiempo, velocidad, pico de freno) para ver exactamente por que
se elige una fase y se descarta la otra.

Uso:
    python analisis_fases.py
"""
import sys

sys.path.insert(0, r"C:\Repositorios\SimGhostInputs")

from fantasma import importers
from fantasma.core.normalize import fastest_lap
from fantasma.core.corners import (
    BRAKE_LOOKBACK_M,
    BRAKE_ON,
    BRAKE_STRONG,
    PHASE_GAP_S,
    detect_corners,
    extract_milestones,
    select_brake_phase,
)

REF = r"C:\Users\jose_\Downloads\Pruebas finales\GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv"


def analyze(corners, data, corner_id, prev_apex_id, this_apex_id):
    apexes = {c["id"]: c["milestones"]["apex"]["d"] for c in corners}
    prev_apex = apexes[prev_apex_id]
    this_apex = apexes[this_apex_id]
    brake_lo = max(prev_apex, this_apex - BRAKE_LOOKBACK_M)
    window = [round(brake_lo), round(this_apex)]
    chosen, phases = select_brake_phase(data, window, BRAKE_ON, BRAKE_STRONG, PHASE_GAP_S)
    print(f"--- {corner_id} window={window} (prev_apex={prev_apex_id}:{prev_apex}, apex={this_apex_id}:{this_apex}) ---")
    for i, ph in enumerate(phases):
        d0, d1 = ph[0]["dist"], ph[-1]["dist"]
        t0, t1 = ph[0]["time"], ph[-1]["time"]
        v0, v1 = ph[0]["speed"], ph[-1]["speed"]
        peak = max(s["brake"] for s in ph)
        flag = " <== CHOSEN (brake_start del corner)" if ph is chosen else ""
        print(f"  fase {i}: d=[{d0:.0f},{d1:.0f}]m t=[{t0:.2f},{t1:.2f}]s v=[{v0:.0f}->{v1:.0f}]km/h peak_brake={peak:.0f}%{flag}")
        if i > 0:
            prev_last = phases[i - 1][-1]
            gap_s = ph[0]["time"] - prev_last["time"]
            still_braking = ph[0]["speed"] <= prev_last["speed"] + 2.0
            merge = gap_s < PHASE_GAP_S and still_braking
            print(f"    vs fase {i-1}: gap_s={gap_s:.2f} still_braking={still_braking} -> {'MERGE' if merge else 'FASE SEPARADA'}")
    print()


def main():
    laps = importers.load_laps(REF, None)
    lap = fastest_lap(laps)
    print(f"Vuelta de referencia: {lap.laptime:.1f}s, {lap.length:.0f}m\n")
    events, data = detect_corners(lap)
    corners = extract_milestones(lap, events)
    analyze(corners, data, "C03", "C02", "C03")  # metro 803
    analyze(corners, data, "C05", "C04", "C05")  # metro 1119


if __name__ == "__main__":
    main()
