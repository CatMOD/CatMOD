# -*- coding: utf-8 -*-
# Copyright 2022 Shang Xie.
# All rights reserved.
#
# This file is part of the CatMOD distribution and
# governed by your choice of the "CatMOD License Agreement"
# or the "GNU General Public License v3.0".
# Please see the LICENSE file that should
# have been included as part of this package.
""".

What's here:

.
-------------------------------------------

Classes:
  - BedReader:
"""

from CatMOD.region import Region


class BedReader(object):

    def __init__(self, bed_file: str, use_memory: bool = False):
        self.bed_file = bed_file
        self.use_memory = use_memory

    def read_bed(self):
        with open(self.bed_file, 'r') as open_bed:
            if self.use_memory:
                for eachline in open_bed.readlines():
                    if eachline[0] != '#':
                        spline = eachline.strip().split('\t')
                        yield Region(spline[0], int(spline[1]), int(spline[2]),
                                     spline[5], spline[3]+'\t'+spline[4])
            else:
                for eachline in open_bed:
                    if eachline[0] != '#':
                        spline = eachline.strip().split('\t')
                        yield Region(spline[0], int(spline[1]), int(spline[2]),
                                     spline[5], spline[3]+'\t'+spline[4])
