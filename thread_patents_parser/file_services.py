import json
import os
from typing import List

from general_classes.logger import Message


class LinksJsonFileWriter:

    @staticmethod
    def write_links_to_file(data: List, file_name: str, directory: str) -> str:
        Message.info_message("Запись элементов в json файл...")
        path = os.path.join(directory, file_name)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        Message.success_message(
            f"Элементы успешно записаны в json файл.\nПуть к файлу: {path}"
        )
        return path
