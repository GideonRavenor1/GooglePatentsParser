import os
import json
from typing import List, Set, Tuple

from xlsxwriter import Workbook

from type_annotations import State
from enums import MetaDataColumnName, PatentsColumnName, PersonColumnName
from logger import Message


class LinksFileReader:
    @staticmethod
    def parse_txt_file(path_to_links: str) -> List:
        with open(path_to_links, "r") as file:
            return list(map(str.strip, file.readlines()))

    @staticmethod
    def parse_json_file(path_to_links: str) -> List:
        with open(path_to_links, "r", encoding="utf-8") as file:
            return json.load(file)


class LinksFileWriter:
    def __init__(self, directory: str) -> None:
        self.__directory = directory

    def write_links_to_txt_file(self, data: Set, file_name: str) -> str:
        Message.info_message("Запись ссылок в txt файл...")
        path = os.path.join(self.__directory, file_name)
        with open(path, "w", encoding="utf-8") as file:
            file.write("\n".join(data))
        Message.success_message(
            f"Ссылки успешно записаны в txt файл.\nПуть к файлу: {path}"
        )
        return path

    def write_links_to_json_file(self, data: List, file_name: str) -> str:
        Message.info_message("Запись ссылок в json файл...")
        path = os.path.join(self.__directory, file_name)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=True, indent=4)
        Message.success_message(
            f"Ссылки успешно записаны в json файл.\nПуть к файлу: {path}"
        )
        return path


class XlsxFileWriter:
    PATENTS = "patents.xlsx"
    METADATA = "metadata.xlsx"
    PERSON = "person.xlsx"

    def __init__(self, directory: str, state: List[State]) -> None:
        self.__directory = directory
        self.__state = state
        self.__patents_path = os.path.join(self.__directory, self.PATENTS)
        self.__metadata_path = os.path.join(self.__directory, self.METADATA)
        self.__person_path = os.path.join(self.__directory, self.PERSON)

    def execute_write(self) -> None:
        self._write_patents()
        self._write_metadata()
        self._write_person()

    def _write_patents(self):
        Message.info_message(f"Запись данных в {self.PATENTS}...")
        with Workbook(self.__patents_path) as workbook:
            worksheet = workbook.add_worksheet(name="Patents")
            bold = workbook.add_format({"bold": True})
            columns = [attribute.value for attribute in PatentsColumnName]
            for column, header in enumerate(columns):
                worksheet.write_string(0, column, header, cell_format=bold)

            row = 1
            for element in self.__state:
                current_assignee = element["current_assignee"]
                inventors = element["inventors"]
                max_deep = max((len(current_assignee), len(inventors)))
                iter_current_assignee = iter(current_assignee)
                iter_inventors = iter(inventors)
                for index in range(max_deep):
                    worksheet.write_string(row, 0, element["title"])

                    try:
                        current_assignee = next(iter_current_assignee)
                    except StopIteration:
                        current_assignee = ""
                    worksheet.write_string(row, 1, current_assignee)

                    try:
                        inventor = next(iter_inventors)
                    except StopIteration:
                        inventor = ""
                    worksheet.write_string(row, 2, inventor)

                    worksheet.write_string(row, 3, element["link"])
                    worksheet.write_string(row, 4, element["priority_date"])
                    worksheet.write_string(row, 5, element["publication_date"])
                    worksheet.write_string(row, 6, element["classification_codes"])
                    worksheet.write_string(row, 7, element["patent_code"])
                    worksheet.write_string(row, 8, element["country"])
                    worksheet.write_string(row, 9, "")
                    worksheet.write_string(row, 10, element["path_to_pdf_file"])
                    row += 1
        Message.success_message(f"Запись данных в {self.PATENTS} завершена.")

    def _write_metadata(self) -> None:
        Message.info_message(f"Запись данных в {self.METADATA}...")
        with Workbook(self.__metadata_path) as workbook:
            columns = [attribute.value for attribute in MetaDataColumnName]
            worksheet = workbook.add_worksheet(name="Metadata")
            bold = workbook.add_format({"bold": True})
            for column, header in enumerate(columns):
                worksheet.write_string(0, column, header, cell_format=bold)

            row = 1
            for element in self.__state:
                worksheet.write_string(row, 0, element["path_to_pdf_file"])
                worksheet.write_string(row, 1, element["link"])
                worksheet.write_string(row, 2, element["publication_date"])
                worksheet.write_string(row, 3, ", ".join(element["inventors"]))
                worksheet.write_string(row, 4, element["patent_code"])
                row += 1
        Message.success_message(f"Запись данных в {self.METADATA} завершена.")

    def _write_person(self) -> None:
        Message.info_message(f"Запись данных в {self.PERSON}...")
        with Workbook(self.__person_path) as workbook:
            columns = [attribute.value for attribute in PersonColumnName]
            worksheet = workbook.add_worksheet(name="Person")
            bold = workbook.add_format({"bold": True})
            for column, header in enumerate(columns):
                worksheet.write_string(0, column, header, cell_format=bold)

            row = 1
            for element in self.__state:
                text = (
                    f"{element['title']} {element['priority_date']} "
                    f"{', '.join(element['inventors'])} {element['abstract']} {element['link']}"
                )
                worksheet.write_string(row, 0, text)
                row += 1
        Message.success_message(f"Запись данных в {self.PERSON} завершена.")

    @staticmethod
    def zipped_files(dir_name: str) -> None:
        Message.info_message("Упаковываю файлы в архив...")
        wget = f"zip -r {dir_name}.zip {dir_name}"
        os.system(wget)
        Message.success_message("Файлы упакованы в архив.")


class MakeDirManager:
    def __init__(self):
        self._current_dir = os.getcwd()

    def make_link_dir(self, name: str) -> str:
        links_dir = os.path.join(self._current_dir, name)
        try:
            os.mkdir(links_dir)
            Message.success_message(f"Директория {links_dir} успешно создана")
        except FileExistsError:
            Message.warning_message(f"Директория {links_dir} уже существует")
        return links_dir

    def make_result_dir(self, name: str) -> str:
        directory = os.path.join(self._current_dir, name)
        try:
            os.mkdir(directory)
            Message.success_message(f"Директория {directory} успешно создана")
        except FileExistsError:
            Message.warning_message(f"Директория {directory} уже существует")
        return directory

    @staticmethod
    def make_temp_browser_dir(directory: str) -> str:
        if not os.path.exists(directory):
            os.mkdir(directory)
        return directory

    @staticmethod
    def make_author_dirs(name: str, directory: str) -> Tuple[str, str]:
        author_dir = os.path.join(directory, name)
        patent_dir = os.path.join(author_dir, "patents")
        try:
            os.mkdir(author_dir)
            Message.success_message(f"Директория {author_dir} успешно создана")
        except FileExistsError:
            Message.warning_message(f"Директория {author_dir} уже существует")
        try:
            os.mkdir(patent_dir)
            Message.success_message(f"Директория {patent_dir} успешно создана")
        except FileExistsError:
            Message.warning_message(f"Директория {patent_dir} уже существует")
        return author_dir, patent_dir
