import json
import os
import threading
from typing import List

from general_classes.logger import Message


class LinksFileWriter:

    @staticmethod
    def write_links_to_txt_file(data: List, file_name: str, directory: str) -> str:
        name = threading.current_thread().name
        Message.info_message(f"[{name}] Запись ссылок в txt файл...")
        path = os.path.join(directory, file_name)
        with open(path, "w", encoding="utf-8") as file:
            file.write("\n".join(data))
        Message.success_message(
            f"[{name}] Ссылки успешно записаны в txt файл.\nПуть к файлу: {path}"
        )
        return path

    @staticmethod
    def write_links_to_json_file(data: List, file_name: str, directory: str) -> str:
        name = threading.current_thread().name
        Message.info_message(f"[{name}] Запись элементов в json файл...")
        path = os.path.join(directory, file_name)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=True, indent=4)
        Message.success_message(
            f"[{name}] Элементы успешно записаны в json файл.\nПуть к файлу: {path}"
        )
        return path
