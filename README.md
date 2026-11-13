# 🖱️ AI Virtual Mouse — Windows

**Controla el ordenador con la mano, sin tocar el ratón.** AI Virtual Mouse usa la
webcam para seguir tu mano en tiempo real y convierte tus gestos en movimientos de
cursor, clics, scroll, cambio de ventana y atajos. Todo se procesa en tu equipo: la
imagen de la cámara **no se guarda ni se envía a ningún sitio**.

Creado por **Albán Morera Peralta** · albanmoreram.p@gmail.com
Software propietario, todos los derechos reservados (ver [`LICENSE`](LICENSE)).

## ¿Para qué sirve?

- Manejar el PC **sin ratón** (a distancia, con las manos ocupadas, para presentaciones o desde el sofá).
- Alternativa para quien tiene dificultades para usar un ratón o un panel táctil.
- Cambiar de ventana con una mano mientras la otra mueve el cursor.

## Gestos

**Mano derecha — ratón**

| Gesto | Acción |
|---|---|
| ☝️ Índice estirado | Mover el cursor |
| 🤏 Tocar índice y pulgar | Clic izquierdo |
| 🤏🤏 Tocarlos dos veces | Doble clic (el 2.º toque cae en el mismo punto) |
| 🤏 Mantener la pinza ~1,5 s | Seleccionar / arrastrar archivos y ventanas |
| ✌️ Índice + medio juntos | Clic derecho |
| 👍 / 👎 Pulgar arriba / abajo | Scroll arriba / abajo (continuo, acelera) |
| ✊ Puño ~1 s | Pausar / reanudar |

**Mano izquierda — ventanas** (se detectan **las dos manos a la vez**)

| Gesto | Acción |
|---|---|
| 🤏 Pinza índice + pulgar | Ventana siguiente (Alt+Tab) |
| ✌️ Índice + medio juntos | Ventana anterior (Alt+Mayús+Tab) |

**Atajos (cualquier mano)**

| Gesto | Acción |
|---|---|
| 🤙 Shaka (pulgar + meñique) ~0,5 s | Abre Claude en tu navegador |
| 🤘 Rock (derecha) | Abre Spotify |
| 🤘 Rock (izquierda) | Abre Chrome en la página que configures (`CHROME_URL`) |

## Funciones

- **Frenado inteligente:** el cursor va más despacio sobre botones, enlaces, archivos y pestañas para acertar más fácil (Windows, UI Automation). Tecla `b` para activarlo o desactivarlo.
- **Clic preciso:** el clic cae donde estaba el cursor justo antes de juntar los dedos.
- **Panel lateral** con estado, gesto actual, última acción, mano detectada, velocidad, FPS y exposición.
- **Varias pantallas** y **varias cámaras** (selector al arrancar, se recuerda tu elección).
- **Exposición de la cámara** ajustable con los botones − / + / Auto del panel (menos exposición = más FPS con poca luz).
- **Icono junto al reloj** para pausar o salir, y **mini ventana** siempre encima (`m`).
- Velocidad del puntero ajustable con `+` / `-`.

## Teclas

`+` / `-` velocidad · `b` freno · `m` mini ventana · `v` cambiar cámara · `e` exposición automática · `q` / `Esc` salir

## Cómo usarlo

**Como programa (.exe)**
1. Descarga el zip de la sección **Releases** y descomprímelo.
2. Doble clic en `crear_exe.bat` (la primera vez tarda unos minutos).
3. Abre `AI Virtual Mouse.exe`.

**Con Python (3.10+)**
```
pip install opencv-python mediapipe pyautogui numpy pystray pillow comtypes pygrabber
python raton_virtual.py
```

Pon la cámara a la altura de la cara y la mano a 40–60 cm. El recuadro de esquinas blancas es la zona activa: mueve el dedo dentro de él.

## Personalizar

Los ajustes están al principio de `raton_virtual.py` (velocidad, umbrales de los gestos, mano de cada acción, `CHROME_PERFIL`, `CHROME_URL`, `INVERTIR_MANOS`…). Si tus manos salen al revés, cambia `INVERTIR_MANOS`.

## Requisitos

Windows 10/11, webcam, Python 3.10+ (solo si no usas el .exe). El modelo de la mano se descarga solo la primera vez.
