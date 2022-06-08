from enum import Enum


class DirTypeEnum(Enum):
    TEMP_DIR = "/tmp/google_patents/"
    LINKS_DIR = "links"
    RESULT_DIR = "result"


class FileTypeEnum(Enum):
    MAIN_TXT = "main_links.txt"
    INVENTORS_TXT = "inventors.txt"
    INVENTORS_JSON = "inventors.json"


class UniqueNames(Enum):
    INVENTOR = "Inventor"
    CURRENT_ASSIGNEE = "Current Assignee"


class XpathIdElements(Enum):
    patent_title = "//h1[@id='title']"
    patent_code = "//h2[@id='pubnum']"
    classifications = "//section[@Id='classifications']"
    more_classifications_button = (
        "//section[@Id='classifications']//classification-viewer/div/div/div[1]"
    )
    classification_elements = (
        "//section[@Id='classifications']//div/classification-tree"
    )
    classification_element_codes = (
        "//section[@Id='classifications']//div/classification-tree//state-modifier/a"
    )


class XpathRightPartElements(Enum):
    important_people_section = (
        "//result-container/patent-result/div/div/div/div[1]/div[2]/section/"
        "dl[contains(@class, 'important-people')]//dt|//result-container/patent-result/div/div/div/div[1]/div[2]/"
        "section/dl[contains(@class, 'important-people')]//dd"
    )
    inventors_link = (
        "//result-container/patent-result/div/div/div/div[1]/div[2]/"
        "section/dl[contains(@class, 'important-people')]//dd//a"
    )
    country = (
        "//result-container/patent-result/div/div/div/div[1]/div[2]/section/header/p"
    )
    pdf = "//result-container/patent-result/div/div/div/div[1]/div[2]/section/header/div/a"
    date_priority = (
        "//result-container/patent-result/div/div/div/div[1]/div[2]/"
        "section/application-timeline//div[contains(@class, 'priority')]"
    )
    date_publication_template = (
        "//result-container/patent-result/div/div/div/div[1]/div[2]/section/application-timeline"
        "//span[contains(text(), '{patent_code}')]//ancestor::div[contains(@class, 'event')]"
        "/div[contains(@class, 'publication')]"
    )
    abstract = "//abstract/div"


class SearchItems(Enum):
    search_form = "//input[@id='searchInput']"
    num_result = "//span[@id='numResultsLabel']"
    result_items = (
        "//search-results//search-result-item//a[@id='link']/parent::state-modifier"
    )
    no_result_message = "//div[@id='noResultsMessage']"
    next_button = "//search-paging/state-modifier[3]/a/paper-icon-button/iron-icon"


class PatentsColumnName(Enum):
    title = "Название"
    current_assignee = "Патентообладатель"
    inventors = "Автор"
    link = "Ссылка на источник"
    priority_date = "Дата приоритета"
    publication_date = "Дата публикации"
    classification_codes = "Код патентного классификатора"
    patent_code = "Номер патента"
    country = "Страна"
    topics = "Тематика"
    path_to_pdf_file = "Подтверждающий документ"


class MetaDataColumnName(Enum):
    file_name = "Название файла"
    source = "Источник"
    publication_date = "Дата публикации"
    author = "Автор публикации"
    description = "Описание"


class PersonColumnName(Enum):
    patents = "Патенты"
