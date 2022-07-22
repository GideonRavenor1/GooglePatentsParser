import re
import sys
import threading
import time
from datetime import datetime
from typing import List, Callable

from general_classes.enums import DirTypeEnum, FileTypeEnum
from general_classes.file_services import MakeDirManager, XlsxFileWriter, LinksJsonFileReader
from general_classes.logger import Message
from thread_patents_parser.file_services import LinksJsonFileWriter
from thread_patents_parser.functions_performed import (
    divide_into_parts, RESULT_ARRAY, validate_urls, collect_inventors_links,
    collect_patents_inventors_links, collect_main_links, collect_patent,
)

MAIN_JSON: str = FileTypeEnum.MAIN_JSON.value
INVENTORS_JSON: str = FileTypeEnum.INVENTORS_JSON.value
PATENTS_JSON: str = FileTypeEnum.PATENTS_JSON.value
TEMP_DIR: str = DirTypeEnum.TEMP_DIR.value
LINKS_DIR: str = DirTypeEnum.LINKS_DIR.value
RESULT_DIR: str = DirTypeEnum.RESULT_DIR.value

DEFAULT_THREADS_COUNT = 8
DEFAULT_KEYWORD_COUNT = 10
REQUIRED_WORD = "assignee"


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
        'Введите поисковый запрос формата "((((H04L9)) OR (crypt))) '
        f'{REQUIRED_WORD}:raytheon country:US language:ENGLISH)": '
    ).strip()
    keyword = input('Введите ключевое слово для поиска на странице: ')
    min_keyword_count = input(
        f'Введите мин.количество ключевых слов на странице(по умолчанию {DEFAULT_KEYWORD_COUNT}): '
    )

    if REQUIRED_WORD not in request:
        Message.error_message(f"Неверный формат поискового запроса. Слово {REQUIRED_WORD} в запросе обязательно.")
        sys.exit()

    split_params = request.split(REQUIRED_WORD)
    request_params_before = split_params[0].strip().replace(" ", "+")
    request_params_after = split_params[1].strip().split(" ", maxsplit=1)[1].replace(" ", "+")
    classifications_code = re.search(r'[^(][a-zA-Z\d]+[^)]', request_params_before)

    if not classifications_code:
        Message.error_message("Неверный формат поискового запроса. Не найден код классификатора")
        sys.exit()

    threads_count = input(f'Введите желаемое количество потоков(по умолчанию {DEFAULT_THREADS_COUNT}): ')
    result_zip_file_name = input('Введите желаемое название архива с результатом: ')

    start_time = datetime.now()

    DEFAULT_THREADS_COUNT = int(threads_count) if threads_count.isdigit() else DEFAULT_THREADS_COUNT
    DEFAULT_KEYWORD_COUNT = int(min_keyword_count) if min_keyword_count.isdigit() else DEFAULT_KEYWORD_COUNT
    valid_classifications_code = classifications_code.group(0)
    Message.info_message(f'Код классификатора: {valid_classifications_code}')
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

        main_links = LinksJsonFileReader.parse_file(path_to_links=path_to_main_links)
        execute_threading_command(
            collect_inventors_links,
            main_links,
            request_params_before,
            request_params_after,
            path_to_chrome_driver,
        )
        valid_urls = validate_urls(array=RESULT_ARRAY)
        path_to_inventors_links = LinksJsonFileWriter.write_links_to_file(
            file_name=INVENTORS_JSON,
            data=valid_urls,
            directory=links_dir
        )
        RESULT_ARRAY.clear()
        time.sleep(10)

        inventors_links = LinksJsonFileReader.parse_file(path_to_links=path_to_inventors_links)
        execute_threading_command(collect_patents_inventors_links, inventors_links, path_to_chrome_driver)
        path_to_json_links = LinksJsonFileWriter.write_links_to_file(
            file_name=PATENTS_JSON,
            data=RESULT_ARRAY,
            directory=links_dir,
        )
        Message.info_message(f'Общее количество элементов: {len(RESULT_ARRAY)}')
        RESULT_ARRAY.clear()
        time.sleep(10)

        patents_links = LinksJsonFileReader.parse_file(path_to_links=path_to_json_links)
        result_dir_name = dir_manager.make_result_dir(name=RESULT_DIR)
        execute_threading_command(
            collect_patent,
            patents_links,
            path_to_chrome_driver,
            temporary_dir,
            result_dir_name,
            valid_classifications_code,
            keyword,
            DEFAULT_KEYWORD_COUNT,
        )

        XlsxFileWriter.delete_empty_directory(dir_name=RESULT_DIR)
        time.sleep(5)
        XlsxFileWriter.zipped_files(dir_name=RESULT_DIR, zip_file_name=result_zip_file_name)
    except (FileNotFoundError, KeyError, IndexError, TypeError) as Error:
        Message.error_message(f"Ошибка в работе программы. Ошибка: {Error}.")
    finally:
        execution_time = datetime.now() - start_time
        Message.info_message(f"Время выполнения: {execution_time}")
        Message.success_message("============== Завершение работы программы. ==============")
