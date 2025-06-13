import os
import sys


def print_directory_tree(start_path):
    """
    Выводит дерево файлов и папок с иерархией, игнорируя __pycache__ и .venv
    :param start_path: Начальная директория для обхода
    """
    # Папки, которые нужно игнорировать
    IGNORE_DIRS = {'__pycache__', '.venv'}

    for root, dirs, files in os.walk(start_path):
        # Фильтруем игнорируемые директории (удаляем их из списка для обхода)
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        level = root.replace(start_path, '').count(os.sep)
        indent = '│   ' * (level - 1) + '├── ' if level > 0 else ''

        # Форматируем вывод текущей папки
        dir_basename = os.path.basename(root)
        # Пропускаем вывод корневой папки, если она в списке игнорируемых
        if level == 0 or dir_basename not in IGNORE_DIRS:
            dir_display = f'{indent}📁 {dir_basename}/' if dir_basename else f'{indent}📁 {os.path.abspath(root)}'
            print(dir_display)
        else:
            continue

        # Выводим файлы в текущей папке
        sub_indent = '│   ' * level + '├── '
        for i, f in enumerate(sorted(files)):
            # Для последнего файла в списке меняем префикс
            prefix = '└── ' if i == len(files) - 1 else '├── '
            file_prefix = '│   ' * level + prefix
            print(f"{file_prefix}📄 {f}")


if __name__ == "__main__":
    # Определяем стартовую директорию
    start_dir = sys.argv[1] if len(sys.argv) > 1 else '.'

    # Проверяем существование пути
    if not os.path.exists(start_dir):
        print(f"Ошибка: Путь '{start_dir}' не существует!")
        sys.exit(1)

    # Проверяем, что путь ведет к директории
    if not os.path.isdir(start_dir):
        print(f"Ошибка: '{start_dir}' не является директорией!")
        sys.exit(1)

    print(f"\nДерево каталогов для: {os.path.abspath(start_dir)}")
    print("Игнорируются папки: __pycache__, .venv\n")
    print_directory_tree(start_dir)
    print("\n" + "═" * 50)