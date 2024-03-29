# This file extracts and cleans the OCR'd text from the PDFs of 5 volumes of Lovecraft's letters
import time
from collections import defaultdict
from typing import Dict, List, Type, Union

from langchain.chains import LLMChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_openai.chat_models import ChatOpenAI
from pypdf import PdfReader
from pypdf._page import PageObject

BOOK_CONFIG: Dict[str, Dict[str, Union[str, int]]] = {
    "volume_1": {
        "filename": "Lovecraft, H. P. - Selected Letters I (Arkham House, 1965).pdf",
        "start_page": 0,
        "end_page": 100,
    },
    "volume_2": {
        "filename": "Lovecraft, H. P. - Selected Letters II (Arkham House, 1968).pdf",
        "start_page": 0,
        "end_page": 100,
    },
    "volume_3": {
        "filename": "Lovecraft, H. P. - Selected Letters III (1929-1931).pdf",
        "start_page": 0,
        "end_page": 100,
    },
    "volume_4": {
        "filename": "Lovecraft, H. P. - Selected Letters IV (1932-1934).pdf",
        "start_page": 0,
        "end_page": 100,
    },
    # "volume_5": {
    #     "filename": "Lovecraft, H. P. - Selected Letters V (1934-1937) (Arkham House, 1976).pdf",
    #     "start_page": 0,
    #     "end_page": 100,
    # },
}

# Get the raw pages from each book
raw_contents: defaultdict = defaultdict(list)
for volume, config in BOOK_CONFIG.items():
    reader: PdfReader = PdfReader(f"data/{config['filename']}")
    for page_num in range(config["start_page"], config["end_page"]):
        page: PageObject = reader.pages[page_num]
        print(type(page))
        break

        raw_contents[volume].append(page.extract_text())


llm: ChatOpenAI = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.25)

messages: List[Type[PromptTemplate]] = [
    SystemMessagePromptTemplate.from_template(
        "I have text from pages of a book containing letters from the 1930s by the "
        "horror writer H.P. Lovecraft. "
        "The text comes from an OCR'd PDF file, one record per page. The OCR process "
        "created errors in the text that I would like to fix. I will provide the text "
        "for each page, and you will provide the corrected text.\n"
    ),
    # MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template(
        "The text for page number {page_number} is:\n\n{page_content}\n\n"
    ),
]
prompt = ChatPromptTemplate.from_messages(messages=messages)

# Everything look alright?
print(prompt.format(page_number=1, page_content=raw_contents["volume_1"][1]))

# memory=memory - maybe summarization memory? Once I get this working
book_chain = LLMChain(name="book_chain", system_prompt=prompt, llm=llm, verbose=True)

time.sleep(0.1)
