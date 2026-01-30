# -*- mode: python -*-
# -*- coding: utf-8 -*-
#
# test_module_kronolapse.py
#
# This test verifies the functionality of the main features of the
# Kronolapse module.

import tests.ModGenFiles as lFiles
import kronolapse.ModKronoLapse as lCronograma


# Read a schedule file
def test_read_schedule() -> None:
    FILE = "schedule_test.csv"
    lFiles.gen_all_files(FILE)
    ScheduleTest = lCronograma.LecturaCronograma(FILE)
    lCronograma.RevisionCronograma(ScheduleTest)
    numfiles = len(ScheduleTest)
    assert numfiles - 1 == 3, "The schedule should have 3 files"


# Show a schedule file
def test_show_schedule() -> None:
    FILE = "schedule_test.csv"
    lFiles.gen_all_files(FILE)
    ScheduleTest = lCronograma.LecturaCronograma(FILE)
    lCronograma.RevisionCronograma(ScheduleTest)
    status = False
    linea = 1
    while True:
        if lCronograma.LapsoPresentacion(ScheduleTest[linea]):
            linea += 1
        if linea == len(ScheduleTest):
            status = True
            break
    assert status is True, "The schedule was not displayed correctly"
