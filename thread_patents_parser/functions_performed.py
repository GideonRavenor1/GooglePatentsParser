import threading
from math import ceil
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from general_classes.file_services import MakeDirManager, XlsxFileWriter
from general_classes.logger import Message
from thread_patents_parser.file_services import LinksFileWriter
from thread_patents_parser.inventors_links_parser import SeleniumInventorsLinksParser
from thread_patents_parser.main_links_parser import SeleniumMainLinksParser
from thread_patents_parser.patents_links_parser import SeleniumPatentsInventorsLinksParser, SeleniumPatentsParser

RESULT_ARRAY = []
LOCK = threading.Lock()


def validate_urls(array: List) -> List:
    Message.info_message(f'Общее количество ссылок: {len(array)}')
    seen_links = {}
    validate_links = [
        seen_links.setdefault(link.lower(), link) for link in array if link.lower() not in seen_links
    ]
    Message.info_message(f'Общее количество уникальных ссылок: {len(validate_links)}')
    return validate_links


def init_settings(temp_dir: str) -> Options:
    prefs = {
        "download.default_directory": temp_dir,
    }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options


def init_service(path_to_driver: str) -> Service:
    chrome_service = Service(executable_path=path_to_driver)
    return chrome_service


def divide_into_parts(array: List, parts: int) -> List[List]:
    part_len = ceil(len(array) / parts)
    return [array[part_len * part:part_len * (part + 1)] for part in range(parts)]


def collect_main_links(path_to_chrome_driver: str, request: str, directory: str, file_name: str) -> str:
    name = threading.current_thread().name
    Message.info_message(f"[{name}] Сбор основных ссылок...")
    service = init_service(path_to_driver=path_to_chrome_driver)
    chrome = webdriver.Chrome(service=service)
    parser = SeleniumMainLinksParser(driver=chrome, request=request, thread_name=name)
    links_list = parser.collect_links()
    path_to_main_links = LinksFileWriter.write_links_to_txt_file(
        file_name=file_name,
        data=links_list,
        directory=directory,
    )
    Message.success_message(f"[{name}] Сбор основных ссылок завершен.")
    parser.close_browser()
    return path_to_main_links


def collect_inventors_links(links: List[str], request_params: str, path_to_chrome_driver: str) -> None:
    name = threading.current_thread().name
    Message.info_message(f'[{name}] - Сбор ссылок авторов...')
    service = init_service(path_to_driver=path_to_chrome_driver)
    chrome = webdriver.Chrome(service=service)
    parser = SeleniumInventorsLinksParser(driver=chrome, request_param=request_params, thread_name=name)
    parser.set_links(links=links)
    Message.success_message(f'[{name}] - Сбор ссылок авторов завершен.')
    result = parser.collect_links()
    LOCK.acquire()
    RESULT_ARRAY.extend(result)
    LOCK.release()
    parser.close_browser()


def collect_patents_inventors_links(links: List[str], path_to_chrome_driver: str) -> None:
    name = threading.current_thread().name
    Message.info_message(f'[{name}] - Сбор ссылок патентов авторов...')
    service = init_service(path_to_driver=path_to_chrome_driver)
    chrome = webdriver.Chrome(service=service)
    parser = SeleniumPatentsInventorsLinksParser(driver=chrome, thread_name=name)
    parser.set_links(links=links)
    Message.success_message(f'[{name}] - Сбор ссылок патентов авторов завершен.')
    result = parser.collect_links()
    LOCK.acquire()
    RESULT_ARRAY.extend(result)
    LOCK.release()
    parser.close_browser()


def collect_patent(links: List[Dict], path_to_chrome_driver: str, tmp_dir: str, directory: str) -> None:
    name = threading.current_thread().name
    Message.info_message(f'[{name}] - Сбор патентов автора...')
    service = init_service(path_to_driver=path_to_chrome_driver)
    options = init_settings(temp_dir=tmp_dir)
    chrome = webdriver.Chrome(service=service, options=options)
    parser = SeleniumPatentsParser(driver=chrome, thread_name=name, tmp_dir=tmp_dir)
    patents_links_len = len(links)
    for element in links:
        dir_name = element["name"]
        links = element["links"]
        parser.set_links(links=links)
        dir_author, dir_patent = MakeDirManager.make_author_dirs(
            name=dir_name, directory=directory
        )
        Message.info_message(f"Осталось авторов: {patents_links_len}")
        Message.info_message(f"Текущий автор: {dir_name}")
        parser.parse_patents_links(patent_dir=dir_patent)
        state = parser.get_state()
        writer = XlsxFileWriter(directory=dir_author, state=state)
        writer.execute_write()
        patents_links_len -= 1
    Message.success_message(f'[{name}] - Сбор патентов авторов завершен.')
