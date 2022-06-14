import sys
import threading
import time
from datetime import datetime
from typing import List, Callable

from general_classes.enums import DirTypeEnum, FileTypeEnum
from general_classes.file_services import MakeDirManager, XlsxFileWriter, LinksFileReader
from general_classes.logger import Message
from thread_patents_parser.file_services import LinksFileWriter
from thread_patents_parser.functions_performed import (
    divide_into_parts, RESULT_ARRAY, validate_urls, collect_inventors_links,
    collect_patents_inventors_links, collect_main_links, collect_patent,
)

MAIN_TXT = FileTypeEnum.MAIN_TXT.value
INVENTORS_TXT = FileTypeEnum.INVENTORS_TXT.value
INVENTORS_JSON = FileTypeEnum.INVENTORS_JSON.value
TEMP_DIR = DirTypeEnum.TEMP_DIR.value
LINKS_DIR = DirTypeEnum.LINKS_DIR.value
RESULT_DIR = DirTypeEnum.RESULT_DIR.value

DEFAULT_THREADS_COUNT = 8


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
    request = input(
        'Введите поисковый запрос формата "((((H04L9)) OR (crypt))) assignee:raytheon country:US language:ENGLISH)": '
    ).strip()
    threads_count = input(f'Введите желаемое количество потоков(по умолчанию {DEFAULT_THREADS_COUNT}): ')
    DEFAULT_THREADS_COUNT = int(threads_count) if threads_count.isdigit() else DEFAULT_THREADS_COUNT
    start_time = datetime.now()
    request_params = request.split("assignee")[0].strip().replace(" ", "+")
    dir_manager = MakeDirManager()
    try:
        links_dir = dir_manager.make_link_dir(name=LINKS_DIR)
        temporary_dir = dir_manager.make_temp_browser_dir(directory=TEMP_DIR)
        path_to_main_links = collect_main_links(
            path_to_chrome_driver=path_to_chrome_driver,
            request=request,
            directory=links_dir,
            file_name=MAIN_TXT
        )
        time.sleep(10)

        main_links = LinksFileReader.parse_txt_file(path_to_links=path_to_main_links)
        execute_threading_command(collect_inventors_links, main_links, request_params, path_to_chrome_driver)
        valid_urls = validate_urls(array=RESULT_ARRAY)
        path_to_inventors_links = LinksFileWriter.write_links_to_txt_file(
            file_name=INVENTORS_TXT,
            data=valid_urls,
            directory=links_dir
        )
        RESULT_ARRAY.clear()
        time.sleep(10)

        inventors_links = LinksFileReader.parse_txt_file(path_to_links='links/inventors.txt')
        execute_threading_command(collect_patents_inventors_links, inventors_links, path_to_chrome_driver)
        path_to_json_links = LinksFileWriter.write_links_to_json_file(
            file_name=INVENTORS_JSON,
            data=RESULT_ARRAY,
            directory=links_dir,
        )
        Message.info_message(f'Общее количество элементов: {len(RESULT_ARRAY)}')
        RESULT_ARRAY.clear()
        time.sleep(10)

        patents_links = LinksFileReader.parse_json_file(path_to_links='links/inventors.json')
        result_dir_name = dir_manager.make_result_dir(name=RESULT_DIR)
        execute_threading_command(collect_patent, patents_links, path_to_chrome_driver, temporary_dir, result_dir_name)

        XlsxFileWriter.zipped_files(dir_name=RESULT_DIR)
    except (FileNotFoundError, KeyError, IndexError, TypeError) as Error:
        Message.error_message(f"XXX Ошибка в работе программы. Ошибка: {Error}. XXX")
    finally:
        execution_time = datetime.now() - start_time
        Message.info_message(f"Время выполнения: {execution_time}")
        Message.success_message(
            "============== Завершение работы программы. =============="
        )
        sys.exit()
