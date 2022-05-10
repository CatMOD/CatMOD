"""setup script for CatMOD.

This uses setuptools which is now the standard python mechanism for
installing packages. If you have downloaded and uncompressed the
CatMOD source code, or fetched it from git, for the simplest
installation just type the command:

    python setup.py install

However, you would normally install the latest CatMOD release from
the PyPI archive with:

    pip install catmod

Or, you can also install it via conda's bioconda channel:

    conda install catmod --channel bioconda

For more in-depth instructions, see the Install section of the
CatMOD manual, linked to from:

    https://github.com/CatMOD/CatMOD/wiki

If all else fails, feel free to post on GitHub Issue:

    https://github.com/CatMOD/CatMOD/issues

or contact Shang Xie and ask for help:

    xieshang0608@gmail.com
"""

import ctypes
from locale import getpreferredencoding
import os
import platform
from re import sub
from subprocess import CalledProcessError, PIPE, Popen, run
import sys

from CatMOD.sys_output import Output


class Environment(object):
    """The current install environment.

    Attributes:
        output (Output): output info, warning and error.
        is_installer (bool): whether to enter the installer mode.
        missing_packages (list): missing packages from current environment.
        conda_missing_packages (list): missing packages from current
                                       conda environment.
    """

    def __init__(self):
        """Initialize an Environment on current environment."""
        self.output = Output()
        self.is_installer = False
        self.conda_required_packages = [('h5py', 'conda-forge'),
                                        ('numpy',),
                                        ('pysam', 'bioconda'),
                                        ('rich', 'conda-forge')]
        self.missing_packages = []
        self.conda_missing_packages = []

        self.process_arguments()
        self.check_permission()
        self.check_system()
        self.check_python()
        self.output_runtime_info()
        self.check_pip()
        self.upgrade_pip()
        self.get_installed_packages()
        self.get_installed_conda_packages()
        self.get_required_packages()
        super().__init__()

    @property
    def is_admin(self):
        """Check whether user is admin.

        Returns:
            retval (bool)
        """
        try:
            retval = os.getuid() == 0
        except AttributeError:
            retval = ctypes.windll.shell32.IsUserAnAdmin() != 0
        return retval

    @property
    def os_version(self):
        """Get OS Version."""
        return platform.system(), platform.release()

    @property
    def py_version(self):
        """Get Python Version."""
        return platform.python_version(), platform.architecture()[0]

    @property
    def is_conda(self):
        """Check whether using Conda.

        Returns:
            (bool)
        """
        return 'conda' in sys.version.lower()

    @property
    def is_virtualenv(self):
        """Check whether this is a virtual environment.

        Returns:
            retval (bool)
        """
        if not self.is_conda:
            retval = (hasattr(sys, 'real_prefix') or
                      (hasattr(sys, 'base_prefix') and
                       sys.base_prefix != sys.prefix))
        else:
            prefix = os.path.dirname(sys.prefix)
            retval = os.path.basename(prefix) == 'envs'
        return retval

    @property
    def encoding(self):
        """Get system encoding."""
        return getpreferredencoding()

    def process_arguments(self):
        """Process any cli arguments."""
        argv = [arg for arg in sys.argv]
        for arg in argv:
            if arg == 'install':
                self.is_installer = True

    def check_permission(self):
        """Check for Admin permissions."""
        if self.is_admin:
            self.output.info('Running as Root/Admin')
        else:
            self.output.warning('Running without root/admin privileges')

    def check_system(self):
        """Check the system."""
        self.output.info('The tool provides tips for installation\n'
                         'and installs required python packages')
        self.output.info(f'Setup in {self.os_version[0]} {self.os_version[1]}')
        if not self.os_version[0] in ['Linux', 'Darwin']:
            self.output.error(
                f'Your system {self.os_version[0]} is not supported!')
            sys.exit(1)

    def check_python(self):
        """Check python and virtual environment status."""
        self.output.info(
            f'Installed Python: {self.py_version[0]} {self.py_version[1]}')
        if not (self.py_version[0].split('.')[0] == '3' and
                self.py_version[0].split('.')[1] in ('7', '8', '9')):
            self.output.error('Please run this script with Python version '
                              '3.7, 3.8 or 3.9 and try again.')
            sys.exit(1)

    def output_runtime_info(self):
        """Output runtime info."""
        if self.is_conda:
            self.output.info('Running in Conda')
        if self.is_virtualenv:
            self.output.info('Running in a Virtual Environment')
        self.output.info(f'Encoding: {self.encoding}')

    def check_pip(self):
        """Check installed pip version."""
        try:
            import pip  # noqa pylint:disable=unused-import
        except ImportError:
            self.output.error(
                'Import pip failed. Please Install python3-pip and try again')
            sys.exit(1)

    def upgrade_pip(self):
        """Upgrade pip to latest version."""
        if not self.is_conda:
            # Don't do this with Conda, as we must use conda's pip
            self.output.info('Upgrading pip...')
            pipexe = [sys.executable, '-m', 'pip']
            pipexe.extend(['install', '--no-cache-dir', '-qq', '--upgrade'])
            if not self.is_admin and not self.is_virtualenv:
                pipexe.append('--user')
            pipexe.append('pip')
            run(pipexe)
        import pip
        self.output.info(f'Installed pip: {pip.__version__}')

    def get_installed_packages(self):
        """Get currently installed packages."""
        self.installed_packages = {}
        chk = Popen(f'"{sys.executable}" -m pip freeze',
                    shell=True, stdout=PIPE)
        installed = chk.communicate()[0].decode(self.encoding).splitlines()

        for pkg in installed:
            if '==' not in pkg:
                continue
            item = pkg.split('==')
            self.installed_packages.update({item[0]: item[1]})

    def get_installed_conda_packages(self):
        """Get currently installed conda packages."""
        if not self.is_conda:
            return
        self.installed_conda_packages = {}
        chk = os.popen('conda list').read()
        installed = [sub(' +', ' ', line.strip())
                     for line in chk.splitlines() if not line.startswith('#')]
        for pkg in installed:
            item = pkg.split(' ')
            self.installed_conda_packages.update({item[0]: item[1]})

    def get_required_packages(self):
        """Load requirements list."""
        self.required_packages = []
        pypath = os.path.dirname(os.path.realpath(__file__))
        requirements_file = os.path.join(pypath, 'requirements.txt')
        with open(requirements_file) as req:
            for package in req.readlines():
                package = package.strip()
                if package and (not package.startswith('#')):
                    self.required_packages.append(package)


class Install(object):
    """Install the requirements.

    Attributes:
        output: output info, warning and error.
        env: environment.
    """

    def __init__(self, environment: Environment):
        """Initialize an Install.

        Args:
            environment (Environment): store an environment.
        """
        self.output = Output()
        self.env = environment

        if not self.env.is_installer:
            self.ask_continue()

        self.install_missing_dep()
        self.output.info('All python3 dependencies are met.\r\n'
                         'You are good to go.\r\n\r\n'
                         'Enter:  python sgphasing.py -h to see the options')
        super().__init__()

    def ask_continue(self):
        """Ask Continue with Install."""
        inp = input(
            'Please ensure your System Dependencies are met. Continue? [y/N] ')
        if inp in ('', 'N', 'n'):
            self.output.error('Please install system dependencies to continue')
            sys.exit(1)

    def check_missing_dep(self):
        """Check for missing dependencies."""
        for pkg in self.env.required_packages:
            pkgs = pkg.split('==')
            key = pkgs[0]
            if key not in self.env.installed_packages:
                self.env.missing_packages.append(pkg)
                continue
            else:
                if len(pkgs) > 1:
                    if pkgs[1] != self.env.installed_packages.get(key):
                        self.env.missing_packages.append(pkg)
                        continue

    def check_conda_missing_dep(self):
        """Check for conda missing dependencies."""
        if not self.env.is_conda:
            return
        for pkg in self.env.conda_required_packages:
            pkgs = pkg.split('==')
            key = pkgs[0]
            if key not in self.env.installed_packages:
                self.env.conda_missing_packages.append(pkg)
                continue
            else:
                if len(pkgs) > 1:
                    if pkgs[1] != self.env.installed_conda_packages.get(key):
                        self.env.conda_missing_packages.append(pkg)
                        continue

    def install_missing_dep(self):
        """Install missing dependencies."""
        # Install conda packages first
        self.check_conda_missing_dep()
        if self.env.conda_missing_packages:
            self.install_conda_packages()
        self.check_missing_dep()
        if self.env.missing_packages:
            self.install_python_packages()

    def install_conda_packages(self):
        """Install required conda packages."""
        self.output.info(
            'Installing Required Conda Packages. This may take some time...')
        for pkg in self.env.conda_missing_packages:
            channel = '' if len(pkg) != 2 else pkg[1]
            self.conda_installer(pkg[0], channel=channel, conda_only=True)

    def conda_installer(self,
                        package: str,
                        channel: str = '',
                        verbose: bool = False,
                        conda_only: bool = False):
        """Install a conda package.

        Args:
            package (str): package name string.
            channel (str): channel name string, default ''.
            verbose (bool): verbose, default False.
            conda_only (bool): if conda only, default False.

        Returns:
            success (bool): if success.
        """
        success = True
        condaexe = ['conda', 'install', '-y']
        if not verbose:
            condaexe.append('-q')
        if channel:
            condaexe.extend(['-c', channel])
        condaexe.append(package)
        self.output.info(f'Installing {package}')
        try:
            if verbose:
                run(condaexe, check=True)
            else:
                with open(os.devnull, 'w') as devnull:
                    run(condaexe, stdout=devnull, stderr=devnull, check=True)
        except CalledProcessError:
            if not conda_only:
                self.output.info(
                    f'Couldn\'t install {package} with Conda. Trying pip')
            else:
                self.output.warning(f'Couldn\'t install {package} with Conda. '
                                    'Please install this package manually')
            success = False
        return success

    def install_python_packages(self, verbose: bool = False):
        """Install required pip packages.

        Args:
            verbose (bool): verbose, default False.
        """
        self.output.info(
            'Installing Required Python Packages. This may take some time...')
        for pkg in self.env.missing_packages:
            self.pip_installer(pkg)

    def pip_installer(self, package: str):
        """Install a pip package.

        Args:
            package (str): package name string.
        """
        pipexe = [sys.executable, '-m', 'pip']
        # hide info/warning and fix cache hang
        pipexe.extend(['install', '-qq', '--no-cache-dir'])
        # install as user to solve perm restriction
        if not self.env.is_admin and not self.env.is_virtualenv:
            pipexe.append('--user')
        msg = f'Installing {package}'
        self.output.info(msg)
        pipexe.append(package)
        try:
            run(pipexe, check=True)
        except CalledProcessError:
            self.output.warning(f'Couldn\'t install {package} with pip. '
                                'Please install this package manually')


def main():
    """Create an environment and install missing packages."""
    ENV = Environment()
    Install(ENV)


if __name__ == '__main__':
    main()
