import json
import os
import shutil
from typing import Tuple, List

from xlsxwriter import Workbook

from general_classes.enums import PatentsColumnName, MetaDataColumnName, PersonColumnName
from general_classes.logger import Message
from general_classes.type_annotations import State


class LinksJsonFileReader:

    @staticmethod
    def parse_file(path_to_links: str) -> List:
        with open(path_to_links, "r", encoding="utf-8") as file:
            return json.load(file)


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
    def zipped_files(dir_name: str, zip_file_name: str) -> None:
        if not os.listdir(dir_name):
            Message.warning_message(f"Директория {dir_name} пуста. Архивация невозможна")
        else:
            zip_file_name = f"{zip_file_name}.zip"
            Message.info_message("Упаковываю файлы в архив...")
            wget = f"zip -r {zip_file_name} {dir_name}"
            os.system(wget)
            Message.success_message("Файлы упакованы в архив.")
            Message.success_message(
                f"Размер архива: {os.stat(zip_file_name).st_size // (1024 * 1024)} мб.\n"
                f"Путь к файлу: {os.path.join(os.getcwd(), zip_file_name)}"
            )

    @staticmethod
    def delete_empty_directory(dir_name: str) -> None:
        directories = os.listdir(dir_name)
        Message.info_message(f"Всего уникальных авторов: {len(directories)}")
        Message.info_message("Поиск пустых директорий...")
        empty_dirs = []
        for ref, source, files in os.walk(dir_name):
            if not files and not source and ref != ".":
                empty_dirs.append(ref)

        len_empty_dirs = len(empty_dirs)
        Message.warning_message(f"Найдено пустых директорий: {len_empty_dirs}")
        if len_empty_dirs:
            [shutil.rmtree(directory.rsplit('/', maxsplit=1)[0]) for directory in empty_dirs]
        Message.success_message("Пустые директории успешно удалены.")


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
