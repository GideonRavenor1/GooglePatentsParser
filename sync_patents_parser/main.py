import re
import sys
import time
from datetime import datetime
from typing import Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from general_classes.enums import DirTypeEnum, FileTypeEnum
from general_classes.file_services import MakeDirManager, XlsxFileWriter, LinksFileReader
from general_classes.logger import Message
from sync_patents_parser.file_services import LinksFileWriter
from sync_patents_parser.selenium_multiparser import SeleniumMultiParser

MAIN_TXT = FileTypeEnum.MAIN_TXT.value
INVENTORS_TXT = FileTypeEnum.INVENTORS_TXT.value
INVENTORS_JSON = FileTypeEnum.INVENTORS_JSON.value
TEMP_DIR = DirTypeEnum.TEMP_DIR.value
LINKS_DIR = DirTypeEnum.LINKS_DIR.value
RESULT_DIR = DirTypeEnum.RESULT_DIR.value

DEFAULT_KEYWORD_COUNT = 10
REQUIRED_WORD = "assignee"


def init_settings(temp_dir: str, path_to_driver: str) -> Tuple[Options, Service]:
    prefs = {
        "download.default_directory": temp_dir,
    }
    chrome_options = webdriver.ChromeOptions()
    chrome_service = Service(executable_path=path_to_driver)
    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options, chrome_service


if __name__ == "__main__":
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

    request_params = request.split("assignee")[0].strip().replace(" ", "+")
    classifications_code = re.search(r'[^(][a-zA-Z\d]+[^)]', request_params)

    if not classifications_code:
        Message.error_message("Неверный формат поискового запроса. Не найден код классификатора")
        sys.exit()

    start_time = datetime.now()

    DEFAULT_KEYWORD_COUNT = int(min_keyword_count) if min_keyword_count.isdigit() else DEFAULT_KEYWORD_COUNT
    valid_classifications_code = classifications_code.group(0)
    Message.info_message(f'Код классификатора: {valid_classifications_code}')
    dir_manager = MakeDirManager()
    temporary_dir = dir_manager.make_temp_browser_dir(directory=TEMP_DIR)
    options, service = init_settings(temp_dir=temporary_dir, path_to_driver=path_to_chrome_driver)
    chrome = webdriver.Chrome(options=options, service=service)
    parser = SeleniumMultiParser(
        driver=chrome,
        tmp_dir=temporary_dir,
        request=request,
        request_params=request_params,
        keyword=keyword,
        min_keyword_count=DEFAULT_KEYWORD_COUNT,
        valid_classifications_code=valid_classifications_code,
    )
    links_dir = dir_manager.make_link_dir(name=LINKS_DIR)
    writer = LinksFileWriter(directory=links_dir)
    reader = LinksFileReader()

    try:
        list_main_links = parser.collect_main_links()
        path_to_main_links = writer.write_links_to_txt_file(file_name=MAIN_TXT, data=list_main_links)
        time.sleep(10)

        main_links = reader.parse_txt_file(path_to_links=path_to_main_links)
        parser.set_links(links=main_links)
        list_inventors_links = parser.collect_inventors_links()
        path_to_inventors_links = writer.write_links_to_txt_file(file_name=INVENTORS_TXT, data=list_inventors_links)
        time.sleep(10)

        inventors_links = reader.parse_txt_file(path_to_links=path_to_inventors_links)
        parser.set_links(links=inventors_links)
        list_patents_links = parser.collect_patents_inventors_links()
        path_to_json_links = writer.write_links_to_json_file(file_name=INVENTORS_JSON, data=list_patents_links)
        time.sleep(10)

        patents_links = reader.parse_json_file(path_to_links=path_to_json_links)
        patents_links_len = len(patents_links)
        directory_name = dir_manager.make_result_dir(name=RESULT_DIR)
        for element in patents_links:
            dir_name = element["name"]
            links = element["links"]
            parser.set_links(links=links)
            dir_author, dir_patent = dir_manager.make_author_dirs(
                name=dir_name, directory=directory_name
            )
            Message.info_message(f"Осталось авторов: {patents_links_len}")
            Message.info_message(f"Текущий автор: {dir_name}")
            parser.parse_patents_links(patent_dir=dir_patent)
            state = parser.get_state()
            writer = XlsxFileWriter(directory=dir_author, state=state)
            writer.execute_write()
            patents_links_len -= 1

        writer.delete_empty_directory(dir_name=RESULT_DIR)
        time.sleep(5)
        writer.zipped_files(dir_name=RESULT_DIR)
    except FileExistsError as Error:
        Message.error_message(f"XXX Ошибка в работе программы. Ошибка: {Error}. XXX")
    finally:
        execution_time = datetime.now() - start_time
        Message.info_message(f"Время выполнения: {execution_time}")
        parser.close_browser()
        Message.success_message(
            "============== Завершение работы программы. =============="
        )
