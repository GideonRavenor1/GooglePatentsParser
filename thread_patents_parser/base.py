import time
from typing import List

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from general_classes.enums import SearchItems
from general_classes.logger import Message


class SeleniumBaseParser:

    def __init__(self, driver: webdriver.Chrome) -> None:
        self._driver = driver
        self._driver.implicitly_wait(time_to_wait=6)
        self._driver.maximize_window()
        self._links = []

    def close_browser(self) -> None:
        self._driver.close()
        self._driver.quit()

    def set_links(self, links: List[str]) -> None:
        self._links = links

    def _follow_the_link(self, link: str) -> None:
        self._driver.get(url=link)


class SeleniumLinksParser(SeleniumBaseParser):
    BASE_URL = "https://patents.google.com/"

    def _add_links_to_list(self, list_: List, all_result: bool = False) -> None:
        links_number = self._find_total_items_result()
        if all_result:
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
            Message.info_message(
                f"Добавлено ссылок: {len_links_to_str}. Всего добавлено: {total_added}"
            )
            list_.extend(links_to_str)
            self._click_to_next_button(xpath=SearchItems.next_button.value)

    def _check_result(self) -> bool:
        try:
            self._driver.find_element(
                by=By.XPATH, value=SearchItems.no_result_message.value
            )
            return False
        except NoSuchElementException:
            return True

    def _add_more_result_per_page(self) -> None:
        more_result_button = self._driver.find_element(by=By.XPATH, value=SearchItems.result_in_page_button.value)
        self._driver.execute_script("arguments[0].click();", more_result_button)
        max_result_button = self._driver.find_element(by=By.XPATH, value=SearchItems.one_hundred_results_per_page.value)
        self._driver.execute_script("arguments[0].click();", max_result_button)

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

    def _find_total_items_result(self) -> int:
        try:
            result = self._driver.find_element(
                by=By.XPATH, value=SearchItems.num_result.value
            )
        except NoSuchElementException:
            Message.warning_message(f'Элемент "Всего результатов" не найден')
            result = "0"
        res_number = list(filter(lambda x: x.isdigit(), result.text.split()))
        return int(res_number[0])
