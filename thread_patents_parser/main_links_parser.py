from typing import List, Dict
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from general_classes.enums import SearchItems
from general_classes.logger import Message
from thread_patents_parser.base import SeleniumLinksParser


class SeleniumMainLinksParser(SeleniumLinksParser):

    def __init__(self, driver: webdriver.Chrome, request: str) -> None:
        super().__init__(driver)
        self._request = request
        self._main_links_list = []

    def collect_links(self) -> List[Dict]:
        self._follow_the_link(link=self.BASE_URL)
        self._fill_form(request=self._request)
        if not self._check_result():
            raise ValueError("Ошибка. Результатов по введённому запросу не найдено")
        self._add_links_to_list(list_=self._main_links_list, all_result=True)
        valid_links = self._links_converter(data=self._main_links_list)
        return valid_links

    def _fill_form(self, request: str) -> None:
        form = self._driver.find_element(
            by=By.XPATH, value=SearchItems.search_form.value
        )
        form.send_keys(request)
        form.send_keys(Keys.ENTER)
        Message.info_message("Ввод запроса в форму...")

    def _links_converter(self, data: List[Dict]) -> List[Dict]:
        Message.info_message(f"Конвертация основных ссылок: {len(data)}")
        seen_links = set()
        list_link = []
        for element in data:
            link = element["link"]
            if link not in seen_links:
                seen_links.add(link)
                list_link.append({"link": urljoin(base=self.BASE_URL, url=element["link"])})
        Message.info_message(f"Всего уникальных ссылок: {len(list_link)}")
        return list_link
