#!/usr/bin/env python3
import os, glob, warnings, tempfile, sys, zipfile
from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path
from typing import Optional, Literal
from pkginfo import Wheel

__version__ = '1.0.0'

LOGGING_LEVELS = ('silent', 'critical', 'error', 'warning', 'info', 'verbose', 'debug', 'silly')
ALLOWED_LOGGING_LEVEL_VALUES = ('silent', 'critical', 'error', 'warning', 'info', 'verbose', 'debug',
                                'silly', 0, 1, 2, 3, 4, 5, 6, 7, '0', '1', '2', '3', '4', '5', '6', '7')

LoggingLevelType = Literal[*ALLOWED_LOGGING_LEVEL_VALUES]
IntLoggingLevelType = Literal[0, 1, 2, 3, 4, 5, 6, 7]


class PythonPackageDownloader:
    def __init__(self):
        self._init_parser()
        self.requirements_file = None

    def _init_parser(self) -> None:
        self.parser = ArgumentParser()
        self.parser.add_argument('packages', nargs='+', type=str, help='packages to download')
        self.parser.add_argument('--version', '-v', action='version', version=__version__)
        self.parser.add_argument('--directory', '-d', type=str, help='directory for unpacking')
        self.parser.add_argument('--logging-level', '--log-level', '--loglevel', '--log',
                                 '--verbosity', '-l', '-V', type=self.logging_level, dest='logging_level',
                                 default=4, help='logging level')
        self.parser.add_argument('--save-wheel', '-s', '-w', action='store_true', help='save .whl files')
        self.parser.add_argument('--save-dist-info', '-i', action='store_true', help='save .dist-info directory')
        self.parser.add_argument('--requirements-file', '--requirements', '-r', type=str, nargs='?',
                                 help='path to requirements file', default=None, const='requirements.txt')

    def no_args_is_help(self):
        if len(sys.argv) == 1:
            self.parser.print_help()
            sys.exit(2)

    @staticmethod
    def red_text(message: str) -> str:
        return '\033[31m' + message + '\033[0m'

    @staticmethod
    def logging_level(level: LoggingLevelType) -> int:
        if level not in ALLOWED_LOGGING_LEVEL_VALUES:
            raise ArgumentTypeError(f'Invalid logging level: {level}')
        elif isinstance(level, int):
            return level
        elif level.isdigit():
            return int(level)
        else:
            return LOGGING_LEVELS.index(level)

    def pip_log_flags(self, temp_filename: str) -> str:
        match self.log_level:
            case 0:
                return f' -qqq > {temp_filename}'
            case 1:
                return ' -qqq'
            case 2:
                return ' -qq'
            case 3:
                return ' -q'
            case 4:
                return ''
            case 5:
                return ' -v'
            case 6:
                return ' -vv'
            case 7:
                return ' -vvv'
            case _:
                raise ValueError(f'Invalid logging level: {self.log_level}')

    def log(self, message: str, min_level: IntLoggingLevelType = 4, red: bool = False) -> None:
        if red:
            message = self.red_text(message)
        if min_level <= self.log_level:
            print(message)

    def write_wheel_requirements(self, wheel_file: Wheel) -> None:
        if self.requirements_file:
            self.log(f'Adding {wheel_file.name} package requirements to the {self.requirements_file.name} file',
                     5)
            self.log(f'{wheel_file.name} package requirements:', 7)
            for req in wheel_file.requires_dist:
                if '; extra' in req:
                    break
                self.requirements_file.write(f'{req}\n')
                self.log(req, 7)

    def download_wheels(self) -> None:
        with tempfile.NamedTemporaryFile('w+') as log_file:
            command = 'pip download ' + ' '.join(self.packages) + ' --no-deps'
            if self.directory:
                command += f' -d {self.directory}'
            command += self.pip_log_flags(log_file.name)
            self.log(f'Running a command {command}', 5)
            os.system(command)

    def extract_wheels(self) -> None:
        directory = Path(self.directory or os.getcwd()).resolve().absolute()
        package_names = list()
        if self.requirements_file_path:
            self.requirements_file = open(self.requirements_file_path, 'w+', encoding='utf-8')
        for filename in glob.glob('*.whl', root_dir=directory):
            full_path = directory / filename
            metadata = Wheel(str(full_path))
            with zipfile.ZipFile(full_path) as wheel:
                self.log(f'Extracting {full_path}')
                if not self.save_dist_info:
                    for file_info in wheel.infolist():
                        if '.dist-info' in file_info.filename or file_info.filename.endswith('.dist-info/RECORD'):
                            continue
                        wheel.extract(file_info, directory)
                else:
                    wheel.extractall(directory)
                self.log(f'Extracted {filename} to {directory}')
                self.write_wheel_requirements(metadata)
                package_names.append(metadata.name)

            if not self.save_wheel:
                if full_path.exists():
                    os.remove(full_path)
                    self.log(f'Removed {filename}')
                else:
                    self.log(f'Could not find {filename}', 3, True)
        self.log(str(package_names), 5)
        self.log(f'Successfully extracted {" ".join(package_names) if len(package_names) > 1 else package_names[0]}')
        if self.requirements_file:
            self.requirements_file.close()

    def _init_args(self, args):
        self.packages = args.packages
        self.log_level = args.logging_level
        self.directory = args.directory
        self.save_wheel = args.save_wheel
        self.save_dist_info = args.save_dist_info
        self.requirements_file_path = args.requirements_file

    def run(self):
        self.no_args_is_help()
        self._init_args(self.parser.parse_args())

        if self.log_level < 3:
            warnings.filterwarnings('ignore')

        try:
            self.download_wheels()
            self.extract_wheels()
        except Exception as error:
            if self.log_level == 0:
                pass
            elif self.log_level == 1:
                print(f'{error.__class__.__name__}: {error}')
            else:
                raise error
            sys.exit(1)


if __name__ == '__main__':
    PythonPackageDownloader().run()
