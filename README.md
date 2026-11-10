# Deutsch am Abend: tu curso diario de alemán con Claude

Cada tarde Claude te prepara una lección de 5–10 minutos (nivel A2 → B1):
- 6 palabras nuevas (vida diaria, IT y tecnología, oficina), con traducción al español
- una regla de gramática explicada en alemán sencillo, con un resumen en español
- ejercicios, también de escritura, que Claude puede corregirte

Cada domingo analiza tu semana y adapta las lecciones: más fáciles o más difíciles, gramática para repasar, palabras difíciles. Cada noche tus datos se copian en una hoja de Google con un panel de control y gráficos.

Todo queda en **tu** cuenta de Claude y en **tu** Google Drive. Nadie más ve tus datos.

## Qué necesitas
- Una cuenta de Claude con un plan que incluya tareas programadas y páginas (artifacts) con base de datos. Compruébalo en support.claude.com si no estás seguro.
- Una cuenta de Google, para la hoja de cálculo.

## Instalación (unos 10 minutos)
1. **Conecta Google**: en Claude, ve a Configuración → Conectores y conecta Google Drive (y Google Sheets, si aparece por separado).
2. **Abre un chat nuevo** en Claude.
3. **Descarga los archivos** de este repositorio (botón verde "Code" → "Download ZIP") y **adjunta estos 5**: `INSTRUCCIONES_PARA_CLAUDE.md`, `deutsch-am-abend.html`, `report.py`, `sheets.py`, `hoja.json`. (Este `README.md` no hace falta.)
4. **Escribe**:
   > Instala Deutsch am Abend siguiendo INSTRUCCIONES_PARA_CLAUDE.md.
5. Responde a la pregunta sobre tu zona horaria y aprueba lo que Claude te pida (publicar la página, crear la hoja y las tareas programadas).
6. Al final recibirás el enlace de tu página y el de tu hoja. Abre la página y pulsa **"Lektion jetzt erstellen"** para hacer tu primera lección hoy mismo.

## Horarios
- Lección nueva: cada día hacia las 18:45 (hora de Berlín)
- Análisis semanal: domingo hacia las 22:15
- Actualización de la hoja: cada noche hacia las 22:40

Si quieres otros horarios, pídeselo a Claude: "cambia la hora de mi lección de alemán a las 20:00".

## Consejos
- Si un ejercicio te parece incorrecto, pulsa "Aufgabe fehlerhaft?": no contará en tus estadísticas.
- En la pestaña "Fortschritt" ves tu plan semanal y tu progreso. En "Wörter" están todas tus palabras.
