import json
import logging
import os
import warnings

from langchain import hub
from langchain.schema.runnable import RunnablePassthrough
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_core.documents.base import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_openai.chat_models import ChatOpenAI
from langchain_text_splitters import CharacterTextSplitter

logging.getLogger("langchain").setLevel(logging.DEBUG)

warnings.simplefilter("ignore")
warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ["PYTHONWARNINGS"] = "ignore"


# Set in ein ~/.zshrc
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

with open("data/stories.json", "r") as file:
    stories = [json.loads(line)["text"] for line in file]
    docs = [Document(page_content=s) for s in stories if len(s) > 100]

# They happen to be split by '\r\n' so we can use the CharacterTextSplitter, which behaves
# strangely re: chunk size and separators. See Stack Overflow...
# https://stackoverflow.com/questions/76633836/what-does-langchain-charactertextsplitters-chunk-size-param-even-do
text_splitter = CharacterTextSplitter(separator="\r\n", chunk_size=1000, chunk_overlap=100)
split_docs = text_splitter.split_documents(docs)

# # Embed them with OpenAI ada model and store them in OpenSearch
# embeddings = OpenAIEmbeddings()
# fs = LocalFileStore("./data/embedding_cache/")
# cached_embedder = CacheBackedEmbeddings.from_bytes_store(embeddings, fs, namespace=embeddings)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L12-v2")

# Setup a OpenSearch to store the embeddings
opensearch = OpenSearchVectorSearch(
    index_name="lovecraft",
    embedding_function=embeddings,
    opensearch_url="http://admin:admin@localhost:9200",
)

# Chat moddel
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.25)

# Pull the RAG prompt from the hub
prompt = hub.pull("daethyra/rag-prompt")

output_parser = StrOutputParser()

retrieval_chain = (
    {"context": opensearch.as_retriever(), "question": RunnablePassthrough()}
    | prompt
    | llm
    | output_parser
)

# Take 1
print(
    retrieval_chain.invoke(
        (
            "You are a computer brain of H.P. Lovecraft. Use the context provided to "
            + "provide a direct answer for an avid fan of H.P. Lovecraft."
            + "\n\n"
            + "Who would win in a fight: Cthulhu or Yog Sothoth? Why?"
        )
    )
)

# Take 2
print(
    retrieval_chain.invoke(
        "What are the names of five stories Lovecraft would have written if he had lived past 1937. Use your imagination."
    )
)
