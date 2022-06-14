import os
import re
import threading
from datetime import datetime
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from general_classes.enums import XpathRightPartElements, UniqueNames, XpathIdElements
from general_classes.logger import Message
from general_classes.type_annotations import JsonDict, State
from thread_patents_parser.base import SeleniumLinksParser, SeleniumBaseParser

LOCK = threading.Lock()


class SeleniumPatentsInventorsLinksParser(SeleniumLinksParser):

    def __init__(self, driver: webdriver.Chrome, thread_name: str):
        super().__init__(driver, thread_name)
        self._json_element = JsonDict()
        self._patents_links_list = []

    def collect_links(self) -> List[JsonDict]:
        len_patents_links = len(self._links)
        for link in self._links:
            Message.info_message(f"[{self._thread_name}] Осталось спарсить ссылок: {len_patents_links}")
            Message.info_message(f"[{self._thread_name}] Текущая ссылка: {link}")
            self._follow_the_link(link=link)
            inventor = (
                link.split("inventor")[2]
                .strip(":()")
                .replace("+", "_")
                .replace("%2C", "")
            )
            len_patents_links -= 1
            if not self._check_result():
                Message.warning_message(f"[{self._thread_name}] Патенты у автора {inventor} не найдена")
                continue
            self._json_element["name"] = inventor
            self._json_element["links"] = []
            self._add_links_to_list(list_=self._json_element["links"])
            valid_links = self._links_converter(data=self._json_element["links"])
            self._json_element["links"] = valid_links
            copy_element = self._json_element.copy()
            self._patents_links_list.append(copy_element)
        return self._patents_links_list

    def _links_converter(self, data: List) -> List:
        Message.info_message(f"[{self._thread_name}] Конвертация {len(data)} ссылок..")
        list_link = list({urljoin(base=self.BASE_URL, url=url) for url in data})
        Message.info_message(f"[{self._thread_name}] Всего уникальных ссылок: {len(list_link)}")
        return list_link


class SeleniumPatentsParser(SeleniumBaseParser):

    def __init__(
        self,
        driver: webdriver.Chrome,
        thread_name: str,
        tmp_dir: str,
        valid_classifications_code: str,
        keyword: str,
        min_keyword_count: int
    ) -> None:
        super().__init__(driver, thread_name)
        self._tmp_dir = tmp_dir
        self._valid_classifications_code = valid_classifications_code
        self._keyword = keyword
        self._min_keyword_count = min_keyword_count
        self._state = State()
        self._url_regex = re.compile(r"^(http|https)://([\w.]+/?)\S*$")
        self._result_list = []

    def parse_patents_links(self, patent_dir: str) -> None:
        for link in self._links:
            self._follow_the_link(link=link)
            self._state["link"] = link
            Message.success_message(f"[{self._thread_name}] Ссылка сохранена")
            self._click_to_more_button()

            try:
                self._find_classification_codes()
            except ValueError:
                continue

            self._find_title()
            self._parse_people_section()
            self._find_country()
            self._find_priority_date()
            self._find_patent_code()
            self._find_publication_date()
            self._find_abstract()
            self._download_pdf_file(patent_dir=patent_dir)
            self._add_state_to_result_list()

    def get_state(self) -> List[State]:
        Message.info_message(f"[{self._thread_name}] Выгружается стейт...")
        copy_state = self._result_list.copy()
        self._result_list.clear()
        return copy_state

    def _click_to_more_button(self) -> None:
        try:
            button = self._driver.find_element(
                by=By.XPATH, value=XpathIdElements.more_classifications_button.value
            )
            self._driver.execute_script("arguments[0].click();", button)
        except NoSuchElementException:
            Message.warning_message(
                f'[{self._thread_name}] Кнопка "View more classifications" не найдена. URL: {self._state["link"]}'
            )

    def _find_classification_codes(self) -> None:
        try:
            classification_element = self._driver.find_element(
                by=By.XPATH, value=XpathIdElements.classification_elements.value
            )
        except NoSuchElementException:
            self._state["classification_codes"] = ""
            Message.warning_message(
                f'[{self._thread_name}] Коды патентных классификаторов не найдены. URL: {self._state["link"]}'
            )
        else:
            self._parse_classification_elements(element=classification_element)

    def _parse_classification_elements(self, element: WebElement) -> None:
        find_code_elements = element.find_elements(
            by=By.XPATH, value=XpathIdElements.classification_element_codes.value
        )
        codes = [i.text for i in find_code_elements if i.text]

        if not codes:
            self._state["classification_codes"] = ""
            Message.warning_message(
                f'[{self._thread_name}] Коды патентных классификаторов не найдены. URL: {self._state["link"]}'
            )
        else:
            self._state["classification_codes"] = ", ".join(codes)
            Message.success_message(f"[{self._thread_name}] Кода патентного классификатора сохранены.")

    def _validate_patent(self, list_of_code: List[str]) -> None:
        Message.info_message(f'[{self._thread_name}] Проверка валидности патента...')
        check_valid_code = [True if self._valid_classifications_code in code else False for code in list_of_code]
        if any(check_valid_code):
            Message.success_message(
                f"Патент прошел проверку. Найден ключевой классификатор: {self._valid_classifications_code}"
            )
            ...
        else:
            Message.warning_message(
                f"[{self._thread_name}] Не найден ключевой классификатор: {self._valid_classifications_code}"
            )
            html = self._driver.find_element(by=By.TAG_NAME, value='html').text
            count_keywords = len(re.findall(self._keyword, html, flags=re.IGNORECASE))
            valid_flag = count_keywords >= 10
            if not valid_flag:
                Message.warning_message(
                    f'[{self._thread_name}] Недостаточно ключевых слов в патенте. Найдено: {count_keywords}. '
                    f'Мин.значение: {self._min_keyword_count}.'
                    f'Патент записан не будет. URL: {self._state["link"]}'
                )
                raise ValueError
            Message.success_message(
                f"[{self._thread_name}] Патент прошел проверку. Найдено ключевых слов: {count_keywords}. "
                f"Мин.значение: {self._min_keyword_count}."
            )

    def _find_title(self) -> None:
        try:
            title = self._driver.find_element(
                by=By.XPATH, value=XpathIdElements.patent_title.value
            )
            self._state["title"] = title.text
            Message.success_message(f"[{self._thread_name}] Название патента сохранено")
        except NoSuchElementException:
            self._state["title"] = ""
            Message.warning_message(
                f'[{self._thread_name}] Название патента не найдено. URL: {self._state["link"]}'
            )

    def _parse_people_section(self) -> None:
        people_section = self._driver.find_elements(
            by=By.XPATH, value=XpathRightPartElements.important_people_section.value
        )
        if not people_section:
            self._state["current_assignee"] = []
            self._state["inventors"] = []
            Message.warning_message(
                f'[{self._thread_name}] Секция people_section не найдена. URL: {self._state["link"]}'
            )
        else:
            self._add_elements_to_state(people_section=people_section)

    def _add_elements_to_state(self, people_section: List[WebElement]) -> None:
        current_element = ""
        current_assignee = []
        inventors = []
        for element in people_section:
            tag_name = element.tag_name
            if tag_name == "dt":
                text = element.text
                if text in {
                    UniqueNames.INVENTOR.value,
                    UniqueNames.CURRENT_ASSIGNEE.value,
                }:
                    current_element = text
            elif tag_name == "dd":
                if current_element == UniqueNames.INVENTOR.value:
                    inventor_text = element.find_element(by=By.ID, value="link").text
                    inventors.append(inventor_text)
                elif current_element == UniqueNames.CURRENT_ASSIGNEE.value:
                    current_assignee.append(element.text)
        if not current_assignee:
            Message.warning_message(
                f'[{self._thread_name}] Патентообладатели не найдены. URL: {self._state["link"]}'
            )
        else:
            Message.success_message(f"[{self._thread_name}] Патентообладатели сохранены")
        if not inventors:
            Message.warning_message(f'[{self._thread_name}] Авторы не найдены. URL: {self._state["link"]}')
        else:
            Message.success_message(f"[{self._thread_name}] Авторы сохранены")
        self._state["current_assignee"] = current_assignee
        self._state["inventors"] = inventors

    def _find_priority_date(self) -> None:
        try:
            priority_date = self._driver.find_element(
                by=By.XPATH, value=XpathRightPartElements.date_priority.value
            )
            date_to_datetime = datetime.strptime(priority_date.text, "%Y-%m-%d")
            self._state["priority_date"] = date_to_datetime.strftime("%d.%m.%Y")
            Message.success_message(f"[{self._thread_name}] Дата приоритета сохранена")
        except NoSuchElementException:
            self._state["priority_date"] = ""
            Message.warning_message(
                f'[{self._thread_name}] Дата приоритета не найдена. URL: {self._state["link"]}'
            )

    def _find_patent_code(self) -> None:
        try:
            patent_code = self._driver.find_element(
                by=By.XPATH, value=XpathIdElements.patent_code.value
            )
            self._state["patent_code"] = patent_code.text
            Message.success_message(f"[{self._thread_name}] Номер патента сохранён")
        except NoSuchElementException:
            self._state["patent_code"] = ""
            Message.warning_message(
                f'[{self._thread_name}] Номер патента не найден. URL: {self._state["link"]}'
            )

    def _find_publication_date(self) -> None:
        patent_code = self._state["patent_code"]
        xpath = XpathRightPartElements.date_publication_template.value.format(
            patent_code=patent_code
        )
        try:
            publication_date = self._driver.find_element(by=By.XPATH, value=xpath)
            date_to_datetime = datetime.strptime(publication_date.text, "%Y-%m-%d")
            self._state["publication_date"] = date_to_datetime.strftime("%d.%m.%Y")
            Message.success_message(f"[{self._thread_name}] Дата публикации сохранена")
        except NoSuchElementException:
            self._state["publication_date"] = ""
            Message.warning_message(
                f'[{self._thread_name}] Дата публикации не найдена. URL: {self._state["link"]}'
            )

    def _find_abstract(self) -> None:
        try:
            abstract = self._driver.find_element(
                by=By.XPATH, value=XpathRightPartElements.abstract.value
            )
            Message.success_message(f"[{self._thread_name}] Абстракт сохранён")
            self._state["abstract"] = abstract.text
        except NoSuchElementException:
            Message.warning_message(f'[{self._thread_name}] Абстракт не найден. URL: {self._state["link"]}')
            self._state["abstract"] = ""

    def _find_country(self) -> None:
        try:
            country = self._driver.find_element(
                by=By.XPATH, value=XpathRightPartElements.country.value
            )
            self._state["country"] = country.text
            Message.success_message(f"[{self._thread_name}] Страна сохранена")
        except NoSuchElementException:
            self._state["country"] = ""
            Message.warning_message(f'[{self._thread_name}] Страна не найдена. URL: {self._state["link"]}')

    def _download_pdf_file(self, patent_dir: str) -> None:
        Message.info_message(f"[{self._thread_name}] Скачивание pdf файла...")
        element = self._driver.find_element(
            by=By.XPATH, value=XpathRightPartElements.pdf.value
        )
        link = element.get_attribute("href")
        LOCK.acquire()
        if link is None:
            Message.warning_message(
                f'[{self._thread_name}] Ссылка для скачивания PDF не найдена. URL: {self._state["link"]}'
            )
            Message.info_message(f"[{self._thread_name}] Скачивание html файла...")
            html = self._driver.page_source
            target = os.path.join(patent_dir, f"{self._state['patent_code']}.html")
            with open(target, "w", encoding="utf-8") as file:
                file.write(html)
        else:
            self._execute_download(link=link)
            file_name = os.listdir(self._tmp_dir)[0]
            file_path = os.path.join(self._tmp_dir, file_name)
            target = os.path.join(patent_dir, file_name)
            os.replace(file_path, target)
        LOCK.release()
        Message.success_message(f"[{self._thread_name}] Файл успешно скачен.")
        self._state["path_to_pdf_file"] = "/".join(target.split("/")[-3:])
        Message.success_message(f"[{self._thread_name}] Путь к файлу сохранён.")

    def _execute_download(self, link: str) -> None:
        Message.info_message(f"[{self._thread_name}] Загрузка файла...")
        wget = f"wget -P {self._tmp_dir} {link} -q"
        os.system(wget)

    def _add_state_to_result_list(self) -> None:
        copy_state = self._state.copy()
        self._result_list.append(copy_state)
