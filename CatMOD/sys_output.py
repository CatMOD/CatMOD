# -*- coding: utf-8 -*-
# Copyright 2022 Shang Xie.
# All rights reserved.
#
# This file is part of the CatMOD distribution and
# governed by your choice of the "CatMOD License Agreement"
# or the "GNU General Public License v3.0".
# Please see the LICENSE file that should
# have been included as part of this package.
"""Represent an output.

What's here:

Format and display output.
--------------------------

Classes:
  - Output
"""

from platform import system


class Output():
    """Format and display output.

    Attributes:
      - red: Red color.
      - green: Green color.
      - yellow: Yellow color.
      - default_color: Default color.
      - term_support_color: Term support color.
    """

    def __init__(self):
        """Initialize Output."""
        self.red = '\033[31m'
        self.green = '\033[32m'
        self.yellow = '\033[33m'
        self.default_color = '\033[0m'
        self.term_support_color = system() in ('Linux', 'Darwin')

    @staticmethod
    def __indent_text_block(text: str):
        """Indent a text block."""
        lines = text.splitlines()
        if len(lines) > 1:
            out = lines[0] + '\r\n'
            for i in range(1, len(lines) - 1):
                out = out + '        ' + lines[i] + '\r\n'
            out = out + '        ' + lines[-1]
            return out
        return text

    def info(self, text: str):
        """Format INFO Text."""
        trm = 'INFO    '
        if self.term_support_color:
            trm = f'{self.green}INFO   {self.default_color} '
        print(trm + self.__indent_text_block(text))

    def warning(self, text: str):
        """Format WARNING Text."""
        trm = 'WARNING '
        if self.term_support_color:
            trm = f'{self.yellow}WARNING{self.default_color} '
        print(trm + self.__indent_text_block(text))

    def error(self, text: str):
        """Format ERROR Text."""
        global INSTALL_FAILED  # pylint:disable=global-statement
        trm = 'ERROR   '
        if self.term_support_color:
            trm = f'{self.red}ERROR  {self.default_color} '
        print(trm + self.__indent_text_block(text))
        INSTALL_FAILED = True
