import logging
import os
from typing import  List
from typing_extensions import override

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from langchain_community.vectorstores import Chroma
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

class ChromaEmbedding(Embeddings):
    embedding_model_name = "text-embedding-v3"

    def __init__(self):
        api_key = os.getenv('LLM_API_KEY')
        api_base = os.getenv('LLM_API_BASE', "https://dashscope.aliyuncs.com/compatible-mode/v1")

        self.embedding_function = OpenAIEmbeddingFunction(
            api_key = api_key,
            api_base = api_base,
            model_name = self.embedding_model_name,
        )


    @override
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embedding_function(texts)


    @override
    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


class CustomPromptRag:
    PROMPT_SIMILAR_SCORE = 0.85   # need tune-up score based on different embedding model

    def __init__(self):
        prompt_docs = self._load_prompts()
        self.vector_store = self._init_vector_store(prompt_docs)


    # should read from DB, load all custom prompt or COT
    def _load_prompts(self) -> List[Document]:
        prompt_docs = []
        prompt_docs.append(self._create_prompt_doc(
            prompt_summary="Fault location and analysis of fault causes",
            prompt_path="templates/example/fault_user_prompt.md"
        ))
        return prompt_docs


    def _create_prompt_doc(self, prompt_summary: str, prompt_path: str)-> Document:
        return Document(
            page_content=prompt_summary,
            metadata={
                "source": prompt_path,
            }
        )


    def _init_vector_store(self, docs: List[Document]) -> VectorStore:
        embeddings = ChromaEmbedding()
        return Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=None
        )


    def search_prompt(self, query:str)-> str:
        prompt_path = None
        results = self.vector_store.similarity_search_with_score(query=query, k=1)
        if results and len(results) > 0:
            doc, score = results[0]
            if score > self.PROMPT_SIMILAR_SCORE:
                logging.info(f"CustomPromptRag search: SIMILAR_SCORE: {score} > {self.PROMPT_SIMILAR_SCORE}, "
                             f"\nquery: '{query}' \nprompt_summary: '{doc.page_content}'\n")
            else:
                prompt_path = doc.metadata['source']
                logging.info(f"CustomPromptRag search: SIMILAR_SCORE: {score}, prompt_path: '{prompt_path}'")

        return prompt_path


if __name__ == "__main__":
    from xgae.utils.setup_env import setup_logging

    setup_logging()

    custom_prompt_rag = CustomPromptRag()

    querys = ["locate 10.2.3.4 fault and solution", # 0.79
              "定位 10.2.3.4 故障,并给出解决方案",      # 0.81
              "locate fault and solution",          # 0.42
              "locate fault",                       # 0.40
              "定位故障",                            # 0.64
              "fault solution",                     # 0.47
              "locate",                             # 0.95
              "5+7"                                 # 1.12
              ]

    for query in querys:
        logging.info("*"*50)
        logging.info(f"query: '{query}'")
        custom_prompt_rag.search_prompt(query)
