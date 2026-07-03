# qa_runs/ — la evidencia de QA vive aquí

**Convención de nombre:** un directorio por corrida, `<rol|propósito>-<YYYYMMDD[-HHMMSS]>` — p. ej. `mariana-20260701-153000/`, `charbel-20260630/`, `pacenotes-20260701/`.

**Qué va adentro: artefactos reales del pipeline, no actas.** Screenshots, logs stdout/stderr, CSVs de comparación, WAVs, `metadata.json`, reportes generados. Un archivo que diga "validé y todo bien" **no es evidencia** (sin auto-firmas, ADR 0016); la evidencia es lo que la corrida produjo. El **veredicto** (pasó/falló y qué se decidió) no vive aquí: va a `HANDOFF.md` o al `CHANGELOG.md`, citando el directorio de la corrida.

**Por qué existe la exigencia (ADR 0019, homologado del starter v0.5.0):** un veredicto de QA visual sin artefacto no vale — las pruebas "clic por clic" que solo se afirmaron fallaron aquí mismo (v2.0: la UI estaba rota a ojo con "tests verdes"). El hook `mariana-stop` verifica mecánicamente que haya evidencia **posterior** al cambio visual antes de dejar cerrar.

**Git:** el bulto se ignora (`.gitignore`); la evidencia **citada** desde HANDOFF/CHANGELOG se commitea con `git add -f qa_runs/<corrida>/<archivo>` (solo lo citado, no la corrida entera — que ya van varios artefactos que se pierden por no vivir en el repo).
