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
  - Predict:
"""

from logging import getLogger
from multiprocessing import cpu_count, Pool
from pathlib import Path

import numpy as np

from catboost import CatBoostClassifier

from CatMOD.reader.bed import BedReader
from CatMOD.sys_output import Output

logger = getLogger(__name__)  # pylint: disable=invalid-name


class Predict(object):
    """The predict process.

    Attributes:
      - args: Arguments.
      - output: Output info, warning and error.
    """

    def __init__(self, arguments):
        """Initialize Predict."""
        self.args = arguments
        self.output = Output()
        self.output.info(
            f'Initializing {self.__class__.__name__}: (args: {arguments}.')
        logger.debug(
            f'Initializing {self.__class__.__name__}: (args: {arguments}.')
        datasets_path = Path(self.args.datasets)
        if not datasets_path.is_dir():
            raise FileNotFoundError(f'{self.args.datasets} is not a directory.')
        self.threads = self.args.threads if self.args.threads else cpu_count()

    def get_all_samples(self):
        self.output.info('Reading bed file.')
        bed_reader = BedReader(self.args.bed)
        # self.region_list = []
        self.datasets_region_set = set()
        for each_region in bed_reader.read_bed():
            # self.region_list.append(each_region.copy())
            region_string = str(each_region)
            self.datasets_region_set.add(self.args.datasets+'/'+region_string)
        self.output.info('Completed reading bed file.')

    def ensemble_features(self):
        threads = min(self.threads, len(self.datasets_region_set))
        with Pool(processes=threads) as pool:
            _ = pool.map(ensemble_features, self.datasets_region_set)

    def predict_all_samples(self):
        threads = min(self.threads, len(self.datasets_region_set))
        global cbc
        cbc = CatBoostClassifier()
        cbc.load_model(self.args.model)
        with Pool(processes=threads) as pool:
            self.all_samples_results = pool.map(
                predict_sample, self.datasets_region_set)

    def write_all_results(self):
        with open(self.args.output, 'w') as open_output:
            for each_sample_result in self.all_samples_results:
                if each_sample_result:
                    open_output.write('\t'.join(each_sample_result) + '\n')

    def process(self):
        """Call the predicting object."""
        self.output.info('Starting predicting Process.')
        logger.debug('Starting predicting Process.')
        self.get_all_samples()
        self.ensemble_features()
        self.predict_all_samples()
        self.write_all_results()
        self.output.info('Completed predicting Process.')
        logger.debug('Completed predicting Process.')


def ensemble_features(datasets_region: str):
    sequence_path = Path(
        f'{datasets_region}.ref_seq.npy')
    alignment_path = Path(
        f'{datasets_region}.reads_alignment.npy')
    quality_path = Path(
        f'{datasets_region}.reads_quality.npy')
    norm_mean_path = Path(
        f'{datasets_region}.reads_norm_mean.npy')
    norm_stdev_path = Path(
        f'{datasets_region}.reads_norm_stdev.npy')
    current_path = Path(
        f'{datasets_region}.reads_current.npy')
    if sequence_path.is_file() and alignment_path.is_file() and quality_path.is_file() and norm_mean_path.is_file() and norm_stdev_path.is_file() and current_path.is_file():
        reads_alignment = np.load(alignment_path)
        reads_quality = np.load(quality_path).astype(np.float32)
        if reads_alignment.shape[0] == reads_quality.shape[0] > 0 and reads_alignment.shape[1] == reads_quality.shape[1] and reads_alignment.shape[2] == 6:
            reads_norm_mean = np.load(norm_mean_path).astype(np.float32)
            reads_norm_stdev = np.load(norm_stdev_path).astype(np.float32)
            reads_current = np.load(current_path).astype(np.float32)
            if reads_norm_mean.shape[0] == reads_norm_stdev.shape[0] == reads_current.shape[0] > 0 and reads_norm_mean.shape[1] == reads_norm_stdev.shape[1] == 5: #and reads_current.shape[1] == 256:
                reads_alignment = reads_alignment.reshape(reads_alignment.shape[0], -1).astype(np.float32)
                sequence = np.load(sequence_path)
                sequence = sequence.flatten().astype(np.float32)
                np.save(f'{datasets_region}.ensemble_features.npy',
                        np.array([np.concatenate((
                            sequence, reads_alignment.mean(0), reads_quality.mean(0),
                            reads_norm_mean.mean(0), reads_norm_stdev.mean(0), reads_current.mean(0)))], dtype=np.float32))


def predict_sample(datasets_region):
    region_path = Path(f'{datasets_region}.ensemble_features.npy')
    if region_path.is_file():
        region_features_array = np.load(region_path)
        region_pred_proba = cbc.predict_proba(
            region_features_array, thread_count=1)
        region_pred_array = np.rint(region_pred_proba[:,1]).astype(np.int32)
        spregion = datasets_region.split('/')[1].split('_')
        spposition = spregion[2].split('-')
        return [spregion[0], spposition[0], spposition[1],
                str(region_pred_array[0]), str(region_pred_proba[0,1]),
                spregion[1]]
    else:
        return []