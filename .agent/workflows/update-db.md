---
description: Empaquetar y actualizar nueva base de datos CSV permanente en Github (Zip optimizado)
---

Ejecuta este workflow cada vez que el usuario agregue o reemplace el archivo `last_uploaded.csv` dentro de la carpeta `data/`. Esto garantiza que los 100MB se empaqueten dentro de los limites de subida gratuita de Github de forma automática, sin fallas y alimente a Streamlit Cloud.

// turbo-all

1. Comprime y reemplaza el ZIP anterior:
```bash
cd /Users/robertomigliore/Documents/Antigravity/data && rm -f dataset_base.zip && zip dataset_base.zip last_uploaded.csv
```

2. Añade los cambios:
```bash
cd /Users/robertomigliore/Documents/Antigravity && git add -f data/dataset_base.zip
```

3. Commit y confirmación:
```bash
cd /Users/robertomigliore/Documents/Antigravity && git commit -m "chore(data): Actualización de base de datos empaquetada"
```

4. Push hacia origen:
```bash
cd /Users/robertomigliore/Documents/Antigravity && git push origin main
```
