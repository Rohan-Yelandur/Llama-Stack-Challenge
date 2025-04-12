from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain.chains import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

import os

from langchain_community.document_loaders import TextLoader, UnstructuredFileLoader
import os


def load_documents():
    docs = []
    folder = "documents"
    for filename in os.listdir(folder):
        ext = os.path.splitext(filename)[1].lower()
        filepath = os.path.join(folder, filename)
        try:
            if ext == ".txt":
                loader = TextLoader(filepath)
            else:
                loader = UnstructuredFileLoader(filepath)
                
            loaded_docs = loader.load()

            for doc in loaded_docs:
                doc.page_content = f"This content is from the file {filename}:\n\n{doc.page_content}"
                doc.metadata["filename"] = filename

            docs.extend(loaded_docs)

        except Exception as e:
            print(f" Failed to load {filename}: {e}")
    
    print(f"Loaded {len(docs)} documents.")
    return docs


# Step 2: Split documents
def split_documents(docs):
    splitter = CharacterTextSplitter(chunk_size=10, chunk_overlap=1)
    print("Split docs:")
    
    return splitter.split_documents(docs)

# Step 3: Create vector store
def create_vectorstore(docs):
    embeddings = OllamaEmbeddings(model="llama3.2:3b")
    return Chroma.from_documents(docs, embeddings, persist_directory="./chroma_db")

# Step 4: Setup QA chain
def create_qa_chain():
    llm = OllamaLLM(model="llama3.2:3b")
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=OllamaEmbeddings(model="llama3.2:3b"))
    retriever = vectorstore.as_retriever()
    return RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)

def create_chat_chain():
    llm = OllamaLLM(model="llama3.2:3b")
    vectorstore = Chroma(persist_directory="./chrom_db", embedding_function=OllamaEmbeddings(model="llama3.2:3b"))
    retriever = vectorstore.as_retriever()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True
    )

# Main loop
def generate_summary():
        print("Indexing documents...")
        docs = load_documents()
        print(f"Loaded documents: {[doc.metadata for doc in docs]}")
        split_docs = split_documents(docs)
        for i, chunk in enumerate(split_docs):
            print(f"Chunk {i}: {chunk.page_content[:100]}")
        create_vectorstore(split_docs)
        qa = create_qa_chain()
        print("\nAnswer:\n", result["result"])
        #summary 
        query ="Give me a suggested reorganized file structure based on all my files and their contents. Structure in the following format {'folder': ['file1', 'file2']}"
        result = qa.invoke(query)
        print(result)

