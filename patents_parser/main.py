import json
import os
import time
from typing import Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from file_services import (
    XlsxFileWriter,
    LinksFileWriter,
    LinksFileReader,
    MakeDirManager,
)
from logger import Message
from selenium_multiparser import SeleniumMultiParser
from enums import DirTypeEnum, FileTypeEnum

MAIN_TXT = FileTypeEnum.MAIN_TXT.value
INVENTORS_TXT = FileTypeEnum.INVENTORS_TXT.value
INVENTORS_JSON = FileTypeEnum.INVENTORS_JSON.value
TEMP_DIR = DirTypeEnum.TEMP_DIR.value
LINKS_DIR = DirTypeEnum.LINKS_DIR.value
RESULT_DIR = DirTypeEnum.RESULT_DIR.value


def init_settings(temp_dir: str) -> Options:
    prefs = {
        "download.default_directory": temp_dir,
    }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options


if __name__ == "__main__":
    # request = input('Введите поисковый запрос: ').strip()
    dir_manager = MakeDirManager()
    temporary_dir = dir_manager.make_temp_browser_dir(directory=TEMP_DIR)
    options = init_settings(temp_dir=temporary_dir)
    chrome = webdriver.Chrome(options=options)
    parser = SeleniumMultiParser(
        driver=chrome, tmp_dir=temporary_dir, request="request"
    )
    links_dir = dir_manager.make_link_dir(name=LINKS_DIR)
    writer = LinksFileWriter(directory=links_dir)
    reader = LinksFileReader()
    try:
        # set_main_links = parser.collect_main_links()
        # path_to_main_links = writer.write_links_to_txt_file(file_name=MAIN_TXT, data=set_main_links)
        # time.sleep(10)
        # main_links = reader.parse_txt_file(path_to_links=path_to_main_links)
        # parser.set_links(links=main_links)
        # set_inventors_links = parser.collect_inventors_links()
        # path_to_inventors_links = writer.write_links_to_txt_file(file_name=INVENTORS_TXT, data=set_inventors_links)
        # time.sleep(10)
        # inventors_links = reader.parse_txt_file(path_to_links=path_to_inventors_links)
        # parser.set_links(links=inventors_links)
        # list_patents_links = parser.collect_patents_inventors_links()
        # path_to_json_links = writer.write_links_to_json_file(file_name=INVENTORS_JSON, data=list_patents_links)
        # time.sleep(10)
        patents_links = reader.parse_json_file(path_to_links="links/inventors.json")
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
        writer.zipped_files(dir_name=RESULT_DIR)
    except FileExistsError as Error:
        Message.error_message(f"XXX Ошибка в работе программы. Ошибка: {Error}. XXX")
    finally:
        parser.close_browser()
        Message.success_message(
            "============== Завершение работы программы. =============="
        )
