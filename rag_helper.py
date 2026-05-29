import os
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
import chromadb


class RAGHelper:
    """
    Helper class for RAG (Retrieval Augmented Generation) functionality.
    Manages document loading, embedding, and retrieval.
    """

    def __init__(self, collection_name: str = "study_materials", persist_directory: str = "./chroma_db"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Embeddings
        self.embeddings = OpenAIEmbeddings()

        # Improved chunking (better retrieval)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            length_function=len,
        )

        self.vectorstore = None
        self._initialize_vectorstore()

    # =========================
    # VECTOR DB INIT
    # =========================
    def _initialize_vectorstore(self):
        try:
            os.makedirs(self.persist_directory, exist_ok=True)

            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )

        except Exception as e:
            print(f"Vector DB init error: {e}")
            self.vectorstore = None

    # =========================
    # PDF LOADER (FIXED)
    # =========================
    def load_pdf(self, file_path: str) -> bool:
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()

            if not documents:
                print("PDF empty or unreadable")
                return False

            chunks = self.text_splitter.split_documents(documents)

            if not chunks:
                print("No chunks created from PDF")
                return False

            if self.vectorstore:
                self.vectorstore.add_documents(chunks)
                return True

            return False

        except Exception as e:
            print(f"PDF load error: {e}")
            return False

    # =========================
    # TEXT LOADER
    # =========================
    def load_text(self, file_path: str) -> bool:
        try:
            loader = TextLoader(file_path)
            documents = loader.load()

            chunks = self.text_splitter.split_documents(documents)

            if self.vectorstore:
                self.vectorstore.add_documents(chunks)
                return True

            return False

        except Exception as e:
            print(f"Text load error: {e}")
            return False

    # =========================
    # TEXT CONTENT DIRECT
    # =========================
    def load_text_content(self, text: str, metadata: dict = None) -> bool:
        try:
            from langchain.schema import Document

            if not text or len(text.strip()) < 10:
                return False

            doc = Document(page_content=text, metadata=metadata or {})
            chunks = self.text_splitter.split_documents([doc])

            if self.vectorstore:
                self.vectorstore.add_documents(chunks)
                return True

            return False

        except Exception as e:
            print(f"Text content error: {e}")
            return False

    # =========================
    # QUERY (FIXED RETRIEVAL)
    # =========================
    def query(self, question: str, k: int = 6) -> List[str]:
        try:
            if not self.vectorstore:
                return []

            if not question or len(question.strip()) == 0:
                return []

            # 🔥 IMPROVED retrieval
            docs = self.vectorstore.similarity_search(question, k=k)

            if not docs:
                return []

            results = []
            for doc in docs:
                if doc.page_content and len(doc.page_content.strip()) > 0:
                    results.append(doc.page_content)

            return results

        except Exception as e:
            print(f"Query error: {e}")
            return []

    # =========================
    # QUERY WITH SCORES
    # =========================
    def query_with_scores(self, question: str, k: int = 6) -> List[tuple]:
        try:
            if not self.vectorstore:
                return []

            results = self.vectorstore.similarity_search_with_score(question, k=k)

            return [(doc.page_content, score) for doc, score in results]

        except Exception as e:
            print(f"Score query error: {e}")
            return []

    # =========================
    # CLEAR DB
    # =========================
    def clear_database(self) -> bool:
        try:
            client = chromadb.PersistentClient(path=self.persist_directory)
            client.delete_collection(name=self.collection_name)
            self._initialize_vectorstore()
            return True

        except Exception as e:
            print(f"Clear DB error: {e}")
            return False

    # =========================
    # DOCUMENT COUNT
    # =========================
    def get_document_count(self) -> int:
        try:
            if self.vectorstore:
                return self.vectorstore._collection.count()
            return 0

        except Exception as e:
            print(f"Count error: {e}")
            return 0

    # =========================
    # PHI SUPPORT (UNCHANGED)
    # =========================
    def create_phi_knowledge_base(self) -> Optional[object]:
        try:
            from phi.vectordb.chroma import ChromaDb

            knowledge_base = ChromaDb(
                collection=self.collection_name,
                path=self.persist_directory,
                embedder=self.embeddings
            )
            return knowledge_base

        except Exception as e:
            print(f"Phi KB error: {e}")
            return None