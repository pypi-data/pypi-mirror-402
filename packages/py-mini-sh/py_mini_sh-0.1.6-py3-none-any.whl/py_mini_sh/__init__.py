"""
This package provides helper functions to simplify the writing of
platform-independent sh-like scripts in Python.
"""

#
# Copyright Abelana Ltd, 2018.
# Licensed under the terms of the MIT License. See LICENSE.txt.
#

import os
import sys
import tarfile
import subprocess
import logging
import glob
import collections
import shutil
import zipfile
import re
import platform
from pathlib import Path

__version__ = '0.1.6'

#: ``PY2`` - True if running on a Python 2.X interpreter.
PY2 = sys.version_info < (3, 0)

if PY2:
    from urllib import ContentTooShortError, urlretrieve  # pylint: disable=no-name-in-module
else:
    from urllib.request import ContentTooShortError, urlretrieve  # pylint: disable=no-name-in-module,import-error


# Uncomment the following to get logging of what this script is doing
logging.getLogger().setLevel(logging.INFO)

#: ``WINDOWS`` is True if running on Windows, which is always the platform
#: which does things differently.
WINDOWS = "Windows" in platform.system()
MAC = "Darwin" in platform.system()
LINUX = "Linux" in platform.system()

# Core variables to have in DEFINES
DEFINES = dict(
    PYVER='%d.%d' % (sys.version_info.major, sys.version_info.minor), # e.g. '2.7'
    PYVER_NUMBER='%d%d' % (sys.version_info.major, sys.version_info.minor), # e.g. '27'
    BIN_DIR='Scripts',
    SEP='\\',
    PYTHON_EXEC=sys.executable,
    VENV_BIN=str(Path(sys.executable).parent) + '{SEP}',
    SITE_PACKAGES=str(Path(sys.executable).parent / 'site-packages{SEP}'),
    PLATFORM='win',
    OS=('%s_%s' % (platform.system(), platform.release())).lower(),
    ALLVARIANTS='{PLATFORM}-{PYVER_NUMBER}',
)

if not WINDOWS:
    # test if virtualenv on Linux

    # change some of the defines for Linux
    DEFINES.update(SEP='/',
                   BIN_DIR='bin',
                   PLATFORM='linux' if LINUX else 'mac',
                  )
else:
    # test if virtualenv on Windows
    if Path(sys.executable).parent.name.lower() != 'scripts':
        logging.error('This package should be run in a virtualenv rather than directly')
        sys.exit(1)

if 'PYPI_HOST' in os.environ:
    DEFINES.update(PYPI_HOST=os.environ['PYPI_HOST'],
                   PIP_FLAGS='-i http://{PYPI_HOST}/simple --trusted-host={PYPI_HOST}')
else:
    DEFINES.update(PIP_FLAGS='')


class CommandError(RuntimeError):
    """An exception that indicates a non-zero status has been returned from
    running a subprocess command.
    """

#: Backwards compatibility with old scripts
BuildError = CommandError


def expand(fstr):
    """Use the Python format method repeatedly to expand all variable
    references recursively.

    :param fstr: The string with the format expressions in it that
        need to be expanded with the current set of definitions.
    :type fstr: str

    :return: The recursively expanded string.
    :rtype: str
    """
    while True:
        nfstr = fstr.format(**DEFINES)
        if nfstr == fstr:
            return fstr
        fstr = nfstr


def exec_(cmd, cwd=None, env=None, ignore_error=False, echo=True):
    """Execute in command in a sub-shell. The ``cmd`` is expanded with the
    current definitions. Raise a ``CommandError`` on a non-zero return
    from the shell (unless ``ignore_error`` is True).

    :param cmd: The command to run, with format variables in it
        are expanded first.
    :type cmd: str

    :param cwd: Set the current working folder for the command if it
        is provided. If it is then it is also expanded first.
    :type cwd: None or str

    :param env: Change the environment in which the command runs if
        provided.
    :type env: None or dict

    :param ignore_error: Indicates whether an error running the
        command should be ignored, or if a CommandError exception is
        raised.
    :type ignore_error: bool

    :param echo: Indicates if the command should be echoed to the
        logging output or not. This us usually because the command
        might contain sensitive information.
    :type echo: bool
    """
    cmd = expand(cmd)
    if cwd:
        cwd = expand(cwd)
    if echo:
        logging.info("Running: %s", cmd)
    retcode = subprocess.call(cmd, shell=True, cwd=cwd, env=env)
    if retcode != 0:
        if not ignore_error:
            raise CommandError("Error running: %s" % cmd)
    return retcode


def pipe(cmd, cwd=None, ignore_error=False, env=None, regexp=None):
    """Execute the command in a sub-shell and collect the stdout from this
    command. The ``cmd`` is expanded with the current definitions. If
    the ``regexp`` argument is not provided, the stdout of the
    command is returned. If the ``regexp`` is provided, then the
    result of running an ``re.search`` on the output is returned.

    :param cmd: The command to run, with format variables in it
        are expanded first.
    :type cmd: str

    :param cwd: Set the current working folder for the command if it
        is provided. If it is then it is also expanded first.
    :type cwd: None or str

    :param ignore_error: If True ignore any error in running the
        command, otherwise raise a :py:exc:`BuildCommand` on any
        error.
    :type ignore_error: bool

    :param env: Change the environment in which the command runs if
        provided.
    :type env: None or dict

    :param regexp: A regular expression to use on the stdout of the
        command. If this is not provided the entire stdout is returned.
    :type regexp: None or an ``re.compile`` object.

    :return: The entire stdout of the command, or the result of
       running ``re.search`` on the stdout.
    :rtype: List[str] or a Regular Expression object

    :raises CommandError: when the cmd cannot run or returns a
        non-zero status.
    """
    cmd = expand(cmd)
    if cwd:
        cwd = expand(cwd)
    logging.info("Running: %s", cmd)
    try:
        output = subprocess.check_output(cmd, shell=True, cwd=cwd, env=env)
    except subprocess.CalledProcessError as exc:
        if ignore_error:
            output = exc.output
        else:
            raise CommandError("Error running: %s, error: %s" % (cmd, str(exc)))
    if regexp:
        return re.search(regexp, output)
    if not PY2:
        output = output.decode('utf-8')
    return output


def download(url, into, unpack=False, unpack_dir=None):
    """Download the contents at the specified URL, expanding the URL with
    the current definitions, into the file named ``into``. If
    ``unpack`` is True, then the retrieved file is assumed to be a tar
    file, and it is unpacked into the folder specified by ``unpack_dir``.

    :param url: The URL used to download the file after expanding it.
    :type url: str

    :param into: The name of the file, after expanding, into which the
        downloaded contents is saved.
    :type into: str

    :param unpack: If True then the downloaded file is unpacked.
    :type unpack: bool

    :param unpack_dir: If ``unpack`` is True the tar file is unpacked
        into this folder after it is expanded. If the value of this
        parameter is None then the default value of ``download`` is used.
        After a successful unpack the original downloaded file is deleted.
    :rtype: str or None

    :raises CommandError: if there is some error in downloading the
        file from the URL.
    """
    url = expand(url)
    into = expand(into)

    logging.info("Downloading URL: '%s' into '%s'", url, into)
    try:
        urlretrieve(url, into)
    except ContentTooShortError as exc:
        raise CommandError(str(exc))
    except IOError as exc:
        raise CommandError(str(exc))
    if unpack:
        if not unpack_dir:
            unpack_dir = 'download'
        unpack_dir = expand(unpack_dir)
        with tarfile.open(into) as tfile:
            tfile.extractall(unpack_dir)
        os.unlink(into)


def is_f(fname):
    """Test if the expanded filename exists.

    :param fname: The name of the file that is tested after :py:func:`expand` is called.
    :type fname: str
    :rtype: bool
    """
    return os.path.isfile(expand(fname))


def is_d(dname):
    """Test if the expanded directory exists.

    :param dname: The name of the directory that is tested after :py:func:`expand` is called.
    :type fname: str
    :rtype: bool
    """
    return os.path.isdir(expand(dname))


def readall(fname):
    """Read all the data from the expanded ``fname`` file. The file is
    opened in text mode.

    :param fname: The file name that gets expanded before being opened.
    :type fname: str

    :return: The contents of the file.
    """
    with open(expand(fname), 'r') as fhandle:
        return fhandle.read()


def writeall(fname, data):
    """Write the ``data`` to the expanded ``fname`` file. The file is
    opened in text mode.

    :param fname: The name of the file that gets written.
    :type fname: str

    :param data: The data that is written to the file.
    :type data: str
    """
    with open(expand(fname), 'w') as fhandle:
        fhandle.write(data)


def del_(fname):
    """Unlink the expanded ``fname`` file if it exists. If the file
    doesn't exist then this function does nothing. If it does, and
    there is an error in removing it, the appropriate OSError
    exception is raised.

    :param fname: Name of file to delete, which is expanded.
    :type fname: str
    """
    fname = expand(fname)
    if os.path.isfile(fname):
        os.unlink(fname)


def parse_pylint_output(lines):
    """This function is useful for extracting data from the stdout of a
    pylint command. It would normally be used in conjunction with a
    :py:func:`pipe` call like this::

        pylint_data = pipe('{VENV_BIN}pylint {PY_LINT_ARGS}', ignore_error=True)
        e, w, c, r = parse_pylint_output(pylint_data)

    :param lines: The lines of stdout text from a pylint run.
    :type lines: List[str]

    :return: A four-tuple of the number of errors, warnings,
        conventions and refactor statements found in the pylint output.
    """
    counting = collections.defaultdict(lambda: 0)
    for line in lines.splitlines():
        if len(line) > 2 and line[1] == ':':
            item = line[0]
            counting[item] += 1
    return counting['E'], counting['W'], counting['C'], counting['R']


def copytree(source, destn):
    """This function expands the supplied ``source`` and ``destn``
    parameters, and then invokes the ``shutil.copytree`` function.

    :param source: The source to the copytree, after it is expanded.
    :type source: str

    :param destn: The destination for the copytree, after it is expanded.
    :type destn: str
    """
    source = expand(source)
    destn = expand(destn)
    shutil.copytree(source, destn)


def unzip(source, destn):
    """This function expands the supplied ``source`` and ``destn``
    parameters, and then invokes the ``zipfile`` module's ``extractall`` method.

    :param source: The location of the zipfile, after it is expanded.
    :type source: str

    :param destn: The destination for where the zipfile should be
        unzipped, after it is expanded.
    :type destn: str
    """
    source = expand(source)
    destn = expand(destn)
    with zipfile.ZipFile(source, 'r') as zfile:
        zfile.extractall(destn)


def copy_changed_files(src, pat, dst, prefix=''):
    """This function is most useful for copying files into a ship folder,
    and only copying the files from the source that are not in the
    destination, or are newer in the source location. This could be
    useful to not trigger re-builds if some make system is expecting
    files not to change if they are not different. This function
    operates only on the supplied source folder and does not recurse
    into sub-folders.

    :param src: The location of the source folder, after it is expanded.
    :type source: str

    :param pat: A ``glob.glob`` pattern which is used for matching the
        source files, after it is expanded.
    :type pat: str

    :param dst: The destination for where the files should be
        copied, after it is expanded.
    :type destn: str
    """
    dst = expand(dst)
    pat = expand(os.path.join(src, pat))
    for fname in glob.glob(pat):
        dest = os.path.join(dst, prefix + os.path.basename(fname))
        existing = ""
        if os.path.isfile(dest):
            with open(dest, 'rb') as dname:
                existing = dname.read()

        with open(fname, 'rb') as fsource:
            current = fsource.read()
        if existing != current:
            logging.info("Copying %s to %s", fname, dest)
            with open(dest, 'wb') as fdest:
                fdest.write(current)


def parse_cmd_line():
    """Pull out command line options that look like "<name>=<value>", and
    return them in a dictionary. Ignore arguments that don't match
    this pattern.
    """
    result = dict()
    for arg in sys.argv[1:]:
        mtch = re.match(r'([a-zA-Z0-9_-]+)\=(\S+)$', arg)
        if mtch:
            var, val = mtch.groups()
            logging.info("Adding %s = %s to global defines", var, val)
            result[var] = val
    return result


def run(func, defines, add_cmd_args=True):
    """This is the entry-point into this package. Scripts should usually
    be expressed as a single function that is handed to this function
    to run in the context of the :ref:`predefined definitions
    <defines_list>`, augmented with the supplied of ``defines`` to
    this function. A common way to structure your script is to do
    the following::

        from py_mini_sh import run, ...

        MY_VAR = 'foo'
        ANOTHER_VAR = 42

        def main()
            ...

        if __name__ == '__main__':
            sys.exit(run(main, globals()))

    :param func: The function to call in the context of the supplied
        extra definitions.
    :type func: Zero-args callable

    :param defines: The list of extra defines or redefinitions which
        are used when expanding many of the parameters of the
        functions defined in this package.
    :type defines: dict

    :param add_cmd_args: If True the command line is parsed to look
        for values of the form "<name>=<value>", and these are defintions
        are added to the defines that are provided.
    :type add_cmd_args: bool

    :return: The return code which should be used to exit Python.
    :rtype: int
    """
    DEFINES.update(defines)
    if add_cmd_args:
        DEFINES.update(parse_cmd_line())
    try:
        func()
    except CommandError as exc:
        logging.error("Error: %s", exc)
        return 1
    return 0
