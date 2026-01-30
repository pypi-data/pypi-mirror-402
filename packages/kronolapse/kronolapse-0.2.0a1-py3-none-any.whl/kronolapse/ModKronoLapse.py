# -*- mode: python -*-
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025-2026 Miguel Molina <mmolina.unphysics@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# GNU General Public License v3.0+
# See COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

"""Modulo con funciones para el cronograma de archivos  y su lapso de
presentación

Funciones:
    * LecturaCronograma - Lee el cronograma de archivos para su implementación
    * MostrarCronograma - Muestra por la salida estandar el cronograma
    * RevisionCronograma - Revisión de los archivos del cronograma
    * es_horario - Función booleana para determinar si el tiempo pertenece
      a un intervalo de tiempo
    * LapsoPresentacion - Función booleana para controlar la presentación
      del archivo
"""

import os
import sys
import csv
import time
import kronolapse.ModTiempo as lTiempo
import kronolapse.ModMostrarImagen as lProyectar


# -----------------------------------
# Lectura de cronograma (archivo CSV)
# -----------------------------------
def LecturaCronograma(archivo: str) -> list:
    """**Descripción:**

    Lee el cronograma de archivos para su implementación a través de un
    arreglo.

    Parámetros
    ----------
    archivo : str
        Nombre del archivo con el cronograma; archivo en formato
        CSV. El archivo CSV debe tener el siguiente formato:

        * Primera línea con encabezado del arreglo. Por ejemplo:

          ``Documento,Tiempo inicial,Tiempo final``

        * Archivos y horarios deben listarse desde la segunda línea; el
          archivo debe tener ruta absoluta o relativa; el horario en
          formato de tiempo ISO 8601.

    Retorno
    -------
    list
        Arreglo de rango 2 (matriz) con datos del cronograma.
    """
    # Verificacion existencia archivo CSV
    if os.path.isfile(archivo) is False:
        print(">> ERROR: archivo CSV del cronograma no existe.", file=sys.stderr)
        print("   Archivo: {}".format(archivo), file=sys.stderr)
        print("   Programa terminado.", file=sys.stderr)
        exit(1)
    with open(archivo, mode='r') as file:
        lista = list(csv.reader(file))
    return lista


# ------------------------------------------------
# Muestra Cronograma de archivos para presentacion
# ------------------------------------------------
def MostrarCronograma(lista: list) -> None:
    """**Descripción:**

    Muestra por la salida estandar el cronograma de archivos para su
    proyección, presentando el archivo, tiempo incial y tiempo final.

    Parámetros
    ----------
    lista : list
        Arreglo de rango 2 (matriz) con datos del cronograma.

    Retorno
    -------
    None
        Ninguno; texto mostrado en salida estandar (STDOUT).
    """
    for fila in lista:
        for col in fila:
            print("{}\t".format(col), end="")
        print("\n", end="")


# -------------------
# Revision Cronograma
# -------------------
def RevisionCronograma(lista: list) -> None:
    """
    **Descripción:**

    Revisión de los archivos del cronograma verificando su correcta
    ruta y revisión de los tiempos ingresados cumplen el formato de
    tiempo ISO 8601.

    Parámetros
    ----------
    lista : list
        Arreglo de rango 2 (matriz) con datos del cronograma.

    Retorno
    -------
    None
        Ninguno.
    """
    # Revision archivo (columna indice 0)
    for fila in range(1, len(lista)):
        if os.path.isfile(lista[fila][0]) is False:
            print(">> ERROR: archivo de Imagen no existe o ruta incorrecta.", file=sys.stderr)  # noqa: E501
            print("   Archivo: {}".format(lista[fila][0]), file=sys.stderr)
            print("   Programa terminado.", file=sys.stderr)
            exit(1)
    # Revision tiempo inicial y final (columnas indice 1 y 2)
    for fila in range(1, len(lista)):
        for col in range(1, 2):
            valor = lTiempo.CheckTextoTiempo(lista[fila][col])
            if valor is False:
                print(">> ERROR: formato de tiempo incorrecto.", file=sys.stderr)
                print("   Fila: {}, Columna: {}, Texto: {}".format(fila, col, lista[fila][col]), file=sys.stderr)  # noqa: E501
                print("   Programa terminado.", file=sys.stderr)
                exit(1)


# ----------------------------
# Control booleano del horario
# ----------------------------
def es_horario(tactual: float, tinicio: float, tfinal: float) -> bool:
    """**Descripción:**

    Función booleana para determinar SI/NO el tiempo actual se
    encuentra dentro de un intervalo de los horarios inicial y final.

    Parámetros
    ----------
    tactual : float
        Tiempo actual en formato UNIX (variable flotante).
    tinicio : float
        Tiempo inicial en formato UNIX (variable flotante).
    tfinal : float
        Tiempo final en formato UNIX (variable flotante).

    Retorno
    -------
    bool
        Objeto tipo booleano. Verdadero si ``tinicio < tactual < tfinal``.
    """
    rta = (tactual >= tinicio) and (tactual < tfinal)
    return rta


# ---------------------------------
# Lapso de presentacion del archivo
# ---------------------------------
def LapsoPresentacion(diapositiva: list) -> bool:
    """**Descripción:**

    Función booleana para controlar la presentación del archivo según
    el lapso de tiempo del cronograma.

    Parámetros
    ----------
    diapositiva : list
        Arreglo de rango 1 (vector) con datos del archivo e
        intervalo de tiempo de presentación.

    Retorno
    -------
    bool
        Objeto tipo booleano. El valor verdadero indica que el archivo
        se encuentra en modo presentación dentro del intervalo de tiempo
        especificado en el cronograma. Cuando ``tactual < tinicio``, la
        función queda en modo de espera hasta tactual sea valido dentro
        del intervalo de tiempo especificado. Para ``tactual > tfinal``,
        se asume que el archivo ya fue presentado retornando un valor
        verdadero.
    """
    archivo = diapositiva[0]
    TiempoInicio_UNIX = lTiempo.TiempoTXT2UNIX(diapositiva[1])
    TiempoFinal_UNIX = lTiempo.TiempoTXT2UNIX(diapositiva[2])
    intervalo_tiempo = TiempoFinal_UNIX - TiempoInicio_UNIX
    ctrl = True
    flag = False
    while ctrl:
        TiempoActual_UNIX = time.time()
        status = es_horario(TiempoActual_UNIX, TiempoInicio_UNIX, TiempoFinal_UNIX)
        if status:
            lProyectar.MostrarImagen(archivo, intervalo_tiempo)
            flag = True
            break
        elif TiempoActual_UNIX < TiempoInicio_UNIX:
            ctrl = True
        elif TiempoActual_UNIX >= TiempoFinal_UNIX:
            print("Archivo ya fue presentado.")
            flag = True
            break
    return flag
