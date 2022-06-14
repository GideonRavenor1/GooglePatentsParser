import time
from random import randint
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from general_classes.enums import XpathRightPartElements, UniqueNames
from general_classes.logger import Message
from thread_patents_parser.base import SeleniumLinksParser


class SeleniumInventorsLinksParser(SeleniumLinksParser):

    def __init__(self, driver: webdriver.Chrome, request_param: str, thread_name: str) -> None:
        super().__init__(driver, thread_name)
        self._inventors_links_list = []
        self._request_params = request_param

    def collect_links(self) -> List:
        len_inventors_links = len(self._links)
        for link in self._links:
            Message.info_message(f"[{self._thread_name}] Осталось спарсить ссылок: {len_inventors_links}")
            Message.info_message(f"[{self._thread_name}] Текущая ссылка: {link}")
            self._follow_the_link(link=link)
            self._find_inventors_links(link=link)
            if len_inventors_links % 10 == 0:
                time.sleep(randint(5, 10))
            len_inventors_links -= 1
        valid_links = self._links_converter(data=self._inventors_links_list)
        return valid_links

    def _find_inventors_links(self, link: str) -> None:
        people_section = self._driver.find_elements(
            by=By.XPATH, value=XpathRightPartElements.inventors_link.value
        )
        if not people_section:
            Message.warning_message(f"[{self._thread_name}] Секция people_section не найдена. URL: {link}")
        else:
            self._get_inventors_links(people_section=people_section, link=link)

    def _get_inventors_links(self, people_section: List[WebElement], link: str) -> None:
        inventors = []
        for element in people_section:
            if self._check_inventor_element(element=element):
                inv_name = element.text.replace(",", "%2C").replace(" ", "+")
                query = (
                    f"?q={self._request_params}&inventor={inv_name}&oq={self._request_params}+inventor:({inv_name}))"
                )
                inventors.append(query)
                Message.info_message(f"[{self._thread_name}] Сгенерированный Query-запрос: {query}")
        if not inventors:
            Message.warning_message(
                f"[{self._thread_name}] Авторы не найдены. Query-запросы не сгенерированы. URL: {link}")
        else:
            self._inventors_links_list.extend(inventors)
            Message.success_message(f"[{self._thread_name}] Сгенерированные Query-запросы с авторами добавлены в "
                                    "буфер.")

    def _links_converter(self, data: List) -> List:
        Message.info_message(f"[{self._thread_name}] Конвертация {len(data)} ссылок..")
        list_link = [urljoin(base=self.BASE_URL, url=url) for url in data]
        Message.info_message(f"[{self._thread_name}] Всего ссылок: {len(data)}")
        return list_link

    @staticmethod
    def _check_inventor_element(element: WebElement) -> bool:
        type_act = element.get_attribute("act")
        if UniqueNames.INVENTOR.value.lower() in type_act:
            return True
        return False
