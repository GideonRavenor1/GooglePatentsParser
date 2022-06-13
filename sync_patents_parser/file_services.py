import json
import os
from typing import List

from general_classes.logger import Message


class LinksFileWriter:
    def __init__(self, directory: str) -> None:
        self.__directory = directory

    def write_links_to_txt_file(self, data: List, file_name: str) -> str:
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
