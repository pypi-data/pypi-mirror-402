# -*- mode: python -*-
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025-2026 Miguel Molina <mmolina.unphysics@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# GNU General Public License v3.0+
# See COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

"""Modulo para el manejo de expresiones con tiempo y fecha

Funciones:
    * CheckTextoTiempo - Verificación del formato de tiempo
    * TiempoTXT2UNIX - Conversión formato de tiempo ISO 8601 a tiempo UNIX
"""

import re
import time
from datetime import datetime


# --------------------------------------
# Funcion para verificar texto de tiempo
# --------------------------------------
def CheckTextoTiempo(texto: str) -> bool:
    """**Descripción:**

    La expresión para fecha/tiempo debe estar redactada en formato
    similar al ISO 8601 (https://es.wikipedia.org/wiki/ISO_8601). Esto
    es, la fecha/tiempo se ingresa en formato `YYYY-mm-dd HH:mm:ss`. El
    tiempo para la hora se representa entre 00 y 23; minutos y segundos
    se representa entre 00 y 59. Está función verifica si la entrada
    cumple o no cumple con el formato requerido.

    Parámetros
    ----------
    texto : str
        Texto para la fecha/tiempo.

    Retorno
    -------
    bool
        Objeto tipo booleano; verdadero si cumple con el formato ISO 8601,
        caso contrario, falso.
    """
    patron = re.compile(r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})")
    valor = patron.match(texto)
    if valor:
        rta = True
    else:
        rta = False
    return rta


# ----------------------------------------------
# Conversion tiempo formato texto a formato UNIX
# ----------------------------------------------
def TiempoTXT2UNIX(texto: str) -> float:
    """**Descripción:**

    Convierte texto de fecha/tiempo en formato ISO 8601 a tiempo UNIX,
    esto es, a la cantidad de segundos transcurridos desde la medianoche
    UTC del 1 de enero de 1970, sin contar segundos intercalares.

    Parámetros
    ----------
    texto : str
        Texto para la fecha/tiempo.

    Retorno
    -------
    float
        Objeto tipo flotante con tiempo en formato UNIX.
    """
    formato = "%Y-%m-%d %H:%M:%S"
    # Conversion variable tipo string a objeto tipo datetime
    objeto = datetime.strptime(texto, formato)
    # Conversion objeto tipo datetime a tupla tiempo
    tupla = objeto.timetuple()
    # Conversion tupla tiempo a tiempo UNIX
    tiempoUNIX = time.mktime(tupla)
    return tiempoUNIX
