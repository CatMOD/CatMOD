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
  - Region:
"""

import math
from pathlib import Path
from typing import Optional

import numpy as np

from pysam import AlignmentFile


_BASE_INTS = {
    'A': 0,
    'C': 1,
    'G': 2,
    'T': 3,
    '-': 4,
    '^': 5}

_BASE_INDEX = {
    'A': '0',
    'C': '1',
    'G': '2',
    'T': '3'}


class Region(object):
    """The region reservoir class.

    Attributes:
        chrom (str): region chromosome id.
        start (int): region start position, 0-based.
        end (int): region end position.
        strand (str): '+' or '-'.
        info (str): information string."""

    def __init__(self,
                 chrom: str,
                 start: int,
                 end: int,
                 strand: str = '+',
                 info: str = '',
                 offset: int = 0):
        """Initialize Region.

        Args:
            chrom (str): region chromosome id.
            start (int): region start position, 0-based.
            end (int): region end position.
            strand (str): '+' or '-', default '+'.
            info (str): information string, default ''.
            offset (int): offset, default 0.
        """
        self.chrom = chrom
        if start <= end:
            self.start = start
            self.end = end
        else:
            raise ValueError(
                f'Start position {start} is larger than end position {end}.')
        if strand in ('+', '-'):
            self.strand = strand
        else:
            raise ValueError("Region strand should be '+' or '-'.")
        self.info = info
        self.offset = offset
        super().__init__()

    def __eq__(self, other):
        return self.chrom == other.chrom and self.strand == other.strand \
            and self.start == other.start and self.end == other.end

    def __str__(self):
        return f'{self.chrom}_{self.strand}_{self.start}-{self.end}'

    def copy(self):
        return Region(self.chrom, self.start, self.end,
                      self.strand, self.info, self.offset)

    def resize(self, window: int, limit: Optional[int] = None):
        """Resize the region."""
        if window > self.end - self.start:
            flank_size = (window - (self.end - self.start)) // 2
            if self.start - flank_size - self.offset <= 0:
                self.start = 0
                self.end = window
            elif limit and self.end + flank_size + 1 - self.offset >= limit:
                self.start = limit - window
                self.end = limit
            elif (window - (self.end - self.start)) % 2 == 0:
                self.start = self.start - flank_size
                self.end = self.end + flank_size
            elif self.offset:
                self.start = self.start - flank_size - 1
                self.end = self.end + flank_size
                self.offset = 0
            else:
                self.start = self.start - flank_size
                self.end = self.end + flank_size + 1
                self.offset = 1
        elif window < self.end - self.start:
            mid = (self.start + self.end - self.offset) // 2
            self.start = mid
            self.end = mid + 1
            if (self.end - self.start - self.offset) % 2 == 0:
                self.offset = 1
            else:
                self.offset = 0
            self.resize(window, limit)


def get_region_alignment(region_args: tuple[Region, str, str, int, str, bool]):
    """Get region alignment."""
    (region, region_string, alignment_file,
        ali_window, output_dir, overwrite) = region_args
    if not overwrite:
        region_done = Path(f'{output_dir}/{region_string}.ali.done')
        if region_done.is_file():
            return None
    else:
        region_done = Path(f'{output_dir}/{region_string}.ali.done')
    reads_id_list, reads_alignment, reads_quality = [], [], []
    sam_query_reader = AlignmentFile(alignment_file, 'rb')
    for read in sam_query_reader.fetch(region.chrom, region.start, region.end):
        read_features_dict = get_read_alignment(read, region, ali_window)
        if read_features_dict:
            # reads_id_list.append(read_features_dict['read_id'])
            reads_alignment.append(read_features_dict['alignment'])
            reads_quality.append(read_features_dict['quality'])
    sam_query_reader.close()
    # np.save(f'{output_dir}/{region_string}.reads_id.npy', reads_id_list)
    np.save(f'{output_dir}/{region_string}.reads_alignment.npy',
            np.array(reads_alignment, dtype=np.int64))
    np.save(f'{output_dir}/{region_string}.reads_quality.npy',
            np.array(reads_quality, dtype=np.float32))
    region_done.touch()


def get_read_alignment(read, region: Region, ali_window: int):
    read_strand = '-' if read.is_reverse else '+'
    if read_strand != region.strand:
        return {}
    range_one_hot = np.zeros((ali_window, 6), dtype=np.int64)
    range_quality = np.zeros(ali_window, dtype=np.float32)
    in_range, insert_seq_list, insert_qual_list = False, [], []
    for read_index, ref_index in read.get_aligned_pairs():
        if ref_index == region.start:
            in_range = True
        elif ref_index:
            if ref_index >= region.end:
                break
        if in_range:
            if read_index:
                if ref_index:
                    # match encoding
                    if insert_seq_list:
                        if region.strand == '+':
                            range_one_hot[ref_index-region.start-1, 5] = \
                                insert_seq_index(insert_seq_list)
                            range_quality[ref_index-region.start-1] = \
                                insert_requality(
                                    [range_quality[ref_index-region.start-1]] +
                                    insert_qual_list)
                        else:
                            range_one_hot[ref_index-region.start, 5] = \
                                insert_seq_index(insert_seq_list)
                            range_one_hot[
                                ref_index-region.start,
                                _BASE_INTS[read.query_sequence[
                                    read_index]]] = 1
                            range_quality[ref_index-region.start] = \
                                insert_requality(insert_qual_list + [
                                    read.query_qualities[read_index]])
                        insert_seq_list, insert_qual_list = [], []
                    else:
                        range_one_hot[ref_index-region.start,
                                      _BASE_INTS[read.query_sequence[
                                          read_index]]] = 1
                        range_quality[ref_index-region.start] = \
                            read.query_qualities[read_index]
                else:
                    # insertion encoding
                    if insert_seq_list and insert_qual_list:
                        insert_seq_list.append(read.query_sequence[read_index])
                        insert_qual_list.append(
                            read.query_qualities[read_index])
                    else:
                        insert_seq_list = [read.query_sequence[read_index]]
                        insert_qual_list = [read.query_qualities[read_index]]
            elif ref_index:
                # deletion encoding
                if insert_seq_list:
                    if region.strand == '+':
                        range_one_hot[ref_index-region.start-1, 5] = \
                            insert_seq_index(insert_seq_list)
                        range_quality[ref_index-region.start-1] = \
                            insert_requality([range_quality[
                                ref_index-region.start-1]]+insert_qual_list)
                    else:
                        range_one_hot[ref_index-region.start, 5] = \
                            insert_seq_index(insert_seq_list)
                        range_one_hot[ref_index-region.start, 4] = 1
                    insert_seq_list, insert_qual_list = [], []
                else:
                    range_one_hot[ref_index-region.start, 4] = 1
    if range_one_hot.any():
        return {'read_id': read.query_name,
                'alignment': range_one_hot,
                'quality': range_quality}
    else:
        return {}


def insert_requality(insert_qual_list: list):
    iq = 1
    for q in insert_qual_list:
        iq *= 1 - 10 ** (-q / 10)
    return -10 * math.log(1 - iq, 10)


def insert_seq_index(insert_seq_list: list):
    return min(
        9223372036854775807,
        int('1' + ''.join([_BASE_INDEX[base] for base in insert_seq_list]), 4))
