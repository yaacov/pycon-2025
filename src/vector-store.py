# Vector store creation from mtv.md using LangChain and FAISS

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from utils import print_success

# 1. Load and split document
loader = TextLoader("mtv.md")
documents = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
docs = text_splitter.split_documents(documents)

model_path = "ibm-granite/granite-embedding-30m-english"
embeddings = HuggingFaceEmbeddings(model_name=model_path)
vectorstore = FAISS.from_documents(docs, embeddings)

# 3. Save vector store to disk
vectorstore.save_local("faiss_index")

print_success("Vector store created and saved to 'faiss_index'.")
