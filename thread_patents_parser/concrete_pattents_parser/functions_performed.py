from typing import List, Dict
from selenium import webdriver

from general_classes.file_services import MakeDirManager, XlsxFileWriter
from general_classes.logger import Message
from thread_patents_parser.concrete_pattents_parser.pattents_links_parser import SeleniumPatentsParser, LOCK
from thread_patents_parser.functions_performed import init_service, init_settings

RESULT_ARRAY = []


def collect_patent(
    links: List[Dict],
    path_to_chrome_driver: str,
    tmp_dir: str,
    directory: str,
    name: str,
) -> None:
    Message.info_message("Сбор патентов автора...")
    service = init_service(path_to_driver=path_to_chrome_driver)
    options = init_settings(temp_dir=tmp_dir)
    chrome = webdriver.Chrome(service=service, options=options)
    parser = SeleniumPatentsParser(
        driver=chrome,
        tmp_dir=tmp_dir,
        name=name
    )
    patents_links_len = len(links)
    for element in links:
        link = element["link"]
        parser.set_links(links=[link])
        # dir_author, dir_patent = MakeDirManager.make_author_dirs(
        #     name=name, directory=directory
        # )
        Message.info_message(f"Осталось ссылок: {patents_links_len}")
        Message.info_message(f"Текущий ссылка: {link}")
        parser.parse_patents_links(patent_dir=directory)
        state = parser.get_state()
        LOCK.acquire()
        RESULT_ARRAY.append(state)
        LOCK.release()
        patents_links_len -= 1
    Message.success_message("Сбор патентов авторов завершен.")


def write_result_to_file(name: str) -> None:
    writer = XlsxFileWriter(directory=name, state=RESULT_ARRAY)
    writer.execute_write()
