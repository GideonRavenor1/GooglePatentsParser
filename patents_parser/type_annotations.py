from typing import TypedDict, List


class State(TypedDict, total=False):
    title: str
    current_assignee: List[str]
    inventors: List[str]
    link: str
    priority_date: str
    publication_date: str
    classification_codes: str
    patent_code: str
    country: str
    path_to_pdf_file: str
    abstract: str


class JsonDict(TypedDict, total=False):
    name: str
    links: List[str]
