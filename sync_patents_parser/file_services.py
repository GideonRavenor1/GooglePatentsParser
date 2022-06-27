import json
import os
from typing import List

from general_classes.logger import Message


class LinksJsonFileWriter:
    def __init__(self, directory: str) -> None:
        self.__directory = directory

    def write_links_to_file(self, data: List, file_name: str) -> str:
        Message.info_message("Запись ссылок в json файл...")
        path = os.path.join(self.__directory, file_name)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        Message.success_message(
            f"Ссылки успешно записаны в json файл.\nПуть к файлу: {path}"
        )
        return path
