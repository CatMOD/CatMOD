# -*- coding: utf-8 -*-
# Copyright 2022 Shang Xie.
# All rights reserved.
#
# This file is part of the CatMOD distribution and
# governed by your choice of the "CatMOD License Agreement"
# or the "GNU General Public License v3.0".
# Please see the LICENSE file that should
# have been included as part of this package.
"""Represent a full help argument parser and execute.

What's here:

Loads the relevant script modules and executes the script.
----------------------------------------------------------

Classes:
  - ScriptExecutor

Identical to the built-in argument parser.
------------------------------------------

Classes:
  - FullHelpArgumentParser

Smart formatter for allowing raw formatting in help
text and lists in the helptext.
---------------------------------------------------

Classes:
  - SmartFormatter

CatMOD argument parser functions.
----------------------------------

Classes:
  - CatMODArgs

Parse the sub-command line arguments.
-------------------------------------

Classes:
  - DPArgs
  - EFArgs
  - TrainArgs
  - PredictArgs
"""

from argparse import ArgumentParser, HelpFormatter
from importlib import import_module
from logging import getLogger
from os import getpid
from re import ASCII, compile
from sys import exit, stderr
from textwrap import wrap

from CatMOD.sys_output import Output


logger = getLogger(__name__)  # pylint: disable=invalid-name


class ScriptExecutor(object):
    """Loads the relevant script modules and executes the script.

    This class is initialised in each of the argparsers for the relevant
    command, then execute script is called within their set_default function.

    Attributes:
      - command (str): Full commands.
      - subparsers: Subparsers for each subcommand.
      - output: Output info, warning and error.
    """

    def __init__(self, command: str, subparsers=None):
        """Initialize ScriptExecutor.
        Args:
          - command (str): Full commands.
          - subparsers: Subparsers for each subcommand.
        """
        self.command = command.lower()
        self.subparsers = subparsers
        self.output = Output()

    def import_script(self):
        """Only import a script's modules when running that script."""
        # cmd = os.path.basename(sys.argv[0])
        src = 'CatMOD'
        mod = '.'.join((src, self.command.lower()))
        module = import_module(mod)
        script = getattr(module, self.command.title().replace('_', ''))
        return script

    def execute_script(self, arguments):
        """Run the script for called command."""
        self.output.info(f'Executing: {self.command}. PID: {getpid()}')
        logger.debug(f'Executing: {self.command}. PID: {getpid()}')
        try:
            script = self.import_script()
            process = script(arguments)
            process.process()
        except KeyboardInterrupt:  # pylint: disable=try-except-raise
            raise
        except SystemExit:
            pass
        except Exception:  # pylint: disable=broad-except
            logger.exception('Got Exception on main handler:')
            logger.critical(
                'An unexpected crash has occurred. '
                'Crash report written to logfile. '
                'Please verify you are running the latest version of CatMOD '
                'before reporting.')
        finally:
            exit()


class FullHelpArgumentParser(ArgumentParser):
    """Identical to the built-in argument parser.

    On error it prints full help message instead of just usage information.
    """

    def error(self, message: str):
        """Print full help messages."""
        self.print_help(stderr)
        args = {'prog': self.prog, 'message': message}
        self.exit(2, f'{self.prog}: error: {message}\n')


class SmartFormatter(HelpFormatter):
    """Smart formatter for allowing raw formatting.

    Mainly acting in help text and lists in the helptext.

    To use: prefix the help item with 'R|' to overide
    default formatting. List items can be marked with 'L|'
    at the start of a newline.

    Adapted from: https://stackoverflow.com/questions/3853722
    """

    def __init__(self, prog: str,
                 indent_increment: int = 2,
                 max_help_position: int = 24,
                 width=None):
        """Initialize SmartFormatter.

        Args:
          - prog (str): Program name.
          - indent_increment (int): Indent increment. default 2.
          - max_help_position (int): Max help position. default 24.
          - width: Width.
        """
        super().__init__(prog, indent_increment, max_help_position, width)
        self._whitespace_matcher_limited = compile(r'[ \r\f\v]+', ASCII)

    def _split_lines(self, text: str, width):
        if text.startswith('R|'):
            text = self._whitespace_matcher_limited.sub(' ', text).strip()[2:]
            output = []
            for txt in text.splitlines():
                indent = ''
                if txt.startswith('L|'):
                    indent = '    '
                    txt = '  - {}'.format(txt[2:])
                output.extend(wrap(
                    txt, width, subsequent_indent=indent))
            return output
        return HelpFormatter._split_lines(self, text, width)


class CatmodArgs(object):
    """CatMOD argument parser functions.

    It is universal to all commands.
    Should be the parent function of all subsequent argparsers.

    Attributes:
      - global_arguments: Global arguments.
      - argument_list: Argument list.
      - optional_arguments: Optional arguments.
      - parser: Parser.
    """

    def __init__(self, subparser, command: str,
                 description: str = 'default', subparsers=None):
        """Initialize CatmodArgs.

        Args:
          - subparser: Subparser.
          - command (str): Command.
          - description (str): Description. default 'default'.
          - subparsers: Subparsers.
        """
        self.global_arguments = self.get_global_arguments()
        self.argument_list = self.get_argument_list()
        self.optional_arguments = self.get_optional_arguments()
        if not subparser:
            return
        self.parser = self.create_parser(subparser, command, description)
        self.add_arguments()
        script = ScriptExecutor(command, subparsers)
        self.parser.set_defaults(func=script.execute_script)

    @staticmethod
    def get_argument_list():
        """Put the arguments in a list so that they are accessible."""
        argument_list = []
        return argument_list

    @staticmethod
    def get_optional_arguments():
        """Put the arguments in a list so that they are accessible.

        This is used for when there are sub-children.
        (e.g. convert and extract) Override this for custom arguments.
        """
        argument_list = []
        return argument_list

    @staticmethod
    def get_global_arguments():
        """Arguments that are used in ALL parts of CatMOD.

        DO NOT override this!
        """
        global_args = []
        global_args.append({'opts': ('-v', '--version'),
                            'action': 'version',
                            'version': 'CatMOD v0.0.1a'})
        return global_args

    @staticmethod
    def create_parser(subparser, command: str, description: str):
        """Create the parser for the selected command."""
        parser = subparser.add_parser(
            command,
            help=description,
            description=description,
            epilog='Questions and feedback: '
                   'https://github.com/CatMOD/CatMOD',
            formatter_class=SmartFormatter)
        return parser

    def add_arguments(self):
        """Parse the arguments passed in from argparse."""
        options = (self.global_arguments + self.argument_list +
                   self.optional_arguments)
        for option in options:
            args = option['opts']
            kwargs = {key: option[key]
                      for key in option.keys() if key != 'opts'}
            self.parser.add_argument(*args, **kwargs)


class DPArgs(CatmodArgs):
    """."""

    @staticmethod
    def get_argument_list():
        """Put the arguments in a list so that they are accessible."""
        argument_list = []
        argument_list.append({
            'opts': ('-r', '--ref'),
            'dest': 'reference',
            'required': True,
            'type': str,
            'help': 'input reference fasta file.'})
        argument_list.append({
            'opts': ('-c', '--current'),
            'dest': 'current',
            'required': True,
            'type': str,
            'help': 'input ONT fast5 dictionary.'})
        # argument_list.append({
        #     'opts': ('-n', '--neg'),
        #     'dest': 'negative',
        #     'required': True,
        #     'type': str,
        #     'nargs': '+',
        #     'help': 'input negative bed files.'})
        argument_list.append({
            'opts': ('-o', '--output'),
            'dest': 'output',
            'required': True,
            'type': str,
            'help': 'output folder path.'})
        return argument_list


class EFArgs(CatmodArgs):
    """."""

    @staticmethod
    def get_argument_list():
        """Put the arguments in a list so that they are accessible."""
        argument_list = []
        argument_list.append({
            'opts': ('-b', '--bed'),
            'dest': 'bed',
            'required': True,
            'type': str,
            'help': 'input all samples bed file.'})
        argument_list.append({
            'opts': ('-r', '--ref'),
            'dest': 'reference',
            'required': True,
            'type': str,
            'help': 'input reference fasta file.'})
        argument_list.append({
            'opts': ('-a', '--align'),
            'dest': 'align',
            'required': True,
            'type': str,
            'help': 'input ONT alignment bam file.'})
        argument_list.append({
            'opts': ('-c', '--current'),
            'dest': 'current',
            'required': True,
            'type': str,
            'help': 'input ONT current folder or index file.'})
        argument_list.append({
            'opts': ('-sw', '--seq_window'),
            'dest': 'seq_window',
            'required': False,
            'type': int,
            'default': 101,
            'help': 'length of sequence window to use [default=101].'})
        argument_list.append({
            'opts': ('-aw', '--ali_window'),
            'dest': 'ali_window',
            'required': False,
            'type': int,
            'default': 41,
            'help': 'length of alignment window to use [default=41].'})
        argument_list.append({
            'opts': ('-cw', '--cur_window'),
            'dest': 'cur_window',
            'required': False,
            'type': int,
            'default': 256,
            'help': 'length of current window window to use [default=256].'})
        argument_list.append({
            'opts': ('-ck', '--current_kind'),
            'dest': 'current_kind',
            'required': False,
            'type': str,
            'default': 'linear',
            'help': 'Specifies the kind of interpolation as a string or as an '
                    'integer specifying the order of the spline interpolator '
                    'to use. The string has to be one of `linear`, `nearest`, '
                    '`nearest-up`, `zero`, `slinear`, `quadratic`, `cubic`, '
                    '`previous`, or `next`. `zero`, `slinear`, `quadratic` '
                    'and `cubic` refer to a spline interpolation of zeroth, '
                    'first, second or third order; `previous` and `next` '
                    'simply return the previous or next value of the point; '
                    '`nearest-up` and `nearest` differ when interpolating '
                    'half-integers (e.g. 0.5, 1.5) in that `nearest-up` '
                    'rounds up and `nearest` rounds down. Default is `linear`.'
        })
        argument_list.append({
            'opts': ('-t', '--threads'),
            'dest': 'threads',
            'required': False,
            'type': int,
            'default': 0,
            'help': 'number of threads to use [default=all].'})
        argument_list.append({
            'opts': ('-s', '--seed'),
            'dest': 'seed',
            'required': False,
            'type': int,
            'default': 0,
            'help': 'random seed for sampling to use [default=0].'})
        argument_list.append({
            'opts': ('--use_memory',),
            'dest': 'use_memory',
            'required': False,
            'type': bool,
            'default': False,
            'help': 'use memory to speed up [default=False].'})
        argument_list.append({
            'opts': ('--overwrite',),
            'dest': 'overwrite',
            'required': False,
            'type': bool,
            'default': False,
            'help': 'overwrite [default=False].'})
        argument_list.append({
            'opts': ('-o', '--output'),
            'dest': 'output',
            'required': True,
            'type': str,
            'help': 'output folder path.'})
        return argument_list


class TrainArgs(CatmodArgs):
    """."""

    @staticmethod
    def get_argument_list():
        """Put the arguments in a list so that they are accessible."""
        argument_list = []
        return argument_list


class PredictArgs(CatmodArgs):
    """."""

    @staticmethod
    def get_argument_list():
        """Put the arguments in a list so that they are accessible."""
        argument_list = []
        argument_list.append({
            'opts': ('-b', '--bed'),
            'dest': 'bed',
            'required': True,
            'type': str,
            'help': 'input all samples bed file.'})
        argument_list.append({
            'opts': ('-d', '--datasets'),
            'dest': 'datasets',
            'required': True,
            'type': str,
            'help': 'input datasets folder path.'})
        argument_list.append({
            'opts': ('-m', '--model'),
            'dest': 'model',
            'required': True,
            'type': str,
            'help': 'input saved model file path.'})
        argument_list.append({
            'opts': ('-t', '--threads'),
            'dest': 'threads',
            'required': False,
            'type': int,
            'default': 0,
            'help': 'number of threads to use [default=all].'})
        argument_list.append({
            'opts': ('-o', '--output'),
            'dest': 'output',
            'required': True,
            'type': str,
            'help': 'output file path.'})
        return argument_list
