# Reportar una lección a Jidoka — la subida del lazo

> *La lección sube, la máquina baja.* Este repo trae maquinaria (hooks, gates, ritual)
> sembrada por [Jidoka](https://github.com/ArmandoMedina/jidoka). Cuando la usas y
> descubres algo —una regla que faltó, un gate que se pudrió, una idea que el método
> debería absorber— **no parchees tu maquinaria local**: repórtalo hacia arriba. Jidoka
> lo arregla con su propio ritual y tú bajas la corrección. Así las versiones no divergen.

## Por qué no lo arreglas aquí

Tu maquinaria del método (la sección `motor`: `verificar/auditar/probar-*`, hooks,
comandos y skills genéricos) es **común a todos los repos que siembran Jidoka**. Si la
parcheas solo aquí, tu copia diverge y el próximo `-Actualizar` te lo marca como conflicto.
El arreglo vive **una vez**, en Jidoka, y baja a todos. Tu **instancia** (tu ley
`blast-radius.json`, tu `product/`, tus ADRs, tu casting) sí es tuya y nunca se toca.

## Cómo subir una lección

1. **Ábrela con el helper** (abre el issue prellenado en el navegador):

   ```powershell
   ./tools/reportar-leccion.ps1
   ```

   O a mano: `https://github.com/ArmandoMedina/jidoka/issues/new?template=leccion.md`.

2. **Escribe la lección en una frase**, dónde la pagaste (anonimiza — disparo
   `frontera-nda`: nunca nombres de clientes, montos ni repos de trabajo; "caso N" basta)
   y qué haría Jidoka distinto.

3. **Regla 2-3**: 2-3 usos reales antes de que una lección se vuelva regla. Un solo uso
   también vale registrarlo: queda esperando su segundo.

## Cómo bajar la corrección

Cuando Jidoka publique el arreglo, corre desde el repo Jidoka apuntando a este repo:

```powershell
./tools/instalar.ps1 -Destino <ruta-de-este-repo> -Actualizar
```

Re-siembra **solo** la mecánica que no tocaste; lo que customizaste se preserva y se te
deja al lado como `<archivo>.jidoka-nuevo` para que reconcilies a mano (o muevas tu ajuste
a la costura `tools/verificar.local.ps1`). Corre en una rama → revisa el diff → PR.
Para saber si estás atrás: `./tools/estado-motor.ps1 -Jidoka <ruta-de-Jidoka>`.
