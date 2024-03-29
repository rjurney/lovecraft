# This file extracts and cleans the OCR'd text from the PDFs of 5 volumes of Lovecraft's letters
import json
import os
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
from tqdm import tqdm

BOOK_CONFIG: Dict[str, Dict[str, Union[str, int]]] = {
    "volume_1": {
        "filename": "Lovecraft, H. P. - Selected Letters I (Arkham House, 1965).pdf",
    },
    "volume_2": {
        "filename": "Lovecraft, H. P. - Selected Letters II (Arkham House, 1968).pdf",
    },
    "volume_3": {
        "filename": "Lovecraft, H. P. - Selected Letters III (1929-1931).pdf",
    },
    "volume_4": {
        "filename": "Lovecraft, H. P. - Selected Letters IV (1932-1934).pdf",
    },
    # "volume_5": {
    #     "filename": "Lovecraft, H. P. - Selected Letters V (1934-1937) (Arkham House, 1976).pdf",
    #     "start_page": 0,
    #     "end_page": 100,
    # },
}
CACHE_PATH = "data/corrected_pages.json"

# Get the raw pages from each book
raw_contents: defaultdict = defaultdict(list)
for volume, config in BOOK_CONFIG.items():
    reader: PdfReader = PdfReader(f"data/{config['filename']}")
    end_page = len(reader.pages)
    print(f"Ingesting {config['filename']} ...")
    for page_num in range(end_page):
        page: PageObject = reader.pages[page_num]
        raw_contents[volume].append(page.extract_text())


# Now use OpenAI GPT-4 to clean up the OCR'd text for each page in each book
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
book_chain = LLMChain(name="book_chain", prompt=prompt, llm=llm, verbose=True)

# Test it once...
var = book_chain.run(page_number=1, page_content=raw_contents["volume_1"][1])
print(var)

# We need to be able to restart on the fly, so we'll store the corrected pages in a diskcache.Cache
# See: https://grantjenks.com/docs/diskcache/tutorial.html

# Check the cache and load any pages we already cleaned
if os.path.exists(CACHE_PATH):
    with open("data/corrected_pages.json") as file:
        print("Loading cached pages ...")
        corrected_pages = json.load(file)
else:
    corrected_pages = {key: [] for key in raw_contents.keys()}

for volume in raw_contents.keys():
    print(f"Cleaning up {volume} ...")
    # For each page in the volume, run the LLMChain to clean it up
    for i, page in enumerate(tqdm(raw_contents[volume], total=len(raw_contents[volume]))):

        if (
            volume in corrected_pages
            and corrected_pages[volume]
            and len(corrected_pages[volume]) > i
        ):
            print(f"Skipping page {i} as it's already been corrected.")
            continue

        print("Submitting page {i} for correction...")
        corrected_page = book_chain.run(page_number=i, page_content=page)
        corrected_pages[volume].append(corrected_page)

        # Cache every 10 pages
        if i % 10 == 0:
            with open(CACHE_PATH, "w") as file:
                json.dump(corrected_pages, file, sort_keys=True, indent=4)
                print("Cached pages 0-{i} for {volume}.")

        # Please Hammer, don't hurt 'OpenAI
        time.sleep(0.1)
