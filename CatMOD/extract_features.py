# -*- coding: utf-8 -*-
# Copyright 2022 Shang Xie.
# All rights reserved.
#
# This file is part of the CatMOD distribution and
# governed by your choice of the "CatMOD License Agreement"
# or the "GNU General Public License v3.0".
# Please see the LICENSE file that should
# have been included as part of this package.
"""Represent a collect flnc information.

What's here:

Preprocess positive and negative data sets.
-------------------------------------------

Classes:
  - ExtractFeatures:
"""

from logging import getLogger
from pathlib import Path
from multiprocessing import cpu_count, Pool

import numpy as np

from rich.progress import Progress

from CatMOD.reader.bam import check_index
from CatMOD.reader.bed import BedReader
from CatMOD.reader.fasta import FastaReader
from CatMOD.region import get_region_alignment
from CatMOD.sys_output import Output

logger = getLogger(__name__)  # pylint: disable=invalid-name


class ExtractFeatures(object):
    """The extract featres process.

    Attributes:
      - args: Arguments.
      - output: Output info, warning and error.
    """

    def __init__(self, arguments):
        """Initialize ExtractFeatures."""
        self.args = arguments
        self.output = Output()
        self.output.info(
            f'Initializing {self.__class__.__name__}: (args: {arguments}.')
        logger.debug(
            f'Initializing {self.__class__.__name__}: (args: {arguments}.')
        self.threads = self.args.threads if self.args.threads else cpu_count()

    def check_directory(self):
        """Check output positive and negative directory."""
        self.output.info('Checking output directory.')
        self.output_str = self.args.output
        self.output_path = Path(self.output_str)
        if not self.output_path.is_dir():
            self.output.info('Creating output directory.')
            self.output_path.mkdir()

    def extract_features(self):
        self.extract_sequence()
        self.extract_alignment()
        self.extract_current()

    def extract_sequence(self):
        self.output.info('Reading bed file and extracting sequence features.')
        bed_reader = BedReader(self.args.bed)
        fasta_reader = FastaReader(self.args.reference)
        self.chr_length = {}
        with open(self.args.reference + '.fai', 'r') as open_fai:
            for eachline in open_fai.readlines():
                spline = eachline.strip().split()
                self.chr_length.update({spline[0]: int(spline[1])})
        self.region_list = []
        self.region_str_set = set()
        bed_regions = len(open(self.args.bed).readlines())
        with Progress() as progress:
            task = progress.add_task(
                f'[green]INFO    [cyan]Reading {bed_regions} bed lines...',
                total=bed_regions)
            for each_region in bed_reader.read_bed():
                self.region_list.append(each_region.copy())
                region_string = str(each_region)
                self.region_str_set.add(region_string)
                each_region.resize(self.args.seq_window,
                                   self.chr_length.get(each_region.chrom, None))
                if self.args.overwrite:
                    np.save(f'{self.output_str}/{region_string}.ref_seq.npy',
                            fasta_reader.fetch_region(each_region, True))
                else:
                    ref_seq_path = Path(
                        f'{self.output_str}/{region_string}.ref_seq.npy')
                    if not ref_seq_path.is_file():
                        np.save(f'{self.output_str}/{region_string}.ref_seq.npy',
                                fasta_reader.fetch_region(each_region, True))
                progress.advance(task)
        fasta_reader.fasta_file.close()
        self.output.info('Completed extracting sequence features.')

    def extract_alignment(self):
        threads = min(self.threads, len(self.region_list))
        self.output.info(
            f'Using {threads} threads to extract '
            'alignment & quality features.')
        indexed_bam = check_index(self.args.align)
        get_region_alignment_args_list = []
        for each_region in self.region_list:
            ali_region = each_region.copy()
            ali_region.resize(
                self.args.ali_window,
                self.chr_length.get(each_region.chrom, None))
            get_region_alignment_args_list.append((
                ali_region, str(each_region), indexed_bam,
                self.args.ali_window, self.output_str,
                self.args.overwrite))
        with Pool(threads) as pool:
            _ = pool.map(get_region_alignment, get_region_alignment_args_list)
        self.output.info('Completed extracting alignment & quality features.')

    def extract_current(self):
        self.output.info('Reading ONT current files.')
        region_info_dict = {}
        site_str_set = set()
        current_files = len(open(self.args.current).readlines())
        with Progress() as progress:
            task = progress.add_task(
                f'[green]INFO    [cyan]Reading {current_files} ONT current files...',
                total=current_files)
            with open(self.args.current, 'r') as open_list:
                for eachlist in open_list.readlines():
                    with open(eachlist.strip(), 'r') as open_current:
                        for eachline in open_current.readlines():
                            spline = eachline.strip().split()
                            site_string = (spline[0] + '_' + spline[5] + '_' +
                                        str(int(spline[1]) + 2) + '-' +
                                        str(int(spline[2]) - 2))
                            if site_string in self.region_str_set:
                                # region_info_dict.setdefault(
                                #     site_string, {}).setdefault(
                                #         'reads_id', []).append(
                                #             eachlist.strip().split(
                                #                 '/')[-1].split('.')[0])
                                region_info_dict.setdefault(
                                    site_string, {}).setdefault(
                                        'reads_norm_mean', []).append(
                                            [float(nm) for nm in
                                            spline[6].split(',')])
                                region_info_dict.setdefault(
                                    site_string, {}).setdefault(
                                        'reads_norm_stdev', []).append(
                                            [float(ns) for ns in
                                            spline[7].split(',')])
                                region_info_dict.setdefault(
                                    site_string, {}).setdefault(
                                        'reads_current', []).append(
                                            [float(cs) for cs
                                            in spline[8].split(',')])
                                site_str_set.add(site_string)
                    progress.advance(task)
        with Progress() as progress:
            task = progress.add_task(
                f'[green]INFO    [cyan]Saving {len(site_str_set)} ONT current features...',
                total=len(site_str_set))
            for region_string in site_str_set:
                region_info = region_info_dict[region_string]
                # np.save(f'{self.output_str}/{region_string}.reads_id.cur.npy',
                #         region_info['reads_id'])
                np.save(f'{self.output_str}/{region_string}.reads_norm_mean.npy',
                        region_info['reads_norm_mean'])
                np.save(f'{self.output_str}/{region_string}.reads_norm_stdev.npy',
                        region_info['reads_norm_stdev'])
                np.save(f'{self.output_str}/{region_string}.reads_current.npy',
                        region_info['reads_current'])
                # del region_info_dict[region_string]
                # collect()
                progress.advance(task)
        self.output.info('Completed extracting current features.')

    def process(self):
        """Call the extracting featres object."""
        self.output.info('Starting extracting featres Process.')
        logger.debug('Starting extracting featres Process.')
        self.check_directory()
        self.extract_features()
        self.output.info('Completed extracting featres Process.')
        logger.debug('Completed extracting featres Process.')
