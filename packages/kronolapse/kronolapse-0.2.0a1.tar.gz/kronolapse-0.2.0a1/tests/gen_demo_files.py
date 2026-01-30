#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025-2026 Miguel Molina <mmolina.unphysics@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# GNU General Public License v3.0+
# See COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

"""gen_demo_files.py - Creates images and schedule for a demo

This script creates images and schedule for a simple demonstration of
kronolapse.

Use:
   python3 tests/gen_demo_files.py
"""

import os
import sys
import ModGenFiles as lFiles

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(script_dir, '..')
sys.path.append(parent_dir)


# Create images and schedule
def generate_demo_files() -> None:
    FILE = "schedule_test.csv"
    lFiles.gen_all_files(FILE)


# Run function
generate_demo_files()
