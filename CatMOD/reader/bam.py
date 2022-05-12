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

Functions:
  - check_index:
"""

import pysam

from CatMOD.sys_output import Output


def open_xam(input_xam: str):
    """Check input and open.

    Args:
        input_xam (str): input sam or bam file path string.

    Returns:
        xamfile (AlignmentFile): pysam opened bam/cram/sam file handle.
        input_format (str): return input_xam format, sam or bam.
    """
    if input_xam.endswith('cram'):
        xamfile = pysam.AlignmentFile(input_xam, 'rc', check_sq=False)
        input_format = 'cram'
    elif input_xam.endswith('bam'):
        xamfile = pysam.AlignmentFile(input_xam, 'rb', check_sq=False)
        input_format = 'bam'
    elif input_xam.endswith('sam'):
        xamfile = pysam.AlignmentFile(input_xam, 'r', check_sq=False)
        input_format = 'sam'
    else:
        output = Output()
        output.error('Input error: input format must be'
                     ' bam, cram or sam file.')
        exit()
    return xamfile, input_format


def check_index(input_xam: str, threads: int = 1):
    """Build index for bam if not exists.

    Args:
        input_xam (str): input sam or bam file path string.
        threads (int): threads using for pysam sort and index, default 1.
    """
    xamfile, input_format = open_xam(input_xam)
    try:
        xamfile.check_index()
        return input_xam
    except ValueError:
        output = Output()
        output.warning(f'{input_xam} lacks .bai or .csi index.')
        output.info(f'Preparing samtools index for input {input_xam}')
        pysam.index(input_xam, '-b', '-@', str(threads))
        xamfile.close()
        return input_xam
    except AttributeError:
        output = Output()
        output.warning(f'{input_xam} lacks .bai or .csi index.')
        output.info(f'Preparing samtools index for input {input_xam}')
        if input_format == 'sam':
            input_bam = input_xam[:-3] + 'bam'
            pysam.sort('-o', input_bam, '--output-fmt', 'BAM',
                       '--threads', str(threads), input_xam)
            pysam.index(input_bam, '-b', '-@', str(threads))
            xamfile.close()
            return input_bam
        else:
            output.error('Input error: input --bam must be a'
                         ' bam, cram or sam file.')
            exit()
