# -*- mode: python -*-
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025-2026 Miguel Molina <mmolina.unphysics@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# GNU General Public License v3.0+
# See COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

"""Modulo para proyectar una imagen por un periodo de tiempo

Funciones:
    * MostrarImagen - Presenta la imagen del archivo para un periodo de tiempo

    Tomado y modificado desde ``ronekko/opencv_imshow_fullscreen.py``
    Info: https://gist.github.com/ronekko/dc3747211543165108b11073f929b85e
"""

import os
import platform
import screeninfo
import cv2


# ****************************************************************************
# Bug: En Linux, ajustar la salida de pantalla segun el entorno de escritorio.
# ****************************************************************************
os_name = platform.system()
if os_name == "Linux":
    if os.environ["XDG_SESSION_TYPE"] == "wayland":
        os.environ["QT_QPA_PLATFORM"] = "xcb"


# ---------------------------------------
# Mostrar imagen por un periodo de tiempo
# ---------------------------------------
def MostrarImagen(archivo: str, periodot: float, verbose: int = 0) -> None:
    """**Descripción:**

    Presenta la imagen del archivo en el monitor del PC para un
    periodo de tiempo.

    Parámetros
    ----------
    archivo : str
        Nombre del archivo para presentar.
    periodot : float
        Intervalo de tiempo de la presentación.
    verbose : int, opcional
        Bandera de control para mostrar información de la
        pantalla. Por defecto, no muestra información.

    Retorno
    -------
    None
        Ninguno.
    """
    # Dimensiones de la pantalla
    screen = screeninfo.get_monitors()[0]
    # Mostrar informacion de la pantalla
    if verbose == 1:
        for m in screeninfo.get_monitors():
            print(str(m))
    # Cargar imagen
    imagen = cv2.imread(archivo)
    # Titulo ventana
    window_name = 'Proyector'
    # Crear la ventana con dimensiones ajustables
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.moveWindow(window_name, screen.x - 1, screen.y - 1)
    # Ajustar la ventana apropidamente a pantalla completa
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    # Mostrar la imagen
    cv2.imshow(window_name, imagen)
    # Imagen mostrada en modo espera hasta presionar la tecla 'q' para romper el bucle
    print("Presione 'q' para terminar.")
    # Periodo de tiempo en milisegundos
    periodo_int = int(periodot*1000)
    while True:
        key = cv2.waitKey(periodo_int)
        if key == 113:
            break
        elif key == -1:
            break
    # Destruir todas las ventanas OpenCV
    cv2.destroyAllWindows()
