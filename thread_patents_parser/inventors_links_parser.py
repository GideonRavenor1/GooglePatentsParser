import time
from random import randint
from typing import List, Dict
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from general_classes.enums import XpathRightPartElements, UniqueNames
from general_classes.logger import Message
from thread_patents_parser.base import SeleniumLinksParser


class SeleniumInventorsLinksParser(SeleniumLinksParser):

    def __init__(self, driver: webdriver.Chrome, request_params_before: str, request_params_after: str) -> None:
        super().__init__(driver)
        self._inventors_links_list = []
        self._request_params_before = request_params_before
        self._request_params_after = request_params_after.replace(",", "%2C")

    def collect_links(self) -> List:
        len_inventors_links = len(self._links)
        for element in self._links:
            link = element["link"]
            Message.info_message(f"Осталось спарсить ссылок: {len_inventors_links}")
            Message.info_message(f"Текущая ссылка: {link}")
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
            Message.warning_message(f"Секция people_section не найдена. URL: {link}")
        else:
            self._get_inventors_links(people_section=people_section, link=link)

    def _get_inventors_links(self, people_section: List[WebElement], link: str) -> None:
        inventors = []
        for element in people_section:
            if self._check_inventor_element(element=element):
                name = element.text
                inv_name = name.replace(",", "%2C").replace(" ", "+")
                query = (
                    f"?q={self._request_params_before}&inventor={inv_name}&{self._request_params_after}"
                    f"&oq={self._request_params_before}+inventor:({inv_name})+{self._request_params_after})"
                )
                inventors.append({"name": name.replace(" ", "_"), "query": query})
                Message.info_message(f"Сгенерированный Query-запрос: {query}")
        if not inventors:
            Message.warning_message(f"Авторы не найдены. Query-запросы не сгенерированы. URL: {link}")
        else:
            self._inventors_links_list.extend(inventors)
            Message.success_message("Сгенерированные Query-запросы с авторами добавлены в буфер.")

    def _links_converter(self, data: List[Dict]) -> List[Dict]:
        Message.info_message(f"Конвертация {len(data)} ссылок..")
        list_link = [
            {"name": element["name"], "link": urljoin(base=self.BASE_URL, url=element["query"])}
            for element in data
        ]
        Message.info_message(f"Всего ссылок: {len(data)}")
        return list_link

    @staticmethod
    def _check_inventor_element(element: WebElement) -> bool:
        type_act = element.get_attribute("act")
        if UniqueNames.INVENTOR.value.lower() in type_act:
            return True
        return False
