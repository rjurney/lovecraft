import json
import logging
import os
import warnings

import tqdm
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import CacheBackedEmbeddings, OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.storage import LocalFileStore
from langchain.vectorstores import OpenSearchVectorSearch
from langchain_community.llms import OpenAI
from langchain_core.documents.base import Document

logging.getLogger("langchain").setLevel(logging.DEBUG)

warnings.simplefilter("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"


def main():
    # Set in my ~/.zshrc
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    with open("data/stories.json", "r") as file:
        stories = [json.loads(line)["text"] for line in file]
        docs = [Document(page_content=s) for s in stories if len(s) > 100]

    # Embed them with OpenAI ada model and store them in OpenSearch
    embeddings = OpenAIEmbeddings()
    fs = LocalFileStore("./data/embedding_cache/")
    cached_embedder = CacheBackedEmbeddings.from_bytes_store(
        embeddings, fs, namespace=embeddings.model
    )

    # Setup a OpenSearch to store the embeddings
    opensearch = OpenSearchVectorSearch(
        index_name="academic_papers",
        embedding_function=cached_embedder,
        opensearch_url="http://admin:admin@localhost:9200",
    )
    opensearch.add_documents(docs, bulk_size=1024, verbose=True)

    # Setup a simple buffer memory system to submit with the API calls to provide prompt context
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Create a ConversationalRetrievalChain from the LLM, the vectorstore, and the memory system
    qa = ConversationalRetrievalChain.from_llm(
        OpenAI(model="gpt-3.5-32k", temperature=0),
        opensearch.as_retriever(),
        memory=memory,
        verbose=True,
    )

    # Ask some questions...
    print(qa({"question": "Who is Cthulhu?"})["answer"])

    print(qa({"question": "Yog Sothoth will grant me great powers if I boil cats!"})["answer"])


if __name__ == "__main__":
    main()
