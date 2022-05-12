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
  - FastaReader:
"""

from pathlib import Path

import numpy as np

from pysam import faidx, FastaFile

from CatMOD.region import Region
from CatMOD.sys_output import Output


_COMP_BASE = {
    'A': 'T',
    'C': 'G',
    'G': 'C',
    'T': 'A',
    'M': 'K',
    'R': 'Y',
    'W': 'S',
    'S': 'W',
    'Y': 'R',
    'K': 'M',
    'V': 'B',
    'H': 'D',
    'D': 'H',
    'B': 'V',
    'N': 'N'}

_BASE_ONEHOT = {
    'A': [1., 0., 0., 0.],
    'C': [0., 1., 0., 0.],
    'G': [0., 0., 1., 0.],
    'T': [0., 0., 0., 1.],
    'M': [0.5, 0.5, 0., 0.],
    'R': [0.5, 0., 0.5, 0.],
    'W': [0.5, 0., 0., 0.5],
    'S': [0., 0.5, 0.5, 0.],
    'Y': [0., 0.5, 0., 0.5],
    'K': [0., 0., 0.5, 0.5],
    'V': [1/3, 1/3, 1/3, 0.],
    'H': [1/3, 1/3, 0., 1/3],
    'D': [1/3, 0., 1/3, 1/3],
    'B': [0., 1/3, 1/3, 1/3],
    'N': [0.25, 0.25, 0.25, 0.25]}
_BASE_ONEHOT_REV = {
    'T': [1., 0., 0., 0.],
    'G': [0., 1., 0., 0.],
    'C': [0., 0., 1., 0.],
    'A': [0., 0., 0., 1.],
    'K': [0.5, 0.5, 0., 0.],
    'Y': [0.5, 0., 0.5, 0.],
    'S': [0.5, 0., 0., 0.5],
    'W': [0., 0.5, 0.5, 0.],
    'R': [0., 0.5, 0., 0.5],
    'M': [0., 0., 0.5, 0.5],
    'B': [1/3, 1/3, 1/3, 0.],
    'D': [1/3, 1/3, 0., 1/3],
    'H': [1/3, 0., 1/3, 1/3],
    'V': [0., 1/3, 1/3, 1/3],
    'N': [0.25, 0.25, 0.25, 0.25]}


class FastaReader(object):

    def __init__(self, fasta_file: str):
        fai_path = Path(fasta_file + '.fai')
        if not fai_path.is_file():
            self.output = Output()
            self.output.warning(f'{fasta_file} lacks .fai index.')
            self.output.info(f'Attempting to create {fasta_file}.fai index.')
            faidx(fasta_file)
        self.fasta_file = FastaFile(fasta_file)

    def fetch(self, chrom: str, start: int, end: int, strand: str = '+',
              return_array: bool = False):
        if return_array:
            if strand == '+':
                return seq2array(
                    self.fasta_file.fetch(chrom, start, end).upper())
            elif strand == '-':
                return seq2array(
                    self.fasta_file.fetch(chrom, start, end).upper(), True)
            else:
                raise ValueError(f'Invalid strand: {strand}')
        else:
            if strand == '+':
                return self.fasta_file.fetch(chrom, start, end).upper()
            elif strand == '-':
                return ''.join([
                    _COMP_BASE[b] for b in
                    self.fasta_file.fetch(chrom, start, end).upper()[::-1]])
            raise ValueError(f'Invalid strand: {strand}')

    def fetch_region(self, region: Region, return_array: bool = False):
        return self.fetch(
            region.chrom, region.start, region.end,
            region.strand, return_array)


def seq2array(sequence: str, if_reverse: bool = False):
    if if_reverse:
        return np.array([_BASE_ONEHOT_REV[b] for b in sequence[::-1]],
                        dtype=np.float32)
    else:
        return np.array([_BASE_ONEHOT[b] for b in sequence], dtype=np.float32)
