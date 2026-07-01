# HANDOFF — relevo para la siguiente sesión

> **Documento vivo de continuidad:** léelo completo antes de tocar nada. El estado en-vuelo vive
> **aquí y en el repo**, nunca en la memoria de la IA. Si avanzas, **actualiza este archivo**.
> Reparto por caducidad: el [ADR](docs/decisions/) guarda *lo permanente* (por qué), el
> [CHANGELOG](CHANGELOG.md) *lo enviado* (qué cambió), el [ROADMAP](ROADMAP.md) *el camino a v1.0*,
> y este HANDOFF *lo efímero* (dónde voy, qué falta ahora).

## Pendiente inmediato

**PR #13 abierto — UI NiceGUI v2.0 + packaging.** Esperar CI verde (6 checks) y mergear.

Cuando mergee: ejecutar `python tools/build_installer.py` en la PC potente (SERVER via Oscar) para medir el bundle size real y resolver la incertidumbre del spike (objetivo: 150-250 MB one-dir). Ver checklist en [ROADMAP.md](ROADMAP.md) → «Front de escritorio custom (v2.0)».

## Para retomar en frío

Ver [ROADMAP.md](ROADMAP.md) → «Camino a la v1.0» y «Diferido post-v1.0».
