import threading
import time
from datetime import datetime
from typing import List, Callable

from general_classes.file_services import MakeDirManager, XlsxFileWriter, LinksJsonFileReader
from general_classes.logger import Message
from thread_patents_parser.concrete_pattents_parser.functions_performed import collect_patent, write_result_to_file
from thread_patents_parser.functions_performed import divide_into_parts, collect_main_links
from thread_patents_parser.main import DEFAULT_THREADS_COUNT, LINKS_DIR, TEMP_DIR, RESULT_DIR, MAIN_JSON


def execute_threading_command(target_func: Callable, links: List,  *args) -> None:
    parts = divide_into_parts(array=links, parts=DEFAULT_THREADS_COUNT)
    threads = []
    for number in range(DEFAULT_THREADS_COUNT):
        thread = threading.Thread(
            target=target_func,
            args=(parts[number], *args),
            name=f'Thread {number + 1}'
        )
        thread.start()
        threads.append(thread)
    Message.info_message(f'Создание {DEFAULT_THREADS_COUNT} потоков...')
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    path_to_chrome_driver = 'chromedriver'
    request = input('Введите поисковый запрос: ').strip()
    inventors_name = input('Введите имя автора паттентов: ').replace(' ', '_')
    threads_count = input(f'Введите желаемое количество потоков(по умолчанию {DEFAULT_THREADS_COUNT}): ')
    start_time = datetime.now()
    DEFAULT_THREADS_COUNT = int(threads_count) if threads_count.isdigit() else DEFAULT_THREADS_COUNT
    dir_manager = MakeDirManager()

    try:
        links_dir = dir_manager.make_link_dir(name=LINKS_DIR)
        temporary_dir = dir_manager.make_temp_browser_dir(directory=TEMP_DIR)
        path_to_main_links = collect_main_links(
            path_to_chrome_driver=path_to_chrome_driver,
            request=request,
            directory=links_dir,
            file_name=MAIN_JSON
        )
        time.sleep(10)

        patents_links = LinksJsonFileReader.parse_file(path_to_links=path_to_main_links)
        result_dir_name = dir_manager.make_result_dir(name=RESULT_DIR)
        dir_author, dir_patent = MakeDirManager.make_author_dirs(
            name=inventors_name, directory=result_dir_name
        )
        execute_threading_command(
            collect_patent,
            patents_links,
            path_to_chrome_driver,
            temporary_dir,
            dir_patent,
            inventors_name,
        )
        write_result_to_file(name=dir_author)
        time.sleep(5)
        XlsxFileWriter.zipped_files(dir_name=RESULT_DIR, zip_file_name=inventors_name)
    except (FileNotFoundError, KeyError, IndexError, TypeError) as Error:
        Message.error_message(f"Ошибка в работе программы. Ошибка: {Error}.")
    finally:
        execution_time = datetime.now() - start_time
        Message.info_message(f"Время выполнения: {execution_time}")
        Message.success_message("============== Завершение работы программы. ==============")
