<a id="en-doc"></a>
# Python Package Downloader (PPD) - Documentation
#### [Документация на русском](#ru-doc)

## Description
**Python Package Downloader (PPD)** is a command—line tool for easily downloading and unpacking Python packages as `.whl` files with the ability to automatically extract and manage dependencies.

## Installation
```shell
pip install python-package-downloader
```

After installation, there are three commands available to run:
- `ppd` (recommended)
- `python-package-downloader`
- `python_package_downloader`

## Basic usage
### Basic syntax
```shell
ppd <pack1> <pack2> ... [options]
```

### Examples
```shell
# Downloading and unpacking a single
ppd requests package

# Download multiple
ppd packages numpy pandas matplotlib

# Uploading to the specified directory
ppd requests --directory ./my_packages

# Save .whl files after unpacking
ppd flask --save-wheel

# Save .dist-info
ppd django --save-dist-info
```

## Command line options
### Required arguments
- `packages` — one or more packages to download (positional argument)

### Basic options
| Option | Short version | Description |
|---------------------------------------------|-----------------|-----------------------------------------------|
| `-- version`, `-v` | `-v` | Show program version |
| `--directory`, `-d` | `-d <path>`     | Directory for downloading and unpacking packages |
| `--save-wheel`, `-w` | `-w` | Save .whl files after unpacking |
| `--save-dist-info`, `-i` | `-i` | Save .dist-info directories |
| `--requirements-file`, `--requirements`, `-r` | `-r [path]`     | Create a file requirements.txt with dependencies |

### Output control (logging)
| Option | Short version | Values | Description |
|------------------------------------------------------------------------------------|-----------------|-----------------------------------------------------------------------------------------|----------------------------|
| `-- logging-level`, `--log-level`, `--loglevel`, `--log`, `--verbosity`, `-l`, `-V` | `-l`, `-V` | `0-7` or `silent`, `critical`, `error`, `warning`, `info`, `verbose`, `debug`, `silly` | Output level of detail |

#### Logging levels:
- `0` / `silent` — completely silent mode
- `1` / `critical` — critical errors only
- `2` / `error` — errors
- `3` / `warning` — warnings
- `4` / `info` — normal information (default)
- `5` / `verbose` — detailed information
- `6` / `debug` — debugging information
- `7` / `silly` — maximum detail

## Detailed description of the functionality
### The work process
1. **Downloading packages:** The program uses `pip download` to download `.whl` files without dependencies
2. **Unpacking:** Automatically extracts the contents of `.whl` files
3. **Cleaning:** By default, deletes the `.whl` files and `.dist-info' directories after unpacking
4. **Dependency Management:** Can create a file `requirements.txt ` with package dependencies

### Features
- **Automatic Python detection:** Finds an available Python interpreter in the system
- **Error handling:** Different error display levels depending on the logging level
- **Color output:** Uses color formatting for better readability
- **Checking for updates:** Automatically checks for new versions

### Files and directories
By default, the program:
1. Downloads `.whl` files to the current directory (or specified via `-d`)
2. Unpacks them into the same directory
3. Deletes `.whl` files (unless `--save-wheel` is specified)
4. Deletes `.dist-info` directories (unless `--save-dist-info` is specified)
5. Creates `requirements.txt ` with dependencies (if `-r` is specified)

## Usage examples
### Example 1: Downloading an offline installation package
```shell
# Upload the package to the current
ppd requests directory

# Result:
# - The requests/ directory with the package contents
# - The package files are ready for use
```

### Example 2: Creating a portable library
```shell
# Create a directory with multiple packages
ppd numpy pandas matplotlib --directory ./data_science_packages

# Save information about
ppd numpy pandas matplotlib -r dependencies./requirements.txt
```

### Example 3: Silent mode for scripts
```shell
# Minimal output, only
ppd errors some-package --log-level silent
# or
ppd some-package -l 0
```

### Example 4: Debugging problems
```shell
# Maximum detailed output
ppd problematic-package --log-level silly
# or
ppd problematic-package -l 7
```

## Requirements
- Python >= 3.10
- Internet access to download packages
- Installed `pip` in the system

## Permissions
- MIT License
- Cross-platform (Windows, Linux, macOS)

## Support and feedback
- The author: Маг Ильяс DOMA (MagIlyasDOMA)
- Email: magilyas.doma.09@list.ru
- GitHub: [https://github.com/MagIlyasDOMA/python-package-downloader](https://github.com/MagIlyasDOMA/python-package-downloader )
- PyPI: [https://pypi.org/project/python-package-downloader/](https://pypi.org/project/python-package-downloader/)

## Notes
- The program uses `pip download --no-deps`, so dependencies are not downloaded automatically
- To get dependencies, use the `-r` option to create a file. requirements.txt
- It is recommended to use virtual environments for packet isolation

## Update
```shell
# Update check (automatic at startup)
ppd --version

# Manual update
pip install --upgrade python-package-downloader
# Or
ppd --upgrade
```

## Exit codes
- `0` — successful completion
- `1` — error during execution 
- `2` — help is called (when running without arguments)

<a id="ru-doc"></a>
# Python Package Downloader (PPD) - Документация
#### [Documentation in English](#en-doc)

## Описание
**Python Package Downloader (PPD)** — это инструмент командной строки для удобной загрузки и распаковки Python пакетов в виде `.whl` файлов с возможностью автоматического извлечения и управления зависимостями.

## Установка
```shell
pip install python-package-downloader
```

После установки доступны три команды для запуска:
- `ppd` (рекомендуется)
- `python-package-downloader`
- `python_package_downloader`

## Основное использование
### Базовый синтаксис
```shell
ppd <пакет1> <пакет2> ... [опции]
```

### Примеры
```shell
# Загрузка и распаковка одного пакета
ppd requests

# Загрузка нескольких пакетов
ppd numpy pandas matplotlib

# Загрузка в указанную директорию
ppd requests --directory ./my_packages

# Сохранение .whl файлов после распаковки
ppd flask --save-wheel

# Сохранение .dist-info директорий
ppd django --save-dist-info
```

## Опции командной строки
### Обязательные аргументы
- `packages` — один или несколько пакетов для загрузки (позиционный аргумент)

### Основные опции
| Опция                                         | Короткая версия | Описание                                      |
|-----------------------------------------------|-----------------|-----------------------------------------------|
| `--version`, `-v`                             | `-v`            | Показать версию программы                     |
| `--directory`, `-d`                           | `-d <путь>`     | Директория для загрузки и распаковки пакетов  |
| `--save-wheel`, `-w`                          | `-w`            | Сохранить .whl файлы после распаковки         |
| `--save-dist-info`, `-i`                      | `-i`            | Сохранить .dist-info директории               |
| `--requirements-file`, `--requirements`, `-r` | `-r [путь]`     | Создать файл requirements.txt с зависимостями |

### Управление выводом (логированием)
| Опция                                                                              | Короткая версия | Значения                                                                                | Описание                   |
|------------------------------------------------------------------------------------|-----------------|-----------------------------------------------------------------------------------------|----------------------------|
| `--logging-level`, `--log-level`, `--loglevel`, `--log`, `--verbosity`, `-l`, `-V` | `-l`, `-V`      | `0-7` или `silent`, `critical`, `error`, `warning`, `info`, `verbose`, `debug`, `silly` | Уровень детализации вывода |

#### Уровни логирования:
- `0` / `silent` — полностью тихий режим
- `1` / `critical` — только критические ошибки
- `2` / `error` — ошибки
- `3` / `warning` — предупреждения
- `4` / `info` — обычная информация (по умолчанию)
- `5` / `verbose` — подробная информация
- `6` / `debug` — отладочная информация
- `7` / `silly` — максимальная детализация

## Детальное описание функциональности
### Процесс работы
1. **Загрузка пакетов:** Программа использует `pip download` для загрузки `.whl` файлов без зависимостей
2. **Распаковка:** Автоматически извлекает содержимое `.whl` файлов
3. **Очистка:** По умолчанию удаляет `.whl` файлы и `.dist-info` директории после распаковки
4. **Управление зависимостями:** Может создать файл `requirements.txt` с зависимостями пакетов

### Особенности
- **Автоматическое определение Python:** Находит доступный интерпретатор Python в системе
- **Обработка ошибок:** Различные уровни отображения ошибок в зависимости от уровня логирования
- **Цветной вывод:** Использует цветное форматирование для лучшей читаемости
- **Проверка обновлений:** Автоматически проверяет наличие новых версий

### Файлы и директории
По умолчанию программа:
1. Загружает `.whl` файлы в текущую директорию (или указанную через `-d`)
2. Распаковывает их в ту же директорию
3. Удаляет `.whl` файлы (если не указан `--save-wheel`)
4. Удаляет `.dist-info` директории (если не указан `--save-dist-info`)
5. Создает `requirements.txt` с зависимостями (если указан `-r`)

## Примеры использования
### Пример 1: Загрузка пакета для офлайн-установки
```shell
# Загрузить пакет в текущую директорию
ppd requests

# Результат:
# - Директория requests/ с содержимым пакета
# - Файлы пакета готовы для использования
```

### Пример 2: Создание портативной библиотеки
```shell
# Создать директорию с несколькими пакетами
ppd numpy pandas matplotlib --directory ./data_science_packages

# Сохранить информацию о зависимостях
ppd numpy pandas matplotlib -r ./requirements.txt
```

### Пример 3: Тихий режим для скриптов
```shell
# Минимальный вывод, только ошибки
ppd some-package --log-level silent
# или
ppd some-package -l 0
```

### Пример 4: Отладка проблем
```shell
# Максимально подробный вывод
ppd problematic-package --log-level silly
# или
ppd problematic-package -l 7
```

## Требования
- Python >= 3.10
- Доступ к интернету для загрузки пакетов
- Установленный `pip` в системе

## Разрешения
- MIT License
- Кроссплатформенный (Windows, Linux, macOS)

## Поддержка и обратная связь
- Автор: Маг Ильяс DOMA (MagIlyasDOMA)
- Email: magilyas.doma.09@list.ru
- GitHub: [https://github.com/MagIlyasDOMA/python-package-downloader](https://github.com/MagIlyasDOMA/python-package-downloader)
- PyPI: [https://pypi.org/project/python-package-downloader/](https://pypi.org/project/python-package-downloader/)

## Примечания
- Программа использует `pip download --no-deps`, поэтому зависимости не загружаются автоматически
- Для получения зависимостей используйте опцию `-r` для создания файла requirements.txt
- Рекомендуется использовать виртуальные окружения для изоляции пакетов

## Обновление
```shell
# Проверка обновлений (автоматическая при запуске)
ppd --version

# Ручное обновление
pip install --upgrade python-package-downloader
# Или
ppd --upgrade
```

## Коды выхода
- `0` — успешное выполнение
- `1` — ошибка при выполнении 
- `2` — вызвана справка (при запуске без аргументов)

