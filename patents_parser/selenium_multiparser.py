import random
import time
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webelement import WebElement

from type_annotations import JsonDict
from selenium_parser import SeleniumParser
from logger import Message
from enums import XpathRightPartElements, SearchItems, UniqueNames


class SeleniumMultiParser(SeleniumParser):
    BASE_URL = "https://patents.google.com/"

    def __init__(self, request: str, driver: webdriver.Chrome, tmp_dir: str) -> None:
        super().__init__(driver, tmp_dir)
        self._request = request
        self._request_params = request.split("assignee")[0].strip().replace(" ", "+")
        self._main_links_list = []
        self._inventors_links_list = []
        self._json_element = JsonDict()
        self._patents_links_list = []

    def collect_main_links(self) -> List:
        self._follow_the_link(link=self.BASE_URL)
        self._fill_form(request=self._request)
        if not self._check_result():
            raise ValueError("Ошибка. Результатов по введённому запросу не найдено")
        self._add_links_to_list(list_=self._main_links_list)
        valid_links = self._links_converter(data=self._main_links_list)
        self._main_links_list.clear()
        return valid_links

    def collect_inventors_links(self) -> List:
        len_inventors_links = len(self._links)
        for link in self._links:
            Message.info_message(f"Осталось спарсить ссылок: {len_inventors_links}")
            Message.info_message(f"Текущая ссылка: {link}")
            self._follow_the_link(link=link)
            self._find_inventors_links(link=link)
            if len_inventors_links % 10 == 0:
                time.sleep(random.randint(5, 10))
            len_inventors_links -= 1
        valid_links = self._links_converter(data=self._inventors_links_list, case_ignore=True)
        self._inventors_links_list.clear()
        return valid_links

    def collect_patents_inventors_links(self) -> List[JsonDict]:
        len_patents_links = len(self._links)
        for link in self._links:
            Message.info_message(f"Осталось спарсить ссылок: {len_patents_links}")
            Message.info_message(f"Текущая ссылка: {link}")
            self._follow_the_link(link=link)
            inventor = (
                link.split("inventor")[2]
                .strip(":()")
                .replace("+", "_")
                .replace("%2C", "")
            )
            len_patents_links -= 1
            if not self._check_result():
                Message.warning_message(f"Патенты у автора {inventor} не найдена")
                continue
            self._json_element["name"] = inventor
            self._json_element["links"] = []
            self._add_links_to_list(list_=self._json_element["links"])
            valid_links = self._links_converter(data=self._json_element["links"])
            self._json_element["links"] = valid_links
            copy_element = self._json_element.copy()
            self._patents_links_list.append(copy_element)
        return self._patents_links_list

    def _fill_form(self, request: str) -> None:
        form = self._driver.find_element(
            by=By.XPATH, value=SearchItems.search_form.value
        )
        form.send_keys(request)
        form.send_keys(Keys.ENTER)
        Message.info_message("Ввод запроса в форму...")

    def _add_links_to_list(self, list_: List) -> None:
        links_number = self._find_total_items_result()
        self._add_more_result_per_page()
        Message.info_message(f"Всего результатов на странице: {links_number}")
        total_added = 0
        while total_added < links_number:
            time.sleep(1)
            links_elements = self._driver.find_elements(
                by=By.XPATH, value=SearchItems.result_items.value
            )
            links_to_str = [
                element.get_attribute("data-result") for element in links_elements
            ]
            len_links_to_str = len(links_to_str)
            total_added += len_links_to_str
            Message.info_message(f"Добавлено ссылок: {len_links_to_str}. Всего добавлено: {total_added}")
            list_.extend(links_to_str)
            self._click_to_next_button(xpath=SearchItems.next_button.value)

    def _find_total_items_result(self) -> int:
        try:
            result = self._driver.find_element(
                by=By.XPATH, value=SearchItems.num_result.value
            )
        except NoSuchElementException:
            Message.warning_message('Элемент "Всего результатов" не найден')
            result = "0"
        res_number = list(filter(lambda x: x.isdigit(), result.text.split()))
        return int(res_number[0])

    def _add_more_result_per_page(self) -> None:
        more_result_button = self._driver.find_element(by=By.XPATH, value=SearchItems.result_in_page_button.value)
        self._driver.execute_script("arguments[0].click();", more_result_button)
        max_result_button = self._driver.find_element(by=By.XPATH, value=SearchItems.one_hundred_results_per_page.value)
        self._driver.execute_script("arguments[0].click();", max_result_button)

    def _links_converter(self, data: List, case_ignore: bool = False) -> List:
        Message.info_message(f"Конвертация {len(data)} ссылок..")
        if case_ignore:
            seen_links = {}
            validate_links = [
                seen_links.setdefault(link.lower(), link) for link in data if link.lower() not in seen_links
            ]
            list_link = [urljoin(base=self.BASE_URL, url=url) for url in validate_links]
        else:
            list_link = list({urljoin(base=self.BASE_URL, url=url) for url in data})
        Message.info_message(f"Всего уникальных ссылок: {len(list_link)}")
        return list_link

    def _check_result(self) -> bool:
        try:
            self._driver.find_element(
                by=By.XPATH, value=SearchItems.no_result_message.value
            )
            return False
        except NoSuchElementException:
            return True

    def _click_to_next_button(self, xpath: str) -> None:
        try:
            button = WebDriverWait(self._driver, 5).until(
                ec.element_to_be_clickable((By.XPATH, xpath))
            )
            button.click()
            Message.info_message("Переход на следующую страницу...")
        except TimeoutException:
            Message.warning_message('Кнопка "следующая страница" не найдена.')
            ...

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
                inv_name = element.text.replace(",", "%2C").replace(" ", "+")
                query = (
                    f"?q={self._request_params}&inventor={inv_name}&oq={self._request_params}+inventor:({inv_name}))"
                )
                inventors.append(query)
                Message.info_message(f"Сгенерированный Query-запрос: {query}")
        if not inventors:
            Message.warning_message(f"Авторы не найдены. Query-запросы не сгенерированы. URL: {link}")
        else:
            self._inventors_links_list.extend(inventors)
            Message.success_message("Сгенерированные Query-запросы с авторами добавлены в буфер.")

    @staticmethod
    def _check_inventor_element(element: WebElement) -> bool:
        type_act = element.get_attribute("act")
        if UniqueNames.INVENTOR.value.lower() in type_act:
            return True
        return False
