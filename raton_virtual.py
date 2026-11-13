"""
===============================================================================
 AI VIRTUAL MOUSE v16  -  Ratón virtual con la mano y la webcam
 Creado por Albán Morera Peralta  ·  albanmoreram.p@gmail.com
===============================================================================
 GESTOS DE MANO (mano DERECHA; la izquierda también mueve el cursor y hace scroll)
   • Índice estirado                       -> mover el cursor (Landmark 8)
   • Toque índice + pulgar (1 vez)         -> clic izquierdo  (instantáneo)
   • Toque índice + pulgar (2 veces)       -> doble clic
   • Pinza índice + pulgar MANTENIDA 1,5 s -> SELECCIONAR: sigue con la pinza
     cerrada y mueve la mano para ampliar la selección; separa los dedos para
     terminar. (También sirve para arrastrar archivos y ventanas.)
   • PUÑO ✊ cerrado ~1 s                   -> PAUSAR el ratón virtual
     (otro puño ~1 s lo vuelve a activar)
   • Índice + medio estirados y juntos     -> clic derecho
   • Pulgar ARRIBA 👍 (resto de dedos cerrados) -> scroll arriba (continuo, acelera)
   • Pulgar ABAJO  👎 (resto de dedos cerrados) -> scroll abajo  (continuo, acelera)
   • Símbolo ROCK 🤘 (índice + meñique estirados, medio + anular doblados;
     el pulgar da igual) mantenido ~0,4 s:
       - con la mano DERECHA   -> abre Spotify
       - con la mano IZQUIERDA -> abre Chrome (perfil "Natanael") en Crunchyroll
     (en la ventana se ve qué mano detecta; si sale al revés: INVERTIR_MANOS)

 CAMBIAR DE VENTANA (con la mano IZQUIERDA)
   • Pinza índice + pulgar                 -> SIGUIENTE ventana  (Alt+Tab)
   • Índice + medio juntos                 -> ventana ANTERIOR   (Alt+Shift+Tab)
     El selector de ventanas se queda abierto ~0,8 s: si repites el gesto
     avanzas / retrocedes una más; al dejar de hacerlo se abre la elegida.

 PRECISIÓN
   • Al pasar por un BOTÓN, ENLACE, ARCHIVO, pestaña o menú el cursor va más
     despacio (más fácil acertar). Solo Windows; necesita 'pip install comtypes'
     (sin él solo frena sobre enlaces, cuando el cursor se convierte en una mano).
     Tecla 'b' = activar / desactivar.
   • El clic cae donde estaba el cursor JUSTO ANTES de juntar los dedos (al
     cerrar la pinza la punta del índice se mueve y arrastraba el cursor).
   • Doble clic: el 2º toque va SIEMPRE al mismo punto que el 1º, aunque la
     mano se haya movido un poco, y para el 2º toque basta con separar los
     dedos UN POCO (no hace falta abrirlos del todo).
   • Al empezar a juntar índice y pulgar, el cursor va más despacio (apuntas mejor).

 ABRIR CLAUDE
   • Shaka 🤙 (pulgar + meñique fuera, índice, medio y anular cerrados)
     mantenido ~0,5 s, con cualquier mano -> abre Claude en tu navegador predeterminado

 ICONO JUNTO AL RELOJ (necesita 'pip install pystray pillow')
   • Clic derecho -> Pausar / Reanudar, Salir

 VARIAS PANTALLAS
   • El recuadro morado cubre TODO el escritorio (todos los monitores).
     Pon VARIAS_PANTALLAS = False para usar solo la pantalla principal.

 CÁMARA
   • Si tienes varias cámaras, al arrancar se abre un selector con la imagen
     de cada una: pulsa 1, 2... para elegir. La elección se recuerda en
     'camara.json'. (Opcional: 'pip install pygrabber' para ver sus nombres.)

 TECLAS (con la ventana de vídeo seleccionada)
   • 'v'        -> cambiar de cámara (vuelve a abrir el selector)
   • Botones − / + / Auto del panel (con el ratón) -> bajar / subir la
                   exposición de un paso en un paso, o volver a automática.
                   (más negativo = imagen más oscura pero MÁS FPS con poca luz;
                   se recuerda para cada cámara)
   • 'e'        -> volver a exposición AUTOMÁTICA (si la imagen se ve negra)
   • '+' / '-'  -> subir / bajar la velocidad del puntero
   • 'c'        -> ajustes del driver de la cámara (solo Windows / DirectShow)
   • 'b'        -> activar / desactivar el freno sobre botones y archivos
   • 'm'        -> mini-ventana siempre encima (para ver la cámara mientras
                   usas otras aplicaciones sin minimizar)
   • 'q' o ESC  -> salir

 Prioridad de los gestos:
   0. Selección en curso (pinza mantenida)  -> SELECCIONAR
   1. Símbolo rock 🤘                        -> SPOTIFY / CHROME (cursor congelado)
   1b. Shaka 🤙                              -> CLAUDE (cursor congelado)
   2. Pinza índice-pulgar cerrándose        -> CLIC / DOBLE CLIC (cursor congelado)
   3. Solo índice + medio estirados         -> mueve; al juntarlos, CLIC DERECHO
   4. Pulgar arriba / abajo                 -> SCROLL (cursor congelado)
   5. Índice estirado                       -> MOVER
===============================================================================
"""

__author__ = "Albán Morera Peralta"
__email__ = "albanmoreram.p@gmail.com"
__version__ = "16.0"
CREDITO = "Creado por " + __author__

import json
import math
from collections import deque
import os
import platform
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

import cv2
import mediapipe as mp
import numpy as np
import pyautogui
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# =============================================================================
# 1. CONFIGURACIÓN (ajusta estos valores a tu gusto)
# =============================================================================
CAM_INDEX = None              # None = elegir con el selector (y recordarla).
                              # Pon 0, 1... para usar siempre esa cámara sin preguntar.
MAX_CAMERAS = 5               # cuántas posiciones de cámara se buscan al arrancar
CAM_WIDTH, CAM_HEIGHT = 640, 480
CAM_FPS_OPCIONES = (60, 30)   # FPS que se piden a la cámara; se prueban y se usa el que
                              # dé MÁS FPS reales (muchas webcam USB llegan a 60 en MJPG)
PROCESS_MAX_WIDTH = 640       # si la cámara entrega imágenes más grandes, se reducen a
                              # este ancho antes de analizarlas (más rápido, misma precisión)
FORCE_EXPOSURE = None         # exposición inicial: None = automática
EXPOSURE_MIN, EXPOSURE_MAX = -11, -1   # límites de los botones − / + (DirectShow: más
                                       # negativo = imagen más oscura pero más FPS)
EXPOSURE_DEFAULT = -5         # desde "Auto", si la cámara no dice su valor actual

# --- Recuadro activo (morado): cuanto MENOR el margen, MÁS GRANDE el recuadro --
MARGIN_X = 40
MARGIN_TOP = 30
MARGIN_BOTTOM = 60

# --- Velocidad del puntero (cambiable en directo con + y -) ------------------
SENSIBILIDAD = 1.5

# --- Suavizado adaptativo ------------------------------------------------------
ALPHA_LENTO = 0.20            # mano casi quieta: mucho suavizado (sin temblor)
ALPHA_RAPIDO = 0.85           # mano rápida: casi sin retraso
VELOCIDAD_RAPIDA_PX = 120
DEAD_ZONE_PX = 2

# --- Clic izquierdo / doble clic (toque índice + pulgar) ----------------------
# Distancias en 3D (incluye profundidad) divididas por el tamaño de la mano.
# Mira el valor "Pinza" en pantalla para calibrarlas.
PINCH_THRESHOLD = 0.30        # por debajo -> toque
PINCH_RELEASE = 0.38          # por encima -> dedos separados, listo para otro toque
                              # (margen pequeño = puedes dar el 2º toque muy rápido)
MIN_TAP_INTERVAL = 0.10       # anti-rebote: ignora "toques" más seguidos que esto
DOUBLE_TAP_WINDOW = 0.8       # 2º toque antes de este tiempo -> DOBLE CLIC
# Tras un clic, el cursor se queda clavado hasta que pase DOUBLE_TAP_WINDOW,
# salvo que muevas la mano más de esta distancia (en píxeles de pantalla,
# medida con el NUDILLO del índice, que apenas se mueve al hacer la pinza).
# El 2º toque cae EXACTAMENTE en el punto del 1º (Windows lo exige).
TAP_LOCK_RADIUS_PX = 120
# El clic se hace donde estaba el cursor cuando los dedos aún estaban abiertos
# (al cerrar la pinza la punta del índice se desplaza y movía el cursor).
PINCH_APPROACH = 0.55         # pinza por encima de esto = dedos "abiertos"
RIGHT_APPROACH = 0.50         # lo mismo para índice + medio (clic derecho)
REWIND_MAX_AGE = 0.6          # segundos: si los dedos tardaron más en cerrarse, no se corrige
REWIND_MAX_PX = 150           # corrección máxima (píxeles de pantalla)
DOUBLE_REARM_DELTA = 0.08     # 2º toque del doble clic: basta con separar los dedos esto
                              # (en el valor "Pinza") y volver a juntarlos
FRENO_AL_CLICAR = True        # el cursor va despacio mientras juntas los dedos para clicar
CLIC_CERRANDO_DELTA = 0.05    # cuánto tiene que bajar "Pinza" en 0,2 s para entender
                              # que vas a hacer clic (con la mano quieta no frena)

# --- Clic derecho (índice + medio juntos) -------------------------------------
RIGHT_THRESHOLD = 0.27
RIGHT_RELEASE = 0.38
RIGHT_COOLDOWN = 0.5

# --- Scroll con el pulgar arriba 👍 / abajo 👎 ------------------------------------
THUMB_ANGLE = 40              # grados de margen respecto a la vertical para que el pulgar
                              # cuente como "arriba" o "abajo"
THUMB_EXT_MIN = 0.65          # el pulgar tiene que estar FUERA: su punta lejos del nudillo
                              # del índice (fracción de la palma). Más bajo = más fácil
SCROLL_START_DELAY = 0.20     # segundos con el pulgar arriba/abajo antes de empezar (evita
                              # scroll accidental al girar la mano)
SCROLL_SPEED_MIN = 4          # muescas de rueda por segundo al empezar
SCROLL_SPEED_MAX = 20         # muescas por segundo tras mantenerlo SCROLL_ACCEL_TIME
SCROLL_ACCEL_TIME = 1.5       # segundos hasta alcanzar la velocidad máxima
SCROLL_INVERTIDO = False      # True = pulgar arriba baja la página

# --- Símbolo rock 🤘: mano derecha -> Spotify, mano izquierda -> Chrome ---------
ROCK_HOLD_TIME = 0.4          # segundos manteniendo el gesto para disparar
SPOTIFY_COOLDOWN = 5.0        # segundos mínimos entre dos aperturas (de cada acción)
SPOTIFY_WEB = False           # True = abrir Spotify en el navegador en vez de la app
ROCK_MANO_SPOTIFY = "derecha" # la OTRA mano abre Chrome
CHROME_PERFIL = "Natanael"    # nombre del perfil de Chrome tal como sale en Chrome
CHROME_URL = "https://www.crunchyroll.com/es-es/series/GRE50KV36/black-clover"
INVERTIR_MANOS = True         # con tu cámara MediaPipe identifica las manos al revés;
                              # pon False si la ventana dice "izquierda" con tu mano derecha

# --- Seleccionar: pinza índice + pulgar mantenida -------------------------------
SELECT_HOLD_TIME = 1.5        # segundos con la pinza cerrada para empezar a seleccionar
SELECT_END_GRACE = 0.20       # segundos que se tolera que la pinza "se abra" sin terminar
                              # (por si la detección parpadea)

# --- Pausa con el puño ------------------------------------------------------------
PAUSE_HOLD_TIME = 1.0         # segundos con el puño cerrado para pausar / reanudar
                              # (evita pausas accidentales al cerrar la mano un momento)

# --- Cambiar de ventana con la mano IZQUIERDA ------------------------------------
# Pinza índice+pulgar = siguiente (Alt+Tab) · índice+medio juntos = anterior
VENTANA_MANO = "izquierda"    # mano que cambia de ventana (la otra hace los clics)
WINDOW_SWITCH_HOLD = 0.8      # segundos que el selector de ventanas sigue abierto
                              # esperando otro gesto (0 = Alt+Tab simple cada vez)
WINDOW_COOLDOWN = 0.25        # anti-rebote entre dos cambios de ventana
SIDE_STABLE_FRAMES = 3        # frames seguidos para aceptar que cambió la mano
                              # (evita que un fallo de 1 frame dé un clic con la izquierda)

# --- Shaka 🤙 (pulgar + meñique) -> abrir Claude ---------------------------------
CLAUDE_URL = "https://claude.ai"   # se abre en el navegador predeterminado
SHAKA_HOLD_TIME = 0.5         # segundos manteniendo el gesto para abrir Claude
SHAKA_COOLDOWN = 3.0          # segundos mínimos entre dos aperturas

# --- Frenar el cursor sobre botones y archivos (Windows) -------------------------
FRENAR_EN_BOTONES = True      # tecla 'b' para activar / desactivar
FRENO_FACTOR = 0.35           # velocidad encima de un botón (0.35 = 35 % de la normal)
FRENO_RECUPERACION = 0.5      # al salir, el cursor vuelve a alcanzar a la mano poco a poco
                              # mientras la mueves (más alto = lo alcanza antes)
FRENO_TAMANO_MAX = 160        # solo se frena si el elemento es "pequeño": su lado menor
                              # mide como mucho esto (una tarjeta gigante no frena)
FRENO_CONSULTAS_S = 25        # veces por segundo que se mira qué hay bajo el cursor

# --- Comodidad ----------------------------------------------------------------
ICONO_BANDEJA = True          # icono junto al reloj (pip install pystray pillow)
VARIAS_PANTALLAS = True       # el cursor recorre todos los monitores

HAND_GRACE_FRAMES = 4

# --- Rutas (funciona igual como .py y como .exe) -------------------------------
def _app_dir():
    """Carpeta del programa: junto al .exe si está empaquetado, o junto al .py."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


SCRIPT_DIR = _app_dir()
# Dentro del .exe, PyInstaller descomprime los archivos incluidos en _MEIPASS
BUNDLE_DIR = getattr(sys, "_MEIPASS", SCRIPT_DIR)
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
# El .exe lleva el modelo dentro; si no, se usa / descarga junto al programa
_BUNDLED_MODEL = os.path.join(BUNDLE_DIR, "hand_landmarker.task")
MODEL_PATH = (_BUNDLED_MODEL if os.path.exists(_BUNDLED_MODEL)
              else os.path.join(SCRIPT_DIR, "hand_landmarker.task"))
CAMERA_CHOICE_PATH = os.path.join(SCRIPT_DIR, "camara.json")

# Landmarks de la mano
WRIST = 0
THUMB_MCP, THUMB_IP, THUMB_TIP = 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP = 9, 10, 12
RING_PIP, RING_TIP = 14, 16
PINKY_MCP, PINKY_PIP, PINKY_TIP = 17, 18, 20

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),            # pulgar
    (0, 5), (5, 6), (6, 7), (7, 8),            # índice
    (5, 9), (9, 10), (10, 11), (11, 12),       # medio
    (9, 13), (13, 14), (14, 15), (15, 16),     # anular
    (13, 17), (17, 18), (18, 19), (19, 20),    # meñique
    (0, 17),                                   # palma
]

# =============================================================================
# 2. CONFIGURACIÓN DE PYAUTOGUI Y DEL SISTEMA
# =============================================================================
pyautogui.PAUSE = 0           # sin la pausa de 0,1 s que PyAutoGUI añade por defecto
pyautogui.FAILSAFE = True     # ratón FÍSICO a una esquina = parada de emergencia
IS_WINDOWS = platform.system() == "Windows"
SCROLL_UNIT = 120 if IS_WINDOWS else 1      # en Windows 120 = 1 muesca de rueda
PRIMARY_W, PRIMARY_H = pyautogui.size()     # pantalla principal


def virtual_screen():
    """
    Rectángulo que contiene TODOS los monitores (Windows). Puede empezar en
    coordenadas negativas si hay un monitor a la izquierda o encima del principal.
    """
    if IS_WINDOWS and VARIAS_PANTALLAS:
        try:
            import ctypes
            gsm = ctypes.windll.user32.GetSystemMetrics
            x0, y0, w, h = gsm(76), gsm(77), gsm(78), gsm(79)   # SM_*VIRTUALSCREEN
            if w > 0 and h > 0:
                return x0, y0, w, h
        except Exception:  # noqa: BLE001
            pass
    return 0, 0, PRIMARY_W, PRIMARY_H


SCREEN_X0, SCREEN_Y0, SCREEN_W, SCREEN_H = virtual_screen()
# Esquinas de emergencia (FAILSAFE) = esquinas del escritorio completo
pyautogui.FAILSAFE_POINTS = [(SCREEN_X0, SCREEN_Y0),
                             (SCREEN_X0 + SCREEN_W - 1, SCREEN_Y0),
                             (SCREEN_X0, SCREEN_Y0 + SCREEN_H - 1),
                             (SCREEN_X0 + SCREEN_W - 1, SCREEN_Y0 + SCREEN_H - 1)]


def os_double_click_time():
    """Tiempo máximo entre dos clics que el sistema acepta como doble clic."""
    if IS_WINDOWS:
        try:
            import ctypes
            return ctypes.windll.user32.GetDoubleClickTime() / 1000.0
        except Exception:  # noqa: BLE001
            pass
    return 0.5


OS_DOUBLE_CLICK_TIME = os_double_click_time()


def boost_windows_process():
    """
    Evita que Windows frene el programa cuando su ventana se minimiza o pasa a
    segundo plano (eso bajaba los FPS a ~8). Hace tres cosas:
      1. Desactiva el "Power Throttling" / modo eficiencia (EcoQoS): Windows
         deja de bajar la velocidad del procesador para este programa y de
         mandarlo a los núcleos lentos ("E-cores") de los Intel modernos.
      2. Pide que NO se ignore la resolución del temporizador al minimizar
         (Windows 11 la empeora para ventanas ocultas).
      3. Sube la prioridad del proceso a ALTA y el temporizador a 1 ms.
    Si algo falla (Windows antiguo, permisos...) simplemente se ignora.
    """
    if not IS_WINDOWS:
        return
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    process = kernel32.GetCurrentProcess()
    applied = []

    # 1 y 2) Desactivar Power Throttling (velocidad de ejecución + temporizador)
    class PROCESS_POWER_THROTTLING_STATE(ctypes.Structure):
        _fields_ = [("Version", wintypes.ULONG),
                    ("ControlMask", wintypes.ULONG),
                    ("StateMask", wintypes.ULONG)]

    PROCESS_POWER_THROTTLING_CURRENT_VERSION = 1
    PROCESS_POWER_THROTTLING_EXECUTION_SPEED = 0x1
    PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION = 0x4
    PROCESS_INFORMATION_CLASS_POWER_THROTTLING = 4
    try:
        kernel32.SetProcessInformation.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                                   ctypes.c_void_p, wintypes.DWORD]
        kernel32.SetProcessInformation.restype = wintypes.BOOL
        for mask, name in ((PROCESS_POWER_THROTTLING_EXECUTION_SPEED, "sin modo eficiencia"),
                           (PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION,
                            "temporizador preciso al minimizar")):
            # ControlMask = qué controlamos; StateMask = 0 -> throttling DESACTIVADO
            state = PROCESS_POWER_THROTTLING_STATE(PROCESS_POWER_THROTTLING_CURRENT_VERSION,
                                                   mask, 0)
            if kernel32.SetProcessInformation(process, PROCESS_INFORMATION_CLASS_POWER_THROTTLING,
                                              ctypes.byref(state), ctypes.sizeof(state)):
                applied.append(name)
    except (AttributeError, OSError):
        pass                                        # Windows 7/8: no existe esta función

    # 3) Prioridad alta y temporizador de 1 ms
    try:
        HIGH_PRIORITY_CLASS = 0x00000080
        kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        if kernel32.SetPriorityClass(process, HIGH_PRIORITY_CLASS):
            applied.append("prioridad alta")
    except (AttributeError, OSError):
        pass
    try:
        if ctypes.WinDLL("winmm").timeBeginPeriod(1) == 0:
            applied.append("temporizador 1 ms")
    except (AttributeError, OSError):
        pass

    if applied:
        print("[INFO] Rendimiento en segundo plano: " + ", ".join(applied))


# =============================================================================
# 3. CÁMARA: elegir automáticamente el modo más rápido
# =============================================================================
def apply_exposure(cap, value):
    """None = exposición automática; número = fija (más negativo = más corta)."""
    if value is None:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)   # 0.75 = automática en DirectShow
    else:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)   # 0.25 = manual en DirectShow
        cap.set(cv2.CAP_PROP_EXPOSURE, value)


def open_camera_mode(index, backend, use_mjpg, fps=30, exposure=None):
    """Abre la cámara 'index' con un backend/formato/FPS concreto. Devuelve cap o None."""
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        cap.release()
        return None
    if use_mjpg:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if exposure is not None:
        apply_exposure(cap, exposure)
    return cap


def measure_fps(cap, warmup=8, frames=30):
    """
    Lee unos frames y mide los FPS REALES que entrega la cámara. Devuelve
    (fps, ancho, alto). El calentamiento descarta los primeros frames, que
    muchas cámaras entregan más despacio mientras ajustan la luz.
    """
    shape = (0, 0)
    for _ in range(warmup):
        ok, frame = cap.read()
        if not ok:
            return 0.0, 0, 0
        shape = frame.shape[:2]
    t0 = time.time()
    for _ in range(frames):
        if not cap.read()[0]:
            return 0.0, 0, 0
    return frames / max(time.time() - t0, 1e-6), shape[1], shape[0]


def open_best_camera(index, several_cameras=False, exposure=None):
    """
    Prueba varios modos de la cámara 'index' (formato MJPG o normal, 60 o 30
    FPS...) con la exposición elegida y se queda con el que da MÁS FPS reales.
    Devuelve (cap, backend, texto_descriptivo).
    """
    if IS_WINDOWS:
        candidates = [(f"DirectShow MJPG {f}", cv2.CAP_DSHOW, True, f) for f in CAM_FPS_OPCIONES]
        candidates.append(("DirectShow 30", cv2.CAP_DSHOW, False, 30))
        # Media Foundation numera las cámaras a su manera: con varias cámaras el
        # mismo número podría abrir OTRA cámara, así que solo se prueba si hay una.
        if not several_cameras:
            candidates.append(("Media Foundation", cv2.CAP_MSMF, False, max(CAM_FPS_OPCIONES)))
    else:
        candidates = [(f"MJPG {f}", cv2.CAP_ANY, True, f) for f in CAM_FPS_OPCIONES]
        candidates.append(("Por defecto 30", cv2.CAP_ANY, False, 30))

    print(f"[INFO] Probando modos de la cámara {index} (tarda unos segundos)...")
    best = None
    for name, backend, mjpg, req_fps in candidates:
        cap = open_camera_mode(index, backend, mjpg, req_fps, exposure)
        if cap is None:
            print(f"       {name:<22} no disponible")
            continue
        fps, w, h = measure_fps(cap)
        cap.release()
        print(f"       {name:<22} {fps:5.1f} FPS  ({w}x{h})")
        if best is None or fps > best[4] + 1:          # +1: en empate, el primero (MJPG)
            best = (name, backend, mjpg, req_fps, fps, w, h)
        if fps >= max(CAM_FPS_OPCIONES) * 0.9:          # ya va al máximo: no hace falta seguir
            break

    if best is None:
        print(f"[ERROR] No se pudo abrir la cámara {index}. Revisa que no la esté usando "
              "otro programa y los permisos de cámara de Windows.")
        sys.exit(1)

    name, backend, mjpg, req_fps, fps, w, h = best
    info = f"{name} - {w}x{h} a {fps:.0f} FPS"
    print(f"[INFO] Usando: {info}")
    if fps < 20:
        print("[AVISO] Pocos FPS. Casi siempre es por poca luz: enciende una lámpara o")
        print("        baja la exposición con el botón − del panel (más oscura, más FPS).")
    return open_camera_mode(index, backend, mjpg, req_fps, exposure), backend, info


# --- Elegir entre varias cámaras ----------------------------------------------
def _probe_backend():
    return cv2.CAP_DSHOW if IS_WINDOWS else cv2.CAP_ANY


def list_cameras():
    """Busca qué cámaras hay (posiciones 0..MAX_CAMERAS-1) y que den imagen."""
    found = []
    for i in range(MAX_CAMERAS):
        cap = cv2.VideoCapture(i, _probe_backend())
        if cap.isOpened():
            ok, _ = cap.read()
            if ok:
                found.append(i)
        cap.release()
    return found


def camera_names():
    """
    Nombres de las cámaras en el mismo orden que OpenCV (DirectShow). Necesita
    'pip install pygrabber' (opcional); si no está, devuelve {} y se usan
    nombres genéricos.
    """
    if not IS_WINDOWS:
        return {}
    try:
        from pygrabber.dshow_graph import FilterGraph
        return dict(enumerate(FilterGraph().get_input_devices()))
    except Exception:  # noqa: BLE001
        return {}


def camera_label(index, names):
    return names.get(index, f"Camara {index}")


def load_camera_choice():
    try:
        with open(CAMERA_CHOICE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write_camera_file(data):
    try:
        with open(CAMERA_CHOICE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def save_camera_choice(index, names):
    data = load_camera_choice() or {}
    data.update({"indice": index, "nombre": names.get(index, "")})
    _write_camera_file(data)


def load_exposure(index, names):
    """Exposición guardada para esta cámara (por nombre), o la de la configuración."""
    data = load_camera_choice() or {}
    return data.get("exposiciones", {}).get(names.get(index, f"camara {index}"), FORCE_EXPOSURE)


def save_exposure(index, names, value):
    data = load_camera_choice() or {}
    data.setdefault("exposiciones", {})[names.get(index, f"camara {index}")] = value
    _write_camera_file(data)


def choose_camera_window(indices, names, current=None):
    """
    Ventana con la imagen EN DIRECTO de cada cámara, una al lado de otra.
    Pulsa 1, 2... para elegir; ESC (o cerrar) = quedarse con la actual / la primera.
    """
    caps = {}
    for i in indices:
        cap = cv2.VideoCapture(i, _probe_backend())
        if cap.isOpened():
            caps[i] = cap
    win = "Elige la camara (pulsa 1, 2...)"
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
    chosen = None
    tile_w, tile_h = 400, 300
    try:
        while chosen is None:
            tiles = []
            for n, i in enumerate(indices, start=1):
                ok, frame = caps[i].read() if i in caps else (False, None)
                if ok:
                    h, w = frame.shape[:2]
                    # Mantener la proporción de la imagen (bandas negras si hace falta)
                    scale = min(tile_w / w, tile_h / h)
                    small = cv2.resize(cv2.flip(frame, 1), (int(w * scale), int(h * scale)))
                    tile = np.zeros((tile_h, tile_w, 3), np.uint8)
                    oy, ox = (tile_h - small.shape[0]) // 2, (tile_w - small.shape[1]) // 2
                    tile[oy:oy + small.shape[0], ox:ox + small.shape[1]] = small
                    res = f"{w}x{h}"
                else:
                    tile = np.full((tile_h, tile_w, 3), 40, np.uint8)
                    res = "sin imagen"
                color = (0, 255, 0) if i == current else (255, 255, 255)
                cv2.rectangle(tile, (0, 0), (tile_w, 62), (0, 0, 0), cv2.FILLED)
                cv2.putText(tile, f"{n}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 3)
                cv2.putText(tile, camera_label(i, names)[:28], (60, 26),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.putText(tile, res + ("  (actual)" if i == current else ""), (60, 52),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                cv2.rectangle(tile, (0, 0), (tile_w - 1, tile_h - 1), color, 2)
                tiles.append(tile)
            # Filas de 3 cámaras como máximo
            while len(tiles) % min(3, len(indices)):
                tiles.append(np.full((tile_h, tile_w, 3), 20, np.uint8))
            per_row = min(3, len(indices))
            rows = [cv2.hconcat(tiles[k:k + per_row]) for k in range(0, len(tiles), per_row)]
            board = cv2.vconcat(rows)
            cv2.putText(board, "Pulsa el NUMERO de la camara que quieres usar  (ESC = cancelar)",
                        (10, board.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
            cv2.imshow(win, board)
            key = cv2.waitKey(30) & 0xFF
            if ord("1") <= key <= ord("9") and key - ord("1") < len(indices):
                chosen = indices[key - ord("1")]
            elif key == 27 or cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < 1:
                chosen = current if current is not None else indices[0]
    finally:
        for cap in caps.values():
            cap.release()
        cv2.destroyWindow(win)
        cv2.waitKey(1)
    return chosen


def select_camera(ask=False, current=None):
    """
    Decide qué cámara usar. Devuelve (índice, lista_de_cámaras, nombres).
      • CAM_INDEX fijo en la configuración -> esa, sin preguntar.
      • Una sola cámara -> esa.
      • Varias: la recordada en 'camara.json' (buscándola por NOMBRE, por si
        Windows ha cambiado el orden al enchufar/desenchufar) o el selector.
      • ask=True (tecla 'v') -> siempre el selector.
    """
    if CAM_INDEX is not None and not ask:
        return CAM_INDEX, [CAM_INDEX], {}
    print("[INFO] Buscando cámaras...")
    cams = list_cameras()
    names = camera_names()
    for i in cams:
        print(f"       {i}: {camera_label(i, names)}")
    if not cams:
        print("[ERROR] No se ha encontrado ninguna cámara.")
        sys.exit(1)
    if len(cams) == 1:
        return cams[0], cams, names
    if not ask:
        saved = load_camera_choice()
        if saved:
            by_name = [i for i in cams if saved.get("nombre") and names.get(i) == saved["nombre"]]
            if by_name:
                return by_name[0], cams, names
            # Sin nombres disponibles (p. ej. sin pygrabber): por su número
            if saved.get("indice") in cams and (not saved.get("nombre") or not names):
                return saved["indice"], cams, names
    index = choose_camera_window(cams, names, current)
    save_camera_choice(index, names)
    print(f"[INFO] Cámara elegida: {index} ({camera_label(index, names)})")
    return index, cams, names


class CameraStream:
    """Lee la cámara en un hilo de fondo y guarda solo el último frame."""

    def __init__(self, cap):
        self.cap = cap
        self.frame = None
        self.frame_id = 0               # cuenta los frames que entrega la cámara (para sus FPS)
        self.running = True
        self.lock = threading.Lock()
        self.cap_lock = threading.Lock()  # para cambiar ajustes sin chocar con la lectura
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def set_exposure(self, value):
        with self.cap_lock:
            apply_exposure(self.cap, value)

    def get_exposure(self):
        """Valor de exposición que dice la cámara ahora (None si no lo da)."""
        with self.cap_lock:
            try:
                v = float(self.cap.get(cv2.CAP_PROP_EXPOSURE))
            except Exception:  # noqa: BLE001
                return None
        return int(round(v)) if EXPOSURE_MIN - 2 <= v <= 0 and v != 0 else None

    def _update(self):
        while self.running:
            with self.cap_lock:
                ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.005)
                continue
            with self.lock:
                self.frame = frame
                self.frame_id += 1

    def read(self):
        with self.lock:
            return self.frame_id, self.frame

    def stop(self):
        self.running = False
        self.thread.join(timeout=1)
        self.cap.release()


def exposure_step(current, delta, camera_value=None):
    """Un paso de exposición: delta +1 = más luz, -1 = menos. None = automática."""
    if current is None:
        current = camera_value if camera_value is not None else EXPOSURE_DEFAULT
        current = min(max(current, EXPOSURE_MIN), EXPOSURE_MAX)
        if delta > 0 and current >= EXPOSURE_MAX or delta < 0 and current <= EXPOSURE_MIN:
            return current
    return min(max(current + delta, EXPOSURE_MIN), EXPOSURE_MAX)


# =============================================================================
# 3b. ¿HAY UN BOTÓN / ARCHIVO DEBAJO DEL CURSOR?  (Windows UI Automation)
# =============================================================================
# Tipos de control de UI Automation que se pueden pulsar
UIA_CLICABLES = {
    50000: "boton", 50002: "casilla", 50003: "desplegable", 50005: "enlace",
    50007: "elemento", 50011: "menu", 50013: "opcion", 50019: "pestana",
    50024: "elemento", 50029: "archivo", 50031: "boton", 50035: "columna",
}
UIA_CONTENIDO = {50020, 50006, 50025}   # texto / imagen / personalizado: mirar al padre


def clickable_rect(element, control_type, rect_of, parent_of, levels=2):
    """
    Si 'element' (o su padre / abuelo, cuando el cursor está sobre el texto o el
    icono de un botón) se puede pulsar y es pequeño, devuelve (rect, nombre).
    Si no, None. Recibe funciones para poder probarla sin Windows.
    """
    for _ in range(levels + 1):
        if element is None:
            return None
        ct = control_type(element)
        if ct in UIA_CLICABLES:
            l, t, r, b = rect_of(element)
            if r - l > 0 and b - t > 0 and min(r - l, b - t) <= FRENO_TAMANO_MAX:
                return (l, t, r, b), UIA_CLICABLES[ct]
            return None
        if ct not in UIA_CONTENIDO:
            return None
        element = parent_of(element)
    return None


class ClickableWatcher:
    """
    Hilo que mira ~25 veces por segundo qué hay debajo del cursor:
      • con UI Automation (pip install comtypes): botones, enlaces, archivos,
        pestañas, menús... y guarda el RECTÁNGULO del elemento, así el bucle
        principal sabe al instante si el cursor sigue dentro o ya ha salido;
      • siempre: si el cursor de Windows es la MANO de los enlaces.
    """

    def __init__(self, enabled):
        self.enabled = enabled and IS_WINDOWS
        self.rect, self.kind, self.rect_time = None, "", 0.0
        self.hand_cursor, self.hand_time = False, 0.0
        self.uia_ok = False
        self._running = True
        if not IS_WINDOWS:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def toggle(self):
        if IS_WINDOWS:
            self.enabled = not self.enabled
        return self.enabled

    def is_over(self, x, y):
        """¿Frenar? (el cursor está dentro de un botón detectado hace poco)."""
        if not self.enabled:
            return False
        now = time.time()
        rect = self.rect
        if rect is not None and now - self.rect_time < 0.5:
            l, t, r, b = rect
            if l <= x <= r and t <= y <= b:
                return True
        return self.hand_cursor and now - self.hand_time < 0.15

    def _run(self):
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32

        class CURSORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD),
                        ("hCursor", wintypes.HANDLE), ("ptScreenPos", wintypes.POINT)]

        user32.LoadCursorW.restype = wintypes.HANDLE
        hand = user32.LoadCursorW(None, 32649)                # IDC_HAND
        info = CURSORINFO()
        info.cbSize = ctypes.sizeof(CURSORINFO)

        uia = walker = make_point = None
        try:
            import comtypes
            import comtypes.client
            try:
                comtypes.CoInitializeEx(comtypes.COINIT_APARTMENTTHREADED)
            except OSError:
                pass
            comtypes.client.GetModule("UIAutomationCore.dll")
            from comtypes.gen import UIAutomationClient as UIA
            uia = comtypes.client.CreateObject(UIA.CUIAutomation, interface=UIA.IUIAutomation)
            walker = uia.ControlViewWalker
            point_type = getattr(UIA, "tagPOINT", wintypes.POINT)
            make_point = lambda x, y: point_type(x, y)    # noqa: E731
            self.uia_ok = True
            print("[INFO] Freno sobre botones y archivos: activo (UI Automation)")
        except ImportError:
            print("[AVISO] Freno sobre botones: solo enlaces. Para botones y archivos: "
                  "pip install comtypes")
        except Exception as exc:  # noqa: BLE001
            print(f"[AVISO] Freno sobre botones: solo enlaces ({exc})")

        def rect_of(el):
            r = el.CurrentBoundingRectangle
            return r.left, r.top, r.right, r.bottom

        period = 1.0 / FRENO_CONSULTAS_S
        while self._running:
            t0 = time.time()
            if self.enabled and user32.GetCursorInfo(ctypes.byref(info)):
                self.hand_cursor = bool(info.hCursor) and info.hCursor == hand
                self.hand_time = time.time()
                x, y = info.ptScreenPos.x, info.ptScreenPos.y
                rect = self.rect
                inside = (rect is not None and rect[0] <= x <= rect[2]
                          and rect[1] <= y <= rect[3] and time.time() - self.rect_time < 0.3)
                if uia is not None and not inside:
                    try:
                        el = uia.ElementFromPoint(make_point(x, y))
                        found = clickable_rect(el, lambda e: e.CurrentControlType, rect_of,
                                               walker.GetParentElement)
                    except Exception:  # noqa: BLE001
                        found = None                  # app ocupada / elemento ya cerrado
                    self.rect, self.kind = found if found else (None, "")
                    self.rect_time = time.time()
                elif inside:
                    self.rect_time = time.time()      # sigue dentro del mismo botón
            time.sleep(max(0.0, period - (time.time() - t0)))

    def stop(self):
        self._running = False


# =============================================================================
# 4. MODELOS DE MEDIAPIPE
# =============================================================================
def ensure_model(path, url, nombre):
    """Descarga un modelo de MediaPipe si no existe todavía."""
    if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
        return
    print(f"[INFO] Descargando modelo de {nombre} en:\n       {path}")
    tmp_path = path + ".part"
    try:
        urllib.request.urlretrieve(url, tmp_path)
        if os.path.getsize(tmp_path) < 1_000_000:
            raise IOError("el archivo descargado es demasiado pequeño (descarga incompleta)")
        os.replace(tmp_path, path)
        print("[INFO] Modelo descargado correctamente.")
    except Exception as exc:  # noqa: BLE001
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        print(f"[ERROR] No se pudo descargar el modelo: {exc}")
        print(f"        Descárgalo manualmente desde:\n        {url}")
        print(f"        y guárdalo como '{os.path.basename(path)}' junto a este script.")
        sys.exit(1)


def create_hand_landmarker():
    """Detector de manos en modo vídeo, con umbrales permisivos para no perder la mano."""
    # El modelo se lee desde Python y se le pasa a MediaPipe en memoria: MediaPipe
    # no sabe abrir rutas con tildes o 'ñ' en Windows (p. ej. "ratón virtual").
    with open(MODEL_PATH, "rb") as f:
        model_bytes = f.read()
    options = vision.HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_buffer=model_bytes),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,                    # las dos manos a la vez (der. = ratón, izq. = ventanas)
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.4,
        min_tracking_confidence=0.4,
    )
    return vision.HandLandmarker.create_from_options(options)


# =============================================================================
# 5. SPOTIFY
# =============================================================================
def open_spotify():
    """Abre la app de Spotify (o la web si no se puede / si SPOTIFY_WEB = True)."""
    system = platform.system()
    try:
        if SPOTIFY_WEB:
            raise RuntimeError("modo web")
        if system == "Windows":
            os.startfile("spotify:")                        # protocolo que registra la app
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", "Spotify"])
        else:
            subprocess.Popen(["spotify"])
        print("[INFO] Abriendo Spotify...")
    except Exception:  # noqa: BLE001
        webbrowser.open("https://open.spotify.com")
        print("[INFO] Abriendo Spotify en el navegador...")


def find_chrome():
    """Ruta de chrome.exe: registro de Windows y, si no, las carpetas habituales."""
    if not IS_WINDOWS:
        return None
    try:
        import winreg
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion"
                                          r"\App Paths\chrome.exe") as k:
                    path = winreg.QueryValue(k, None)
                    if path and os.path.exists(path):
                        return path
            except OSError:
                pass
    except ImportError:
        pass
    for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"),
                 os.environ.get("LOCALAPPDATA")):
        if base:
            path = os.path.join(base, "Google", "Chrome", "Application", "chrome.exe")
            if os.path.exists(path):
                return path
    return None


def chrome_profile_dir(display_name):
    """
    Chrome guarda cada perfil en una carpeta interna ("Default", "Profile 1"...).
    Esta función lee el archivo 'Local State' de Chrome para encontrar qué
    carpeta corresponde al perfil con ese NOMBRE (sin distinguir mayúsculas).
    Devuelve (carpeta o None, lista de nombres de perfil encontrados).
    """
    local_state = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome",
                               "User Data", "Local State")
    try:
        with open(local_state, encoding="utf-8") as f:
            cache = json.load(f).get("profile", {}).get("info_cache", {})
    except (OSError, ValueError):
        return None, []
    wanted = display_name.strip().lower()
    names = []
    for folder, info in cache.items():
        candidates = [info.get("name", ""), info.get("gaia_name", ""),
                      info.get("gaia_given_name", ""), info.get("shortcut_name", "")]
        names.append(info.get("name", folder))
        if any(c and c.strip().lower() == wanted for c in candidates):
            return folder, names
    return None, names


def open_chrome_profile():
    """Abre CHROME_URL en Chrome con el perfil CHROME_PERFIL."""
    chrome = find_chrome()
    if not chrome:
        print("[AVISO] No encuentro Chrome; abro la página en el navegador por defecto.")
        webbrowser.open(CHROME_URL)
        return
    folder, names = chrome_profile_dir(CHROME_PERFIL)
    args = [chrome]
    if folder:
        args.append(f"--profile-directory={folder}")
        print(f"[INFO] Abriendo Chrome (perfil '{CHROME_PERFIL}' = {folder})...")
    else:
        print(f"[AVISO] No encuentro el perfil '{CHROME_PERFIL}' de Chrome. "
              f"Perfiles disponibles: {', '.join(names) or 'ninguno'}. Uso el último usado.")
    args.append(CHROME_URL)
    try:
        subprocess.Popen(args)
    except OSError as exc:
        print(f"[AVISO] No se pudo abrir Chrome ({exc}); uso el navegador por defecto.")
        webbrowser.open(CHROME_URL)


def hand_side(result, i=0):
    """
    'derecha' / 'izquierda' según MediaPipe. La imagen se pasa en espejo, que
    es lo que MediaPipe espera, así que coincide con tu mano real. Si saliera
    al revés en tu cámara, pon INVERTIR_MANOS = True.
    """
    try:
        label = result.handedness[i][0].category_name
    except (AttributeError, IndexError, TypeError):
        return None
    side = {"Right": "derecha", "Left": "izquierda"}.get(label)
    if side and INVERTIR_MANOS:
        side = "izquierda" if side == "derecha" else "derecha"
    return side


def rock_action(side):
    """Qué abre el rock con esa mano: ('spotify' | 'chrome', texto)."""
    if side is None or side == ROCK_MANO_SPOTIFY:
        return "spotify", "Spotify"
    return "chrome", "Chrome: " + CHROME_PERFIL


# =============================================================================
# 6. FUNCIONES AUXILIARES DE LA MANO
# =============================================================================
def to_pixels(landmarks, width, height):
    return [(int(lm.x * width), int(lm.y * height)) for lm in landmarks]


def dist3d(lms, i, j, w, h):
    """
    Distancia 3D entre dos landmarks (x, y y PROFUNDIDAD z). Con la profundidad,
    dos dedos que parecen juntos en la imagen pero están uno delante del otro
    no cuentan como toque -> el clic es más preciso.
    """
    a, b = lms[i], lms[j]
    return math.sqrt(((a.x - b.x) * w) ** 2 + ((a.y - b.y) * h) ** 2 + ((a.z - b.z) * w) ** 2)


def finger_extended(pts, tip, pip):
    """Dedo estirado: su punta está claramente más lejos de la muñeca que su PIP."""
    return math.dist(pts[WRIST], pts[tip]) > math.dist(pts[WRIST], pts[pip]) * 1.1


def is_rock_sign(pts):
    """
    Símbolo rock 🤘: índice y meñique estirados, medio y anular doblados.
    El pulgar no se comprueba (vale fuera o dentro).
    """
    return (finger_extended(pts, INDEX_TIP, INDEX_PIP)
            and finger_extended(pts, PINKY_TIP, PINKY_PIP)
            and not finger_extended(pts, MIDDLE_TIP, MIDDLE_PIP)
            and not finger_extended(pts, RING_TIP, RING_PIP))


def is_shaka(pts):
    """
    Shaka 🤙: pulgar FUERA y meñique estirado; índice, medio y anular doblados.
    No se confunde con el rock (lleva el índice estirado) ni con el pulgar
    arriba/abajo del scroll (lleva el meñique cerrado).
    """
    return (finger_extended(pts, PINKY_TIP, PINKY_PIP)
            and not finger_extended(pts, INDEX_TIP, INDEX_PIP)
            and not finger_extended(pts, MIDDLE_TIP, MIDDLE_PIP)
            and not finger_extended(pts, RING_TIP, RING_PIP)
            and thumb_extended(pts))


def open_claude():
    """Abre Claude en el navegador predeterminado."""
    print("[INFO] Abriendo Claude...")
    webbrowser.open(CLAUDE_URL)


def is_fist(pts):
    """
    Puño ✊: ningún dedo estirado, la punta del índice metida hacia la palma
    (para no confundirlo con la pinza) y el PULGAR RECOGIDO (para no
    confundirlo con el pulgar arriba/abajo del scroll, que si no pausaría).
    """
    return (not finger_extended(pts, INDEX_TIP, INDEX_PIP)
            and not finger_extended(pts, MIDDLE_TIP, MIDDLE_PIP)
            and not finger_extended(pts, RING_TIP, RING_PIP)
            and not finger_extended(pts, PINKY_TIP, PINKY_PIP)
            and not index_not_curled(pts)
            and not thumb_extended(pts))


def index_not_curled(pts):
    """El índice no está metido en un puño (evita clics al cerrar la mano)."""
    return math.dist(pts[WRIST], pts[INDEX_TIP]) > math.dist(pts[WRIST], pts[INDEX_MCP])


def _bend_ok(a, b, c, max_deg):
    """True si en la articulación b el dedo se dobla menos de max_deg grados."""
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return False
    return (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2) >= math.cos(math.radians(max_deg))


def thumb_extended(pts):
    """
    Pulgar FUERA de la mano: punta lejos del nudillo del índice, lejos de los
    dedos doblados (en un puño el pulgar descansa sobre ellos) y bastante recto.
    """
    palm = math.dist(pts[WRIST], pts[MIDDLE_MCP]) or 1.0
    return (math.dist(pts[THUMB_TIP], pts[INDEX_MCP]) > THUMB_EXT_MIN * palm
            and math.dist(pts[THUMB_TIP], pts[MIDDLE_PIP]) > 0.5 * palm
            and _bend_ok(pts[THUMB_MCP], pts[THUMB_IP], pts[THUMB_TIP], 45))


def thumb_direction(pts):
    """
    'arriba' 👍 o 'abajo' 👎 si el pulgar está fuera, apuntando en vertical, y
    los otros cuatro dedos están cerrados. Si no, None.
    """
    if (finger_extended(pts, INDEX_TIP, INDEX_PIP) or finger_extended(pts, MIDDLE_TIP, MIDDLE_PIP)
            or finger_extended(pts, RING_TIP, RING_PIP)
            or finger_extended(pts, PINKY_TIP, PINKY_PIP)):
        return None
    if not thumb_extended(pts):
        return None
    dx = pts[THUMB_TIP][0] - pts[THUMB_MCP][0]
    dy = pts[THUMB_TIP][1] - pts[THUMB_MCP][1]
    length = math.hypot(dx, dy) or 1.0
    limit = math.cos(math.radians(THUMB_ANGLE))
    if -dy / length >= limit:
        return "arriba"
    if dy / length >= limit:
        return "abajo"
    return None


def active_box(cam_w, cam_h):
    return MARGIN_X, MARGIN_TOP, cam_w - MARGIN_X, cam_h - MARGIN_BOTTOM


def map_to_screen(x, y, cam_w, cam_h, sensibilidad):
    """Recuadro de la cámara -> pantalla, amplificado alrededor del centro."""
    x1, y1, x2, y2 = active_box(cam_w, cam_h)
    nx = ((x - x1) / (x2 - x1) - 0.5) * sensibilidad + 0.5
    ny = ((y - y1) / (y2 - y1) - 0.5) * sensibilidad + 0.5
    nx = min(max(nx, 0.0), 1.0)
    ny = min(max(ny, 0.0), 1.0)
    return SCREEN_X0 + nx * (SCREEN_W - 1), SCREEN_Y0 + ny * (SCREEN_H - 1)


def clamp_to_screen(x, y):
    """1 px dentro de los bordes para no activar el FAILSAFE en las esquinas."""
    return (int(min(max(x, SCREEN_X0 + 1), SCREEN_X0 + SCREEN_W - 2)),
            int(min(max(y, SCREEN_Y0 + 1), SCREEN_Y0 + SCREEN_H - 2)))


def adaptive_alpha(distance_px):
    """Más recorrido pendiente = menos suavizado (respuesta rápida)."""
    t = min(distance_px / VELOCIDAD_RAPIDA_PX, 1.0)
    return ALPHA_LENTO + (ALPHA_RAPIDO - ALPHA_LENTO) * t


_credit_cache = {}


def draw_credit(img):
    """Firma pequeña abajo a la derecha. Con Pillow se ven las tildes; si no, sin ellas."""
    h, w = img.shape[:2]
    text = f"{__author__}  ·  {__email__}"
    if "img" not in _credit_cache:
        _credit_cache["img"] = None
        try:
            from PIL import Image, ImageDraw, ImageFont
            font = None
            for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
                try:
                    font = ImageFont.truetype(name, 13)
                    break
                except OSError:
                    pass
            font = font or ImageFont.load_default()
            box = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), text, font=font)
            mask = Image.new("L", (box[2] - box[0] + 2, box[3] - box[1] + 4), 0)
            ImageDraw.Draw(mask).text((1 - box[0], 2 - box[1]), text, font=font, fill=255)
            _credit_cache["img"] = np.asarray(mask, dtype=np.float32) / 255.0
        except Exception:  # noqa: BLE001
            pass
    mask = _credit_cache["img"]
    if mask is not None and mask.shape[1] < w - 10 and mask.shape[0] < h:
        mh, mw = mask.shape
        y0, x0 = h - mh - 6, w - mw - 10
        roi = img[y0:y0 + mh, x0:x0 + mw].astype(np.float32)
        roi = roi * (1 - mask[..., None]) + np.array([200, 200, 200], np.float32) * mask[..., None]
        img[y0:y0 + mh, x0:x0 + mw] = roi.astype(np.uint8)
    else:
        plain = text.replace("á", "a").replace("·", "-")
        cv2.putText(img, plain, (w - 330, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (200, 200, 200), 1)


def pick_hands(result, cam_w):
    """
    Con DOS manos: la que está a la derecha de la imagen (en espejo = tu mano
    derecha) es la del ratón y la otra la de las ventanas. Se decide por la
    posición, que es más fiable que la etiqueta de MediaPipe con dos manos.
    Devuelve (índice mano ratón, índice mano ventanas o None).
    """
    hands = result.hand_landmarks
    if len(hands) < 2:
        return 0, None
    xs = [h[WRIST].x for h in hands[:2]]
    right = 0 if xs[0] >= xs[1] else 1
    mouse = right if VENTANA_MANO == "izquierda" else 1 - right
    return mouse, 1 - mouse


# =============================================================================
# 6b. INTERFAZ: columna de información a la izquierda de la cámara
# =============================================================================
PANEL_W = 236                          # ancho de la columna (px)
UI_BG = (20, 22, 26)                   # colores en RGB (Pillow)
UI_LINE = (44, 47, 54)
UI_TEXT = (236, 238, 242)
UI_MUTED = (128, 134, 146)
UI_GREEN = (61, 220, 132)
UI_ORANGE = (255, 169, 77)
UI_BLUE = (90, 170, 255)
UI_GREY = (110, 115, 125)

_ui_fonts = {}
_ui_cache = {"key": None, "img": None}


def _ui_font(size, weight="regular"):
    """Segoe UI en Windows (con tildes); si no está, Arial / DejaVu / la de Pillow."""
    k = (size, weight)
    if k not in _ui_fonts:
        from PIL import ImageFont
        names = {"regular": ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"),
                 "semi": ("seguisb.ttf", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
                 }[weight]
        font = None
        for name in names:
            try:
                font = ImageFont.truetype(name, size)
                break
            except OSError:
                pass
        _ui_fonts[k] = font or ImageFont.load_default()
    return _ui_fonts[k]


def _ascii(text):
    """Para el modo sin Pillow: quita tildes y símbolos que cv2 no sabe dibujar."""
    import unicodedata
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return t


def _render_panel(h, info):
    """Dibuja la columna (solo cuando cambia algo; se guarda en caché)."""
    W, pad, col2 = PANEL_W, 20, 128
    try:
        from PIL import Image, ImageDraw
    except Exception:  # noqa: BLE001  -> versión sencilla con cv2
        img = np.zeros((h, W, 3), np.uint8)
        img[:] = UI_BG[::-1]
        y = 30
        for label, value in (("", "AI Virtual Mouse"), ("", info["status"]),
                             ("GESTO", info["mode"]), ("ACCION", info["action"] or "-"),
                             ("MANO", info["side"]), ("VELOCIDAD", f"{info['speed']:.1f}x"),
                             ("FPS", f"{info['fps']:.0f}")):
            if label:
                cv2.putText(img, label, (pad, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                            UI_MUTED[::-1], 1, cv2.LINE_AA)
                y += 18
            cv2.putText(img, _ascii(value)[:22], (pad, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        UI_TEXT[::-1], 1, cv2.LINE_AA)
            y += 30
        return img

    im = Image.new("RGB", (W, h), UI_BG)
    d = ImageDraw.Draw(im)
    f_title, f_val = _ui_font(17, "semi"), _ui_font(15, "semi")
    f_txt, f_small, f_lbl = _ui_font(13), _ui_font(12), _ui_font(10, "semi")

    def label(x, y, text):
        d.text((x, y), text.upper(), font=f_lbl, fill=UI_MUTED)

    # Cabecera
    d.text((pad, 16), "AI Virtual Mouse", font=f_title, fill=UI_TEXT)
    color = {"activo": UI_GREEN, "pausa": UI_ORANGE}.get(info["state"], UI_GREY)
    d.ellipse((pad, 47, pad + 8, 55), fill=color)
    d.text((pad + 15, 42), info["status"], font=f_txt, fill=color)
    d.line((pad, 70, W - pad, 70), fill=UI_LINE)

    # Gesto actual
    label(pad, 84, "Gesto")
    d.text((pad, 99), info["mode"], font=f_val, fill=UI_TEXT)
    if info["hint"]:
        d.text((pad, 121), info["hint"], font=f_small, fill=UI_MUTED)
    # (la barra de progreso se dibuja aparte en y = 143, cada frame)

    # Última acción (en verde mientras está "reciente")
    label(pad, 160, "Última acción")
    d.text((pad, 175), info["action"] or "—", font=f_val,
           fill=UI_GREEN if info["action_live"] else UI_MUTED)
    d.line((pad, 206, W - pad, 206), fill=UI_LINE)

    # Mano | Freno
    label(pad, 220, "Mano")
    d.text((pad, 235), info["side"], font=f_txt, fill=UI_TEXT)
    label(col2, 220, "Freno")
    d.text((col2, 235), info["brake"], font=f_txt,
           fill=UI_BLUE if info["brake_live"] else UI_TEXT)

    # Velocidad | Rendimiento
    label(pad, 266, "Velocidad")
    d.text((pad, 281), f"{info['speed']:.1f}×", font=f_txt, fill=UI_TEXT)
    bx0, bx1 = pad, col2 - 18
    d.rounded_rectangle((bx0, 304, bx1, 307), radius=2, fill=UI_LINE)
    t = (info["speed"] - 1.0) / 2.0
    d.rounded_rectangle((bx0, 304, bx0 + max(4, int((bx1 - bx0) * t)), 307), radius=2,
                        fill=UI_TEXT)
    label(col2, 266, "FPS")
    d.text((col2, 281), f"{info['fps']:.0f}", font=f_txt,
           fill=UI_TEXT if info["fps"] >= 20 else UI_ORANGE)
    d.text((col2 + 30, 283), f"cámara {info['cam_fps']:.0f}", font=f_small, fill=UI_MUTED)

    # Exposición: valor + botones − / + / Auto (se pulsan con el ratón)
    label(pad, 318, "Exposición")
    exp = info["exposure"]
    d.text((pad, 337), "Auto" if exp is None else str(exp), font=f_txt, fill=UI_TEXT)
    for name, (x1, y1, x2, y2) in EXP_BUTTONS.items():
        off = (name == "menos" and exp is not None and exp <= EXPOSURE_MIN or
               name == "mas" and exp is not None and exp >= EXPOSURE_MAX or
               name == "auto" and exp is None)
        d.rounded_rectangle((x1, y1, x2, y2), radius=5,
                            fill=UI_BG if off else UI_LINE, outline=UI_LINE)
        text = {"menos": "−", "mas": "+", "auto": "Auto"}[name]
        f = f_small if name == "auto" else f_txt
        tb = d.textbbox((0, 0), text, font=f)
        d.text(((x1 + x2 - (tb[2] - tb[0])) / 2 - tb[0], (y1 + y2 - (tb[3] - tb[1])) / 2 - tb[1]),
               text, font=f, fill=UI_GREY if off else UI_TEXT)

    # Pie: teclas y firma
    if h >= 440:
        d.line((pad, h - 101, W - pad, h - 101), fill=UI_LINE)
        keys = (("+ −", "velocidad", "b", "freno"), ("m", "mini", "v", "cámara"))
        for i, (k1, t1, k2, t2) in enumerate(keys):
            y = h - 89 + i * 17
            d.text((pad, y), k1, font=f_small, fill=UI_TEXT)
            d.text((pad + 32, y), t1, font=f_small, fill=UI_MUTED)
            d.text((col2 + 8, y), k2, font=f_small, fill=UI_TEXT)
            d.text((col2 + 22, y), t2, font=f_small, fill=UI_MUTED)
    d.text((pad, h - 44), CREDITO, font=f_small, fill=UI_GREY)
    d.text((pad, h - 27), __email__, font=f_small, fill=UI_GREY)

    return np.asarray(im)[..., ::-1].copy()      # RGB -> BGR


PANEL_MIN_H = 480                      # la columna siempre tiene al menos este alto
EXP_BUTTONS = {"menos": (104, 333, 136, 357),      # zonas clicables (x1, y1, x2, y2)
               "mas": (142, 333, 174, 357),
               "auto": (180, 333, 216, 357)}


def panel_button_at(x, y):
    """Qué botón del panel hay en (x, y) de la ventana, o None."""
    for name, (x1, y1, x2, y2) in EXP_BUTTONS.items():
        if x1 <= x <= x2 and y1 <= y <= y2:
            return name
    return None


def draw_panel(h, info, progress=0.0, progress_color=UI_GREEN):
    """Columna izquierda (de la caché) + barra de progreso del gesto que se mantiene."""
    key = (h,) + tuple(sorted(info.items()))
    if _ui_cache["key"] != key:
        _ui_cache["key"] = key
        _ui_cache["img"] = _render_panel(h, info)
    img = _ui_cache["img"].copy()
    x0, x1, y = 20, PANEL_W - 20, 143
    cv2.rectangle(img, (x0, y), (x1, y + 3), UI_LINE[::-1], cv2.FILLED)
    if progress > 0:
        cv2.rectangle(img, (x0, y), (x0 + int((x1 - x0) * min(progress, 1.0)), y + 3),
                      progress_color[::-1], cv2.FILLED)
    cv2.line(img, (PANEL_W - 1, 0), (PANEL_W - 1, h), UI_LINE[::-1], 1)
    return img


def draw_box_corners(img, x1, y1, x2, y2, color=(235, 235, 235), length=22):
    """Zona activa: solo las 4 esquinas, finas (en vez del recuadro morado)."""
    for (cx, cy, sx, sy) in ((x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1), (x2, y2, -1, -1)):
        cv2.line(img, (cx, cy), (cx + sx * length, cy), color, 2, cv2.LINE_AA)
        cv2.line(img, (cx, cy), (cx, cy + sy * length), color, 2, cv2.LINE_AA)


def draw_hand(img, pts):
    for a, b in HAND_CONNECTIONS:
        cv2.line(img, pts[a], pts[b], (235, 235, 235), 1, cv2.LINE_AA)
    for p in pts:
        cv2.circle(img, p, 3, (132, 220, 61), cv2.FILLED, cv2.LINE_AA)


# =============================================================================
# 7. CONTROLADOR DE GESTOS
# =============================================================================
class GestureController:
    """Guarda el estado de los gestos entre frames y ejecuta las acciones."""

    def __init__(self):
        self.cur_x, self.cur_y = pyautogui.position()   # posición suavizada del cursor
        # Clic izquierdo / doble clic
        self.pinch_armed = True
        self.last_tap_time = None         # hora del último toque (para el doble clic)
        self.lock_until = 0.0             # cursor clavado hasta esta hora tras un clic
        self.lock_pos = None              # posición EXACTA del 1er clic
        self.lock_knuckle = None          # nudillo del índice en el 1er clic (cámara)
        self.open_pos, self.open_pos_t = None, 0.0     # cursor con la pinza abierta
        self.v_open_pos, self.v_open_pos_t = None, 0.0  # cursor con índice+medio separados
        # Pinza: freno al ir a clicar y 2º toque fácil
        self.pinch_hist = deque()         # (hora, valor de la pinza) de los últimos 0,2 s
        self.aim_until = 0.0              # frenar hasta esta hora (dedos cerrándose)
        self.tap_min = 1.0                # pinza mínima desde el último toque
        self.tap_peak = 0.0               # pinza máxima desde que se rearmó
        self.soft_armed = False
        # Freno sobre botones: desfase entre la mano y el cursor
        self.prev_abs, self.prev_abs_t = None, 0.0
        self.off_x = self.off_y = 0.0
        self.slow = False
        # Clic derecho
        self.right_armed = True
        self.last_right_time = 0.0
        # Scroll
        self.scroll_dir = None            # "arriba" / "abajo" mientras se mantiene
        self.scroll_since = 0.0           # desde cuándo se apunta en esa dirección
        self.scroll_last = 0.0            # hora del último envío de scroll
        self.scroll_accum = 0.0           # scroll acumulado aún no enviado (en unidades)
        # Rock -> Spotify
        self.rock_hold_start = None
        self.rock_side = None
        self.last_rock_action = {}        # acción -> hora de la última vez (cooldown)
        self.rock_progress = 0.0
        # Shaka -> Claude
        self.shaka_hold_start = None
        self.last_shaka_time = -1e9
        self.shaka_progress = 0.0
        # Selección con la pinza mantenida: idle -> active
        self.hold_start = None            # hora del toque cuya pinza sigue cerrada
        self.select_state = "idle"
        self.select_lost_since = None
        self.select_point = None          # nudillo del índice, suavizado
        self.select_progress = 0.0        # progreso de la espera de 1,5 s (0-1)
        # Pausa con el puño
        self.paused = False
        self.fist_start = None            # desde cuándo está el puño cerrado
        self.fist_armed = True            # hay que abrir la mano antes del siguiente puño
        self.pause_progress = 0.0
        # Cambio de ventana con la mano izquierda (Alt mantenido un momento)
        self.alt_down = False
        self.alt_until = 0.0
        self.last_window_time = 0.0
        self.win_pinch_armed = True
        self.win_v_armed = True
        # Texto de feedback en pantalla
        self.action_text = ""
        self.action_until = 0.0

    def show(self, text, seconds=0.6):
        self.action_text = text
        self.action_until = time.time() + seconds

    # --- mover ------------------------------------------------------------------
    def _lock_moved(self, knuckle, cam_w, sensibilidad):
        """Cuánto se ha movido la mano desde el 1er clic (px de pantalla, por el nudillo)."""
        if knuckle is None or self.lock_knuckle is None:
            return 0.0
        x1, _, x2, _ = active_box(cam_w, 1)
        return math.dist(knuckle, self.lock_knuckle) * SCREEN_W * sensibilidad / (x2 - x1)

    def double_click_pending(self, knuckle, cam_w, sensibilidad):
        """True si un toque ahora sería el 2º del doble clic (tiempo y mano quieta)."""
        return (self.last_tap_time is not None
                and time.time() - self.last_tap_time <= DOUBLE_TAP_WINDOW
                and self._lock_moved(knuckle, cam_w, sensibilidad) < TAP_LOCK_RADIUS_PX)

    def move_cursor(self, ix, iy, cam_w, cam_h, sensibilidad, knuckle=None, slow=False):
        if self.alt_down:
            return                        # con el selector de ventanas abierto, el
                                          # ratón quieto (si no, elegiría otra ventana)
        now = time.time()
        ax, ay = map_to_screen(ix, iy, cam_w, cam_h, sensibilidad)   # donde "apunta" la mano
        if self.prev_abs is None or now - self.prev_abs_t > 0.25:
            dx = dy = 0.0                 # mano recién vuelta: sin salto
        else:
            dx, dy = ax - self.prev_abs[0], ay - self.prev_abs[1]
        self.prev_abs, self.prev_abs_t = (ax, ay), now

        # Tras un clic, el cursor se queda clavado (para que el doble clic caiga en
        # el mismo sitio) salvo que muevas la mano claramente.
        if now < self.lock_until and self.lock_pos is not None:
            if self._lock_moved(knuckle, cam_w, sensibilidad) < TAP_LOCK_RADIUS_PX:
                return
            self.lock_until = 0.0         # movimiento claro -> se libera ya
            self.last_tap_time = None     # y el siguiente toque ya no es doble clic

        # Freno: encima de un botón el cursor recorre solo FRENO_FACTOR de lo que
        # se mueve la mano. Esa diferencia se guarda como desfase y, fuera de los
        # botones, se recupera poco a poco mientras la mano se mueve (nunca de golpe).
        self.slow = slow
        if slow:
            self.off_x += dx * (FRENO_FACTOR - 1.0)
            self.off_y += dy * (FRENO_FACTOR - 1.0)
        else:
            off = math.hypot(self.off_x, self.off_y)
            if off > 0:
                k = max(0.0, off - math.hypot(dx, dy) * FRENO_RECUPERACION) / off
                self.off_x *= k
                self.off_y *= k
        # Nunca empujar fuera de la pantalla (sin redondear: si no, se acumula error)
        tx = min(max(ax + self.off_x, SCREEN_X0 + 1), SCREEN_X0 + SCREEN_W - 2)
        ty = min(max(ay + self.off_y, SCREEN_Y0 + 1), SCREEN_Y0 + SCREEN_H - 2)
        self.off_x, self.off_y = tx - ax, ty - ay

        alpha = adaptive_alpha(math.dist((tx, ty), (self.cur_x, self.cur_y)))
        new_x = self.cur_x + (tx - self.cur_x) * alpha
        new_y = self.cur_y + (ty - self.cur_y) * alpha
        dead = DEAD_ZONE_PX * (0.5 if slow else 1.0)   # frenado hay menos temblor
        if abs(new_x - self.cur_x) > dead or abs(new_y - self.cur_y) > dead:
            self.cur_x, self.cur_y = new_x, new_y
            pyautogui.moveTo(*clamp_to_screen(self.cur_x, self.cur_y))

    # --- pinza: freno al ir a clicar y 2º toque fácil -------------------------------
    def update_pinch(self, ratio):
        """Se llama en cada frame con el valor de la pinza."""
        now = time.time()
        # Freno: los dedos se están CERRANDO (la pinza ha bajado en los últimos 0,2 s)
        self.pinch_hist.append((now, ratio))
        while self.pinch_hist and now - self.pinch_hist[0][0] > 0.2:
            self.pinch_hist.popleft()
        if ratio > PINCH_APPROACH:
            self.aim_until = 0.0
        elif (FRENO_AL_CLICAR
              and max(r for _, r in self.pinch_hist) - ratio >= CLIC_CERRANDO_DELTA):
            self.aim_until = now + 0.25
        # 2º toque: tras un clic, separar los dedos un poco ya vale para rearmar
        in_window = (self.last_tap_time is not None
                     and now - self.last_tap_time <= DOUBLE_TAP_WINDOW)
        if not in_window:
            self.soft_armed = False
            return
        if not self.pinch_armed:
            self.tap_min = min(self.tap_min, ratio)
            if ratio >= self.tap_min + DOUBLE_REARM_DELTA:
                self.pinch_armed = True
                self.soft_armed, self.tap_peak = True, ratio
        elif not self.soft_armed:
            self.soft_armed, self.tap_peak = True, ratio
        else:
            self.tap_peak = max(self.tap_peak, ratio)

    def aiming(self):
        """True mientras los dedos se cierran para hacer clic (-> cursor despacio)."""
        return time.time() < self.aim_until

    def is_tap(self, ratio):
        """¿Este frame es un toque? Normal: pinza cerrada. 2º toque: basta con
        volver a juntar los dedos DOUBLE_REARM_DELTA desde donde se separaron."""
        if not self.pinch_armed:
            return False
        if ratio < PINCH_THRESHOLD:
            return True
        return (self.soft_armed and ratio < PINCH_RELEASE
                and ratio <= self.tap_peak - DOUBLE_REARM_DELTA)

    def tap_done(self, ratio):
        self.pinch_armed = False
        self.tap_min, self.soft_armed = ratio, False

    # --- dónde cae el clic ---------------------------------------------------------
    def note_open(self, pinch_ratio, v_ratio):
        """Recuerda dónde estaba el cursor con los dedos todavía abiertos."""
        now = time.time()
        if pinch_ratio > PINCH_APPROACH:
            self.open_pos, self.open_pos_t = (self.cur_x, self.cur_y), now
        if v_ratio > RIGHT_APPROACH:
            self.v_open_pos, self.v_open_pos_t = (self.cur_x, self.cur_y), now

    def _rewound(self, pos, pos_t):
        """Punto del clic: el de antes de cerrar los dedos, si es reciente y cercano."""
        here = (self.cur_x, self.cur_y)
        if (pos is not None and time.time() - pos_t <= REWIND_MAX_AGE
                and math.dist(pos, here) <= REWIND_MAX_PX):
            return clamp_to_screen(*pos)
        return clamp_to_screen(*here)

    def _go(self, pos):
        self.cur_x, self.cur_y = pos
        self.prev_abs = None              # que el siguiente movimiento no dé un salto

    # --- clic izquierdo y doble clic ----------------------------------------------
    def register_tap(self, knuckle=None, cam_w=640, sensibilidad=SENSIBILIDAD):
        """
        Se llama en cada toque índice-pulgar.
          • 1er toque  -> clic INMEDIATO y el cursor se queda clavado.
          • 2º toque dentro de DOUBLE_TAP_WINDOW -> DOBLE CLIC garantizado:
              - si va dentro del tiempo de doble clic de Windows, basta otro clic
                (Windows junta los dos);
              - si va más lento, se envía un doble clic completo.
        """
        now = time.time()
        if self.last_tap_time is not None and now - self.last_tap_time < MIN_TAP_INTERVAL:
            return                                           # rebote, se ignora
        self.hold_start = now        # si la pinza sigue cerrada 1,5 s -> seleccionar

        if self.double_click_pending(knuckle, cam_w, sensibilidad) and self.lock_pos:
            # 2º toque: EXACTAMENTE en el punto del 1º, aunque la mano se haya movido
            x, y = self.lock_pos
            self._go((x, y))
            elapsed = now - self.last_tap_time
            if elapsed < OS_DOUBLE_CLICK_TIME - 0.05:
                pyautogui.click(x, y)                        # Windows lo une con el anterior
            else:
                # Esperamos a salir del tiempo de doble clic del sistema para que
                # el 1er clic anterior no se mezcle con este doble clic (máx. ~0,1 s)
                wait = OS_DOUBLE_CLICK_TIME + 0.02 - elapsed
                if wait > 0:
                    time.sleep(wait)
                pyautogui.doubleClick(x, y)
            self.last_tap_time = None
            self.lock_until = time.time() + 0.25
            self.show("Doble clic")
        else:
            # 1er toque: donde estaba el cursor ANTES de cerrar los dedos
            x, y = self._rewound(self.open_pos, self.open_pos_t)
            self._go((x, y))
            pyautogui.click(x, y)
            self.last_tap_time = now
            self.lock_until = now + DOUBLE_TAP_WINDOW
            self.lock_pos = (x, y)
            self.lock_knuckle = knuckle
            self.show("Clic", 0.4)

    # --- clic derecho -------------------------------------------------------------
    def try_right_click(self):
        now = time.time()
        if self.right_armed and now - self.last_right_time > RIGHT_COOLDOWN:
            x, y = self._rewound(self.v_open_pos, self.v_open_pos_t)
            self._go((x, y))
            pyautogui.rightClick(x, y)
            self.right_armed = False
            self.last_right_time = now
            self.show("Clic derecho")

    # --- scroll apuntando arriba / abajo ------------------------------------------
    def update_scroll(self, direction):
        """
        Scroll CONTINUO mientras el pulgar apunta arriba o abajo. Empieza tras
        SCROLL_START_DELAY y va acelerando de SCROLL_SPEED_MIN a SCROLL_SPEED_MAX.
        Devuelve el progreso del retardo inicial (0-1) para dibujarlo.
        """
        now = time.time()
        if direction != self.scroll_dir:            # nueva dirección -> reiniciar
            self.scroll_dir, self.scroll_since = direction, now
            self.scroll_last, self.scroll_accum = now, 0.0
            return 0.0

        held = now - self.scroll_since
        if held < SCROLL_START_DELAY:
            self.scroll_last = now
            return held / SCROLL_START_DELAY

        t = min((held - SCROLL_START_DELAY) / SCROLL_ACCEL_TIME, 1.0)
        speed = SCROLL_SPEED_MIN + (SCROLL_SPEED_MAX - SCROLL_SPEED_MIN) * t   # muescas/s
        dt = min(now - self.scroll_last, 0.1)       # por si se perdió la mano un momento
        self.scroll_accum += speed * SCROLL_UNIT * dt
        self.scroll_last = now

        # En Windows se pueden mandar fracciones de muesca (scroll suave);
        # en otros sistemas solo muescas enteras.
        step = 1 if IS_WINDOWS else SCROLL_UNIT
        amount = int(self.scroll_accum // step) * step
        if amount:
            self.scroll_accum -= amount
            sign = 1 if direction == "arriba" else -1
            if SCROLL_INVERTIDO:
                sign = -sign
            pyautogui.scroll(sign * amount)
        return 1.0

    def reset_scroll(self):
        self.scroll_dir = None
        self.scroll_accum = 0.0

    # --- seleccionar manteniendo la pinza ----------------------------------------------
    def update_hold(self, pinch_closed, knuckle):
        """
        Cuenta cuánto tiempo sigue cerrada la pinza DESPUÉS del clic. Al llegar
        a SELECT_HOLD_TIME empieza la selección (pulsa el botón y no lo suelta).
        Un toque normal es mucho más corto, así que el clic y el doble clic
        funcionan igual que siempre.
        """
        if self.select_state == "active":
            return
        if not pinch_closed or self.hold_start is None:
            self.hold_start = None if not pinch_closed else self.hold_start
            self.select_progress = 0.0
            return
        self.select_progress = min((time.time() - self.hold_start) / SELECT_HOLD_TIME, 1.0)
        if self.select_progress >= 1.0:
            self.cur_x, self.cur_y = pyautogui.position()
            pyautogui.mouseDown()
            self.select_state, self.select_lost_since = "active", None
            self.select_point = knuckle
            self.hold_start, self.select_progress = None, 0.0
            self.last_tap_time = None          # el siguiente toque no cuenta como doble clic
            self.show("Seleccionando", 0.8)

    def update_select(self, pinch_closed, knuckle, cam_w, cam_h, sensibilidad):
        """
        Mientras la selección está activa: la mano mueve el cursor con el botón
        pulsado. Se sigue el NUDILLO del índice (con la pinza cerrada la punta se
        mueve sola; el nudillo no) y se usa el MISMO suavizado adaptativo que el
        movimiento normal. Al abrir la pinza (o perder la mano) se suelta.
        """
        if self.select_state != "active":
            return
        now = time.time()
        if not pinch_closed or knuckle is None:
            if self.select_lost_since is None:
                self.select_lost_since = now
            if now - self.select_lost_since >= SELECT_END_GRACE:
                self.end_select()
                self.show("Selección hecha", 0.8)
            return
        self.select_lost_since = None

        x1, _, x2, _ = active_box(cam_w, cam_h)
        scale = SCREEN_W * sensibilidad / (x2 - x1)        # px de pantalla por px de cámara
        alpha = adaptive_alpha(math.dist(knuckle, self.select_point) * scale)
        sx = self.select_point[0] + (knuckle[0] - self.select_point[0]) * alpha
        sy = self.select_point[1] + (knuckle[1] - self.select_point[1]) * alpha
        dx, dy = (sx - self.select_point[0]) * scale, (sy - self.select_point[1]) * scale
        self.select_point = (sx, sy)
        if abs(dx) > DEAD_ZONE_PX or abs(dy) > DEAD_ZONE_PX:
            self.cur_x, self.cur_y = clamp_to_screen(self.cur_x + dx, self.cur_y + dy)
            pyautogui.moveTo(*clamp_to_screen(self.cur_x, self.cur_y))

    def end_select(self):
        """Suelta el botón si la selección estaba activa (nunca lo deja pulsado)."""
        if self.select_state == "active":
            pyautogui.mouseUp()
        self.select_state, self.select_progress, self.select_lost_since = "idle", 0.0, None
        self.hold_start = None

    # --- cambiar de ventana (mano izquierda) ------------------------------------------
    def switch_window(self, forward):
        """
        Siguiente (forward=True) o anterior ventana. Se deja Alt PULSADO
        WINDOW_SWITCH_HOLD segundos: si repites el gesto, avanzas/retrocedes una
        más en el selector (como al pulsar Tab varias veces con Alt apretado).
        """
        now = time.time()
        if now - self.last_window_time < WINDOW_COOLDOWN:
            return
        self.last_window_time = now
        if not self.alt_down:
            pyautogui.keyDown("alt")
            self.alt_down = True
        if forward:
            pyautogui.press("tab")
        else:
            pyautogui.keyDown("shift")
            pyautogui.press("tab")
            pyautogui.keyUp("shift")
        self.alt_until = now + WINDOW_SWITCH_HOLD
        self.show("Siguiente ventana" if forward else "Ventana anterior", 0.8)
        if WINDOW_SWITCH_HOLD <= 0:
            self.release_alt()

    def update_alt(self):
        """Suelta Alt (y se abre la ventana elegida) cuando pasa el tiempo de espera."""
        if self.alt_down and time.time() >= self.alt_until:
            self.release_alt()

    def release_alt(self):
        if self.alt_down:
            pyautogui.keyUp("alt")
            self.alt_down = False

    # --- pausa con el puño --------------------------------------------------------------
    def update_pause(self, fist):
        """
        Puño mantenido PAUSE_HOLD_TIME -> pausa (o reanuda si ya estaba pausado).
        Después hay que ABRIR la mano antes de que otro puño cuente, para que no
        se pause y reanude en bucle si mantienes el puño cerrado.
        """
        now = time.time()
        if not fist:
            self.fist_start, self.fist_armed, self.pause_progress = None, True, 0.0
            return
        if not self.fist_armed:
            return
        if self.fist_start is None:
            self.fist_start = now
        self.pause_progress = min((now - self.fist_start) / PAUSE_HOLD_TIME, 1.0)
        if self.pause_progress >= 1.0:
            self.fist_armed, self.fist_start, self.pause_progress = False, None, 0.0
            self.paused = not self.paused
            self.set_paused(self.paused)

    def set_paused(self, paused):
        """Pausa / reanuda (desde el puño o desde el icono junto al reloj)."""
        self.paused = paused
        if paused:
            self.end_select()                    # nunca dejar el botón pulsado
            self.reset_scroll()
            self.release_alt()                   # ni la tecla Alt
        self.show("Pausado" if paused else "Activado", 1.0)

    # --- símbolo rock -> Spotify ----------------------------------------------------
    def update_rock(self, rock, side=None):
        """
        Rock mantenido ROCK_HOLD_TIME segundos: mano derecha -> Spotify,
        mano izquierda -> Chrome. Si cambias de mano a mitad, se reinicia.
        """
        now = time.time()
        action, _ = rock_action(side)
        if (not rock or now - self.last_rock_action.get(action, 0.0) < SPOTIFY_COOLDOWN
                or side != self.rock_side):
            self.rock_hold_start, self.rock_progress = None, 0.0
            self.rock_side = side if rock else None
            return
        if self.rock_hold_start is None:
            self.rock_hold_start = now
        self.rock_progress = min((now - self.rock_hold_start) / ROCK_HOLD_TIME, 1.0)
        if self.rock_progress >= 1.0:
            self.last_rock_action[action] = now
            self.rock_hold_start, self.rock_progress = None, 0.0
            if action == "chrome":
                open_chrome_profile()
                self.show("Abriendo Chrome", 1.2)
            else:
                open_spotify()
                self.show("Abriendo Spotify", 1.2)


    # --- shaka -> Claude ----------------------------------------------------------
    def update_shaka(self, shaka):
        """Shaka mantenido SHAKA_HOLD_TIME segundos -> abre Claude (una vez)."""
        now = time.time()
        if not shaka or now - self.last_shaka_time < SHAKA_COOLDOWN:
            self.shaka_hold_start, self.shaka_progress = None, 0.0
            return
        if self.shaka_hold_start is None:
            self.shaka_hold_start = now
        self.shaka_progress = min((now - self.shaka_hold_start) / SHAKA_HOLD_TIME, 1.0)
        if self.shaka_progress >= 1.0:
            self.last_shaka_time = now
            self.shaka_hold_start, self.shaka_progress = None, 0.0
            open_claude()
            self.show("Abriendo Claude", 1.2)


# =============================================================================
# 8. ICONO JUNTO AL RELOJ
# =============================================================================
class TrayIcon:
    """Icono en la bandeja del sistema: Pausar / Reanudar y Salir."""

    def __init__(self, gc):
        self.ok = False
        self.request_pause = self.request_quit = False
        if not ICONO_BANDEJA:
            return
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            print("[AVISO] Icono junto al reloj desactivado: pip install pystray pillow")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"[AVISO] Icono junto al reloj desactivado: {exc}")
            return
        try:
            ico = next((p for p in (os.path.join(BUNDLE_DIR, "icono.ico"),
                                    os.path.join(SCRIPT_DIR, "icono.ico")) if os.path.exists(p)), None)
            if ico:
                image = Image.open(ico)
            else:                                   # flecha de ratón blanca sobre morado
                image = Image.new("RGBA", (64, 64), (124, 58, 237, 255))
                ImageDraw.Draw(image).polygon([(18, 10), (18, 52), (30, 40), (38, 56),
                                               (44, 53), (36, 37), (52, 37)], fill="white")

            def _set(attr):
                return lambda icon, item: setattr(self, attr, True)

            menu = pystray.Menu(
                pystray.MenuItem(f"AI Virtual Mouse v{__version__}", None, enabled=False),
                pystray.MenuItem(CREDITO, None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(lambda item: "Reanudar" if gc.paused else "Pausar",
                                 _set("request_pause"), default=True),
                pystray.MenuItem("Salir", _set("request_quit")),
            )
            self.icon = pystray.Icon("ai_virtual_mouse", image,
                                     f"AI Virtual Mouse - {CREDITO}", menu)
            self.icon.run_detached()
            self.ok = True
        except Exception as exc:  # noqa: BLE001
            print(f"[AVISO] Icono junto al reloj desactivado: {exc}")

    def stop(self):
        """Quita el icono sin bloquear la salida (máx. 1 s)."""
        if self.ok:
            th = threading.Thread(target=self._safe_stop, daemon=True)
            th.start()
            th.join(timeout=1.0)

    def _safe_stop(self):
        try:
            self.icon.stop()
        except Exception:  # noqa: BLE001
            pass


# =============================================================================
# 9. BUCLE PRINCIPAL
# =============================================================================
def main():
    print(f"[INFO] AI Virtual Mouse v{__version__} - {CREDITO} ({__email__})")
    sensibilidad = SENSIBILIDAD
    boost_windows_process()           # que no baje a 8 FPS al minimizar / cambiar de app
    mini = False                      # tecla 'm': mini-ventana siempre encima

    ensure_model(MODEL_PATH, MODEL_URL, "mano")
    landmarker = create_hand_landmarker()
    cam_index, cams, cam_names = select_camera()
    exposure = load_exposure(cam_index, cam_names)
    cap, backend, cam_info = open_best_camera(cam_index, several_cameras=len(cams) > 1,
                                              exposure=exposure)
    cam = CameraStream(cap)
    cam_fps, cam_frames_t0 = 0.0, 0
    gc = GestureController()
    tray = TrayIcon(gc)
    buttons = ClickableWatcher(FRENAR_EN_BOTONES)

    print(f"[INFO] Escritorio: {SCREEN_W}x{SCREEN_H} (desde {SCREEN_X0},{SCREEN_Y0})  |  "
          f"Doble clic del sistema: {OS_DOUBLE_CLICK_TIME:.2f} s")
    print("[INFO] Índice = mover | Toque índice+pulgar = clic (x2 = doble) | "
          "Índice+medio juntos = clic derecho | Pulgar arriba/abajo = scroll | "
          "Rock 🤘 = Spotify")
    print("[INFO] Mano IZQUIERDA: pinza = siguiente ventana | índice+medio juntos = anterior")
    print("[INFO] Se ven las DOS manos a la vez: la derecha mueve el ratón mientras la")
    print("       izquierda cambia de ventana (no hace falta quitar la derecha).")
    print("[INFO] Shaka 🤙 (pulgar + meñique) 0,5 s = abrir Claude")

    last_ts_ms = 0
    last_frame_id = -1
    lost_frames = 0
    fps, fps_count, fps_t0 = 0.0, 0, time.time()
    window = "AI Virtual Mouse  (q / ESC para salir)"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, PANEL_W + 640, 480)
    ui_clicks = []                    # botones del panel pulsados con el ratón

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            name = panel_button_at(x, y)
            if name:
                ui_clicks.append(name)

    try:
        cv2.setMouseCallback(window, on_mouse)
    except cv2.error as exc:
        print(f"[AVISO] Los botones del panel no responderán al ratón: {exc}")
    last_title_update = 0.0
    stable_side, pending_side, pending_count = None, None, 0
    view_size = None                  # tamaño de la ventana (panel + cámara)
    two_hands = was_two_hands = False
    last_action = ""

    try:
        while True:
            # --- Órdenes del icono junto al reloj ------------------------------
            if tray.request_quit:
                break
            if tray.request_pause:
                tray.request_pause = False
                gc.set_paused(not gc.paused)
            gc.update_alt()                   # suelta Alt cuando toca (cambio de ventana)

            # --- Botones del panel: exposición − / + / Auto ----------------------
            while ui_clicks:
                name = ui_clicks.pop(0)
                if mini:
                    continue
                if name == "auto":
                    new_exp = None
                else:
                    cam_val = cam.get_exposure() if exposure is None else None
                    new_exp = exposure_step(exposure, 1 if name == "mas" else -1, cam_val)
                if new_exp != exposure or name == "auto":
                    exposure = new_exp
                    cam.set_exposure(exposure)
                    save_exposure(cam_index, cam_names, exposure)
                gc.show("Exposición " + ("auto" if exposure is None else str(exposure)), 1.0)

            frame_id, frame = cam.read()
            if frame is None or frame_id == last_frame_id:
                k = cv2.waitKey(1) & 0xFF
                if k in (ord("q"), 27):
                    break
                if k == ord("e"):                    # aunque la cámara no dé imagen
                    ui_clicks.append("auto")
                continue
            last_frame_id = frame_id

            # Imágenes grandes (p. ej. 1280x720) se reducen antes de analizarlas:
            # MediaPipe trabaja internamente a baja resolución, así que no se pierde
            # precisión y se ahorra tiempo en cada paso.
            if frame.shape[1] > PROCESS_MAX_WIDTH:
                scale = PROCESS_MAX_WIDTH / frame.shape[1]
                frame = cv2.resize(frame, (PROCESS_MAX_WIDTH, int(frame.shape[0] * scale)),
                                   interpolation=cv2.INTER_AREA)
            frame = cv2.flip(frame, 1)            # efecto espejo
            cam_h, cam_w = frame.shape[:2]

            # --- Mano (en este hilo) ---------------------------------------------
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts_ms = max(int(time.monotonic() * 1000), last_ts_ms + 1)
            last_ts_ms = ts_ms
            result = landmarker.detect_for_video(mp_image, ts_ms)

            x1, y1, x2, y2 = active_box(cam_w, cam_h)
            draw_box_corners(frame, x1, y1, x2, y2)

            mode_text, mode_hint = "Sin mano", "Pon la mano dentro del recuadro"
            two_hands = False
            rock = False
            shaka = False
            side = None

            if result.hand_landmarks:
                lost_frames = 0
                mouse_i, win_i = pick_hands(result, cam_w)
                two_hands = win_i is not None
                lms = result.hand_landmarks[mouse_i]
                pts = to_pixels(lms, cam_w, cam_h)
                draw_hand(frame, pts)
                mode_text, mode_hint = "Mano detectada", ""
                knuckle = (lms[INDEX_MCP].x * cam_w, lms[INDEX_MCP].y * cam_h)

                ix, iy = pts[INDEX_TIP]
                thx, thy = pts[THUMB_TIP]
                mx, my = pts[MIDDLE_TIP]
                hand_size = dist3d(lms, WRIST, MIDDLE_MCP, cam_w, cam_h) or 1.0
                pinch_ratio = dist3d(lms, INDEX_TIP, THUMB_TIP, cam_w, cam_h) / hand_size
                v_ratio = dist3d(lms, INDEX_TIP, MIDDLE_TIP, cam_w, cam_h) / hand_size

                idx = finger_extended(pts, INDEX_TIP, INDEX_PIP)
                mid = finger_extended(pts, MIDDLE_TIP, MIDDLE_PIP)
                ring = finger_extended(pts, RING_TIP, RING_PIP)
                pinky = finger_extended(pts, PINKY_TIP, PINKY_PIP)
                pinch_closing = pinch_ratio < PINCH_RELEASE
                two_fingers = idx and mid and not ring and not pinky
                gc.note_open(pinch_ratio, v_ratio)        # para que el clic no se desplace
                gc.update_pinch(pinch_ratio)

                # Puño mantenido -> pausar / reanudar (funciona también estando pausado)
                fist = is_fist(pts)
                gc.update_pause(fist and gc.select_state != "active")

                # Selección en curso: la pinza tiene que seguir cerrada
                gc.update_select(pinch_closing, knuckle, cam_w, cam_h, sensibilidad)
                selecting = gc.select_state == "active"
                rock = is_rock_sign(pts) and not selecting and not gc.paused
                shaka = is_shaka(pts) and not selecting and not gc.paused
                # Mano estable: un cambio de mano se acepta tras SIDE_STABLE_FRAMES
                # frames seguidos (un error de 1 frame no cambia lo que hace la pinza)
                raw_side = hand_side(result, mouse_i)     # 'derecha' / 'izquierda'
                if two_hands:
                    # Con las dos manos no hay duda: esta es la del ratón
                    raw_side = "izquierda" if VENTANA_MANO == "derecha" else "derecha"
                    stable_side = None
                elif was_two_hands:
                    stable_side = None            # se fue una mano: aceptar la otra ya
                was_two_hands = two_hands
                if raw_side == stable_side or stable_side is None:
                    stable_side, pending_count = raw_side, 0
                elif raw_side == pending_side:
                    pending_count += 1
                    if pending_count >= SIDE_STABLE_FRAMES:
                        stable_side, pending_count = raw_side, 0
                else:
                    pending_side, pending_count = raw_side, 1
                side = stable_side
                window_hand = side == VENTANA_MANO
                aiming = gc.aiming() and not window_hand    # dedos cerrándose para clicar
                slow = aiming or buttons.is_over(gc.cur_x, gc.cur_y)

                # ---------- PAUSADO: no se hace nada salvo esperar otro puño ----------
                if gc.paused:
                    mode_text, mode_hint = "En pausa", "Puño 1 s para reanudar"
                    gc.reset_scroll()

                # ---------- 0) SELECCIÓN EN CURSO (pinza mantenida) -----------------
                elif selecting:
                    gc.reset_scroll()
                    mode_text, mode_hint = "Seleccionando", "Separa los dedos para soltar"
                    cv2.line(frame, (ix, iy), (thx, thy), (132, 220, 61), 3, cv2.LINE_AA)
                    cv2.circle(frame, pts[INDEX_MCP], 9, (132, 220, 61), cv2.FILLED, cv2.LINE_AA)

                # ---------- 1) SÍMBOLO ROCK -> SPOTIFY -----------------------------
                elif rock:
                    mode_text, mode_hint = "Rock", "Abrir " + rock_action(side)[1]
                    gc.reset_scroll()
                    for tip in (INDEX_TIP, PINKY_TIP):
                        cv2.circle(frame, pts[tip], 9, (132, 220, 61), cv2.FILLED, cv2.LINE_AA)

                # ---------- 1b) SHAKA -> CLAUDE ---------------------------------------
                elif shaka:
                    mode_text, mode_hint = "Shaka", "Abrir Claude"
                    gc.reset_scroll()
                    for tip in (THUMB_TIP, PINKY_TIP):
                        cv2.circle(frame, pts[tip], 9, (255, 170, 90), cv2.FILLED, cv2.LINE_AA)

                # ---------- PUÑO (aún sin pausar): no hace nada más ----------------
                elif fist:
                    mode_text, mode_hint = "Puño", "Mantén 1 s para pausar"
                    gc.reset_scroll()
                else:
                    # Pulgar arriba/abajo (solo si no es una pinza)
                    direction = None if pinch_closing else thumb_direction(pts)
                    if direction is None:
                        gc.reset_scroll()

                    # ---------- 2) PULGAR ARRIBA / ABAJO -> SCROLL -------------------
                    if direction is not None:
                        progress = gc.update_scroll(direction)
                        arrow_end = (thx, thy - 45) if direction == "arriba" else (thx, thy + 45)
                        color = (255, 200, 0) if progress >= 1.0 else (180, 180, 180)
                        cv2.arrowedLine(frame, (thx, thy), arrow_end, color, 4, tipLength=0.4)
                        mode_text = "Scroll " + direction
                        mode_hint = "" if progress >= 1.0 else "Mantén el pulgar..."
                        if progress >= 1.0:
                            gc.show("Scroll " + direction, 0.2)

                    # ---------- 3a) MANO IZQUIERDA: PINZA -> SIGUIENTE VENTANA --------
                    elif window_hand and pinch_closing:
                        mode_text, mode_hint = "Siguiente ventana", "Mano izquierda · pinza"
                        cv2.line(frame, (ix, iy), (thx, thy), (255, 200, 0), 2, cv2.LINE_AA)
                        if (gc.win_pinch_armed and pinch_ratio < PINCH_THRESHOLD
                                and index_not_curled(pts)):
                            gc.switch_window(True)
                            gc.win_pinch_armed = False
                            cv2.circle(frame, ((ix + thx) // 2, (iy + thy) // 2), 15,
                                       (255, 200, 0), cv2.FILLED)

                    # ---------- 3b) MANO IZQUIERDA: ÍNDICE+MEDIO -> VENTANA ANTERIOR ---
                    elif window_hand and two_fingers and v_ratio < RIGHT_RELEASE:
                        mode_text, mode_hint = "Ventana anterior", "Mano izquierda · índice + medio"
                        cv2.line(frame, (ix, iy), (mx, my), (255, 200, 0), 2, cv2.LINE_AA)
                        if gc.win_v_armed and v_ratio < RIGHT_THRESHOLD:
                            gc.switch_window(False)
                            gc.win_v_armed = False

                    # ---------- 3) TOQUE ÍNDICE-PULGAR -> CLIC / DOBLE CLIC -------
                    elif pinch_closing:
                        mode_text, mode_hint = "Pinza", ""
                        cv2.line(frame, (ix, iy), (thx, thy), (132, 220, 61), 2, cv2.LINE_AA)
                        if gc.is_tap(pinch_ratio) and index_not_curled(pts):
                            gc.register_tap(knuckle, cam_w, sensibilidad)
                            gc.tap_done(pinch_ratio)
                            cv2.circle(frame, ((ix + thx) // 2, (iy + thy) // 2), 15,
                                       (0, 255, 0), cv2.FILLED)
                        # ¿Sigue cerrada? -> cuenta atrás para seleccionar
                        gc.update_hold(True, knuckle)
                        if gc.select_progress > 0:
                            mode_text, mode_hint = "Pinza", "Mantén para seleccionar"

                    # ---------- 4) ÍNDICE + MEDIO -> MOVER / CLIC DERECHO ----------
                    elif two_fingers:
                        cv2.line(frame, (ix, iy), (mx, my), (255, 170, 90), 2, cv2.LINE_AA)
                        if v_ratio < RIGHT_RELEASE:
                            mode_text, mode_hint = "Clic derecho", ""
                            if v_ratio < RIGHT_THRESHOLD:
                                gc.try_right_click()
                        else:
                            mode_text = "Moviendo"
                            mode_hint = ("Más despacio para clicar" if aiming else
                                         "Más despacio sobre el botón" if slow else "")
                            gc.move_cursor(ix, iy, cam_w, cam_h, sensibilidad, knuckle, slow)

                    # ---------- 5) ÍNDICE (en cualquier dirección) -> MOVER ----------
                    elif idx:
                        mode_text = "Moviendo"
                        mode_hint = ("Más despacio para clicar" if aiming else
                                     "Más despacio sobre el botón" if slow else "")
                        gc.move_cursor(ix, iy, cam_w, cam_h, sensibilidad, knuckle, slow)
                        cv2.circle(frame, (ix, iy), 7, (255, 170, 90) if slow else (132, 220, 61),
                                   cv2.FILLED, cv2.LINE_AA)

                # Rearme de los clics (los dedos tienen que separarse)
                if pinch_ratio > PINCH_RELEASE:
                    gc.pinch_armed = True
                    if not two_hands:
                        gc.win_pinch_armed = True
                if (v_ratio > RIGHT_RELEASE or not two_fingers) and not two_hands:
                    gc.win_v_armed = True

                # ---------- MANO DE LAS VENTANAS (cuando se ven las dos) -----------
                if two_hands:
                    wl = result.hand_landmarks[win_i]
                    wp = to_pixels(wl, cam_w, cam_h)
                    draw_hand(frame, wp)
                    w_size = dist3d(wl, WRIST, MIDDLE_MCP, cam_w, cam_h) or 1.0
                    w_pinch = dist3d(wl, INDEX_TIP, THUMB_TIP, cam_w, cam_h) / w_size
                    w_v = dist3d(wl, INDEX_TIP, MIDDLE_TIP, cam_w, cam_h) / w_size
                    w_two = (finger_extended(wp, INDEX_TIP, INDEX_PIP)
                             and finger_extended(wp, MIDDLE_TIP, MIDDLE_PIP)
                             and not finger_extended(wp, RING_TIP, RING_PIP)
                             and not finger_extended(wp, PINKY_TIP, PINKY_PIP))
                    if not gc.paused and w_pinch < PINCH_RELEASE:
                        cv2.line(frame, wp[INDEX_TIP], wp[THUMB_TIP], (255, 200, 0), 2, cv2.LINE_AA)
                        if (gc.win_pinch_armed and w_pinch < PINCH_THRESHOLD
                                and index_not_curled(wp)):
                            gc.switch_window(True)
                            gc.win_pinch_armed = False
                    elif not gc.paused and w_two and w_v < RIGHT_RELEASE:
                        cv2.line(frame, wp[INDEX_TIP], wp[MIDDLE_TIP], (255, 200, 0), 2, cv2.LINE_AA)
                        if gc.win_v_armed and w_v < RIGHT_THRESHOLD:
                            gc.switch_window(False)
                            gc.win_v_armed = False
                    if w_pinch > PINCH_RELEASE:
                        gc.win_pinch_armed = True
                    if w_v > RIGHT_RELEASE or not w_two:
                        gc.win_v_armed = True
                if not pinch_closing:
                    gc.update_hold(False, knuckle)
                if v_ratio > RIGHT_RELEASE or not two_fingers:
                    gc.right_armed = True

            else:
                lost_frames += 1
                gc.update_select(False, None, cam_w, cam_h, sensibilidad)  # termina la selección
                gc.update_hold(False, None)
                if lost_frames > HAND_GRACE_FRAMES:
                    gc.reset_scroll()
                    gc.update_pause(False)
                    stable_side, pending_count = None, 0

            gc.update_rock(rock, side)
            gc.update_shaka(shaka)

            # --- FPS medio cada medio segundo -----------------------------------
            fps_count += 1
            elapsed = time.time() - fps_t0
            if elapsed >= 0.5:
                fps = fps_count / elapsed
                # FPS de la CÁMARA (frames que entrega) vs FPS del PROCESO (frames analizados)
                cam_fps = (cam.frame_id - cam_frames_t0) / elapsed
                cam_frames_t0 = cam.frame_id
                fps_count, fps_t0 = 0, time.time()

            # --- Interfaz: columna izquierda con toda la información ----------------
            if gc.paused:
                frame = (frame * 0.45).astype(np.uint8)      # vídeo oscurecido = en pausa
            if mini:
                draw_credit(frame)
                view = frame
            else:
                if IS_WINDOWS:
                    brake = ("Apagado" if not buttons.enabled else
                             "Botones" if buttons.uia_ok else "Enlaces")
                else:
                    brake = "—"
                live = time.time() < gc.action_until
                if live or gc.action_text:
                    last_action = gc.action_text
                info = {
                    "state": "pausa" if gc.paused else ("activo" if side else "sin"),
                    "status": "En pausa" if gc.paused else ("Activo" if side else "Esperando mano"),
                    "mode": mode_text, "hint": mode_hint,
                    "action": last_action, "action_live": live,
                    "side": "Las dos" if two_hands else (side.capitalize() if side else "—"),
                    "brake": brake, "brake_live": bool(gc.slow and buttons.enabled),
                    "speed": round(sensibilidad, 1),
                    "fps": round(fps), "cam_fps": round(cam_fps),
                    "exposure": exposure,
                }
                progress, pcolor = 0.0, UI_GREEN
                for p, c in ((gc.select_progress, UI_GREEN), (gc.pause_progress, UI_ORANGE),
                             (gc.rock_progress, UI_GREEN), (gc.shaka_progress, UI_BLUE)):
                    if p > progress:
                        progress, pcolor = p, c
                view_h = max(cam_h, PANEL_MIN_H)
                if cam_h < view_h:                       # cámara panorámica: rellenar abajo
                    pad_img = np.zeros((view_h - cam_h, cam_w, 3), np.uint8)
                    pad_img[:] = UI_BG[::-1]
                    frame = np.vstack([frame, pad_img])
                view = np.hstack([draw_panel(view_h, info, progress, pcolor), frame])
            if view.shape[:2] != view_size:
                view_size = view.shape[:2]
                if not mini:
                    cv2.resizeWindow(window, view_size[1], view_size[0])
            cv2.imshow(window, view)
            # Si cierras la ventana con la X, el programa termina (importante en
            # el .exe, que no tiene terminal para pararlo)
            if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                break

            # Los FPS también en el título de la ventana: así los ves en la barra
            # de tareas aunque esté minimizada.
            if time.time() - last_title_update > 1.0:
                estado = "  [PAUSADO]" if gc.paused else ""
                cv2.setWindowTitle(window, f"AI Virtual Mouse - {fps:.0f} FPS (camara {cam_fps:.0f})"
                                           f"{estado}  (q / ESC para salir)")
                last_title_update = time.time()

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key in (ord("+"), ord("=")):
                sensibilidad = min(sensibilidad + 0.1, 3.0)
            if key in (ord("-"), ord("_")):
                sensibilidad = max(sensibilidad - 0.1, 1.0)
            if key == ord("b"):
                gc.show("Freno " + ("activado" if buttons.toggle() else "apagado"), 1.0)
            if key == ord("m"):
                # Mini-ventana siempre encima: la cámara sigue a la vista mientras
                # usas otras aplicaciones (y Windows no la trata como "oculta").
                mini = not mini
                cv2.setWindowProperty(window, cv2.WND_PROP_TOPMOST, 1 if mini else 0)
                cv2.resizeWindow(window, *((240, 180) if mini else (PANEL_W + 640, 480)))
                view_size = None
                if mini:
                    cv2.moveWindow(window, PRIMARY_W - 260, PRIMARY_H - 260)
            if key == ord("c") and backend == cv2.CAP_DSHOW:
                cam.cap.set(cv2.CAP_PROP_SETTINGS, 1)   # abre el panel del driver
            if key == ord("e"):
                ui_clicks.append("auto")             # volver a exposición automática
            if key == ord("v"):
                # Cambiar de cámara: se suelta la actual (para poder verla en el
                # selector), se elige y se abre la nueva.
                gc.end_select()
                gc.reset_scroll()
                cam.stop()
                new_index, cams, cam_names = select_camera(ask=True, current=cam_index)
                exposure = load_exposure(new_index, cam_names)
                cap, backend, cam_info = open_best_camera(new_index, several_cameras=len(cams) > 1,
                                                          exposure=exposure)
                cam = CameraStream(cap)
                cam_index, last_frame_id, cam_frames_t0 = new_index, -1, 0
                gc.show("Cámara: " + camera_label(cam_index, cam_names)[:14], 1.5)
    finally:
        gc.end_select()                                  # nunca dejar el botón pulsado
        gc.release_alt()                                 # ni la tecla Alt
        cam.stop()
        buttons.stop()
        landmarker.close()
        tray.stop()
        cv2.destroyAllWindows()


def _setup_log_without_console():
    """
    El .exe no tiene terminal: los mensajes se guardan en
    'AI Virtual Mouse - registro.txt' junto al .exe para poder revisar errores.
    """
    if sys.stdout is None or sys.stderr is None:
        log = open(os.path.join(SCRIPT_DIR, "AI Virtual Mouse - registro.txt"), "w",
                   encoding="utf-8", buffering=1)
        sys.stdout = sys.stderr = log


def _show_error(message):
    """Ventana de error de Windows (en el .exe no se vería en ningún otro sitio)."""
    print(message)
    if IS_WINDOWS:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message + f"\n\n{CREDITO} - {__email__}",
                                             "AI Virtual Mouse", 0x10)
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    _setup_log_without_console()
    exit_code = 0
    try:
        main()
    except pyautogui.FailSafeException:
        pyautogui.mouseUp()
        pyautogui.keyUp("alt")
        print("[INFO] FAILSAFE activado (ratón físico en una esquina). Programa detenido.")
    except SystemExit as exc:
        if exc.code not in (None, 0):
            exit_code = exc.code if isinstance(exc.code, int) else 1
            _show_error("El programa se ha detenido. Mira el archivo\n"
                        "'AI Virtual Mouse - registro.txt' junto al programa para ver el motivo.")
    except Exception:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        exit_code = 1
        _show_error("Error inesperado:\n\n" + traceback.format_exc(limit=3))
    finally:
        # Salir SIEMPRE del todo, aunque quede algún hilo vivo (icono junto al reloj)
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:  # noqa: BLE001
            pass
        os._exit(exit_code)
