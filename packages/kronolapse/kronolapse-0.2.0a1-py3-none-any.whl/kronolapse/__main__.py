#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025-2026 Miguel Molina <mmolina.unphysics@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# GNU General Public License v3.0+
# See COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

"""**main.py - Script de ejecución principal para kronolapse**

**kronolapse** es un script de Python para ser ejecutado desde una
típica terminal de línea de comandos.

`main.py` establece la Interfaz de Línea de Comandos (CLI) con el
usuario.

Uso
---
   **kronolapse [opciones]** *cronograma*

Descripción
-----------
Este script procesa una lista de archivos en formato de imágenes para
mostrar en un monitor, de acuerdo a un cronograma de horarios y lapsos
de tiempo determinados.

La lista con archivos y su cronograma de presentación, es leído desde
un archivo CSV con un arreglo de tres campos (o columnas) estructurado
como sigue:

   Ruta archivo para presentación,Tiempo inicial,Tiempo final

Los tiempos son ingresados en formato *ISO 8601*, esto es, en formato
`YYYY-mm-dd HH:mm:ss`.

**Recomendación:** Los tiempos inicial y final del cronograma de
horarios entre archivos no deben coincidir para evitar la superposición
o solapamiento de dos imágenes simultaneas. Bug en investigación.

Opciones
--------
    -h, --help
        Muestra este mensaje de ayuda y finaliza programa.
    -V, --version
        Muestra el número de versión y finaliza programa.
    -s, --show
        Solo muestra el archivo del cronograma.

Autor
-----
Copyright (C) 2025-2026 Miguel Molina <mmolina.unphysics@gmail.com>
"""


__author__ = "Miguel Molina"
__copyright__ = "Copyright (C) 2025-2026 Miguel Molina"
__email__ = "mmolina.unphysics@gmail.com"
__license__ = "GPLv3+"
__date__ = "2026-01-22"
__version__ = "0.2.0a1"

import argparse
import kronolapse.ModKronoLapse as lCronograma


# ----
# Run!
# ----
def main() -> None:
    """**Descripción:**

    Implementación de la rutina principal de las funciones modulares de
    kronolapse con la CLI.

    Retorno
    -------
    None
        Ninguno.
    """
    # Objeto ArgumentParser para linea de comandos estandar de Phyton
    gnralOpts = argparse.ArgumentParser(
        prog="kronolapse",
        description="Displays a presentation of a set of files according to a schedule",
        formatter_class=argparse.RawTextHelpFormatter
    )
    gnralOpts._positionals.title = "Mandatory arguments"
    gnralOpts._optionals.title = "Options"
    # Argumeno obligatorio:
    gnralOpts.add_argument(
        "FILE",
        help="Schedule in CSV format",
        type=str
    )
    # Opcion: version del programa
    gnralOpts.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s " + __version__ + "\n" + __copyright__ +
        "\nLicense: " + __license__ +
        ". Visit <https://www.gnu.org/licenses/gpl-3.0.txt>."
    )
    # Opcion: mostrar cronograma
    gnralOpts.add_argument(
        "-s",
        "--show",
        action="store_true",
        help="Only shows the schedule file"
    )

    args = gnralOpts.parse_args()

    CrongrmList = lCronograma.LecturaCronograma(args.FILE)
    lCronograma.RevisionCronograma(CrongrmList)

    if args.show:
        lCronograma.MostrarCronograma(CrongrmList)
        exit()

    linea = 1
    while True:
        if lCronograma.LapsoPresentacion(CrongrmList[linea]):
            linea += 1
        if linea == len(CrongrmList):
            break


if __name__ == '__main__':
    main()
