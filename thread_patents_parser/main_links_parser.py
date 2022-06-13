from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from general_classes.enums import SearchItems
from general_classes.logger import Message
from thread_patents_parser.base import SeleniumLinksParser


class SeleniumMainLinksParser(SeleniumLinksParser):

    def __init__(self, driver: webdriver.Chrome, request: str, thread_name: str) -> None:
        super().__init__(driver, thread_name)
        self._request = request
        self._main_links_list = []

    def collect_links(self) -> List:
        self._follow_the_link(link=self.BASE_URL)
        self._fill_form(request=self._request)
        if not self._check_result():
            raise ValueError(f"[{self._thread_name}] Ошибка. Результатов по введённому запросу не найдено")
        self._add_links_to_list(list_=self._main_links_list, all_result=True)
        valid_links = self._links_converter(data=self._main_links_list)
        return valid_links

    def _fill_form(self, request: str) -> None:
        form = self._driver.find_element(
            by=By.XPATH, value=SearchItems.search_form.value
        )
        form.send_keys(request)
        form.send_keys(Keys.ENTER)
        Message.info_message(f"[{self._thread_name}] Ввод запроса в форму...")

    def _links_converter(self, data: List) -> List:
        Message.info_message(f"[{self._thread_name}] Конвертация {len(data)} ссылок..")
        list_link = list({urljoin(base=self.BASE_URL, url=url) for url in data})
        Message.info_message(f"[{self._thread_name}] Всего уникальных ссылок: {len(list_link)}")
        return list_link
