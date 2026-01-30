# -*- mode: python -*-
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025-2026 Miguel Molina <mmolina.unphysics@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# GNU General Public License v3.0+
# See COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

"""ModGenFiles.py - Modules for creating images

This module generates three images and a schedule file for its
presentation. Requires PIL package.
"""

import os
import math
from PIL import Image
from datetime import datetime, timedelta


# Transform function
def fTrans(x: int, a: int) -> int:
    if x < a:
        y = x - a
    else:
        y = x - a + 1
    return y


# Color spectrum palette
def ColorSpectrum(z: float) -> list:
    # Red value
    if 0.0 <= z < 0.167:
        R = 1
    elif 0.167 <= z < 0.333:
        R = -6*z + 2
    elif 0.333 <= z < 0.667:
        R = 0
    elif 0.667 <= z < 0.833:
        R = 6*z - 4
    else:  # 0.833 <= z <= 1
        R = 1
    # Green value
    if 0.000 <= z < 0.200:
        G = 5*z
    elif 0.200 <= z < 0.500:
        G = 1
    elif 0.500 <= z < 0.700:
        G = -5*z + 3.5
    else:  # 0.700 <= z <= 1
        G = 0
    # Blue value
    if 0.000 <= z < 0.300:
        B = 0
    elif 0.300 <= z < 0.500:
        B = 5*z - 1.5
    elif 0.500 <= z < 0.800:
        B = 1
    else:  # 0.800 <= z <= 1
        B = -4*z + 4.2
    R = int(255 * R)
    G = int(255 * G)
    B = int(255 * B)
    return [R, G, B]


# Convert PPM to JPG; delete PPM
def imgPPM2JPEG(infile: str) -> None:
    baseimg = os.path.splitext(infile)[0]
    inputimg = baseimg + ".ppm"
    outputimg = baseimg + ".jpg"
    try:
        with Image.open(inputimg) as im:
            im.save(outputimg)
    except OSError:
        print("cannot convert", inputimg)
    try:
        os.remove(inputimg)
    except FileNotFoundError:
        print("File {} was not found.".format(inputimg))
    except Exception as e:
        print("An error occurred: {}".format(e))


# Generate an image blue and red squares
def gen_image_RGBSquare(imgname: str, sizex: int, sizey: int) -> None:
    imgppm = imgname + ".ppm"
    halfsizex = sizex//2
    halfsizey = sizey//2
    rojo = (255, 0, 0)
    azul = (0, 0, 255)
    with open(imgppm, "w") as imgfile:
        imgfile.write("P3\n")
        imgfile.write("{} {}\n".format(sizex, sizey))
        imgfile.write("255\n")
        for iy in range(sizey):
            for ix in range(sizex):
                x = fTrans(ix, halfsizex)
                y = fTrans(iy, halfsizey)
                fxy = x*y
                if fxy > 0:
                    color = rojo
                else:
                    color = azul
                imgfile.write("{}\n".format(" ".join(map(str, color))))
    imgfile.close()
    imgPPM2JPEG(imgname)


# Generate an image concentric rings
def gen_image_Rings(imgname: str, sizex: int, sizey: int, radius: int) -> None:
    imgppm = imgname + ".ppm"
    halfsizex = sizex//2
    halfsizey = sizey//2
    magenta = (255, 0, 255)
    amarillo = (255, 255, 0)
    negro = (0, 0, 0)
    # Background image
    matrix = []
    for iy in range(sizey):
        row = []
        for ix in range(sizex):
            row.append(" ".join(map(str, magenta)))
        matrix.append(row)
    # Concentric rings
    Deltar = radius/10
    LF = 8
    for iy in range(sizey):
        for ix in range(sizex):
            r = math.sqrt((ix - halfsizex)**2 + (iy - halfsizey)**2)
            if r <= radius:
                for il in range(0, LF+1, 2):
                    if (il*Deltar <= r) and (r < (il+1)*Deltar):
                        matrix[iy][ix] = " ".join(map(str, amarillo))
                    elif ((il+1)*Deltar <= r) and (r < (il+2)*Deltar):
                        matrix[iy][ix] = " ".join(map(str, negro))
    with open(imgppm, "w") as imgfile:
        imgfile.write("P3\n")
        imgfile.write("{} {}\n".format(sizex, sizey))
        imgfile.write("255\n")
        for iy in range(sizey):
            for ix in range(sizex):
                imgfile.write("{}\n".format(matrix[iy][ix]))
    imgfile.close()
    imgPPM2JPEG(imgname)


# Generate a density plot for gaussian function two-dimensional
def gen_image_fgauss(imgname: str, sizex: int, sizey: int) -> None:
    imgppm = imgname + ".ppm"
    mu_x = sizex/2
    mu_y = sizey/2
    sigma_x = 300.0
    sigma_y = 200.0
    with open(imgppm, "w") as imgfile:
        imgfile.write("P3\n")
        imgfile.write("{} {}\n".format(sizex, sizey))
        imgfile.write("255\n")
        for iy in range(sizey):
            for ix in range(sizex):
                Zx = (ix - mu_x)/sigma_x
                Zy = (iy - mu_y)/sigma_y
                fz = math.exp(-0.5*(Zx**2 + Zy**2))
                color = ColorSpectrum(fz)
                imgfile.write("{} {} {}\n".format(color[0], color[1], color[2]))
    imgfile.close()
    imgPPM2JPEG(imgname)


# Generate a set images
def gen_images() -> None:
    gen_image_RGBSquare("RGBSquare", 1024, 768)  # Resolution XGA (4:3)
    gen_image_Rings("Rings", 1366, 768, 360)  # Resolution WXGA (16:9)
    gen_image_fgauss("fGauss", 1280, 800)  # Resolution WXGA (16:10)


# Generate a schedule file
def gen_schedule(outfile: str, lstimgs: list) -> None:
    duration = timedelta(seconds=5)
    t_now = datetime.now()
    print("Current time: {}".format(t_now.strftime("%Y-%m-%d %H:%M:%S")))
    t_ini = t_now + timedelta(seconds=15)
    print("Starting test in 15 seconds ...")
    with open(outfile, mode='w') as cvsfile:
        cvsfile.write("Document,Time initial,Time end\n")
        for imgfile in lstimgs:
            t_fin = t_ini + duration
            if os.path.exists(imgfile):
                filepath = os.path.abspath(imgfile)
                cvsfile.write("{},{},{}\n".format(filepath,
                                                  t_ini.strftime("%Y-%m-%d %H:%M:%S"),
                                                  t_fin.strftime("%Y-%m-%d %H:%M:%S"))
                              )
                t_ini = t_fin + timedelta(seconds=1)
            else:
                print("The image file {} does not exist.".format(imgfile))
    cvsfile.close()


# Generate all set files
def gen_all_files(outfile: str):
    names = ["RGBSquare", "Rings", "fGauss"]
    imgext = ".jpg"
    images = [i + imgext for i in names]
    for imgfile in images:
        if not os.path.exists(imgfile):
            gen_images()
            break
    if not os.path.exists(outfile):
        gen_schedule(outfile, images)
