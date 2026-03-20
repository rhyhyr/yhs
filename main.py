from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

from langchain_community.vectorstores import FAISS

import glob

# 1. PDF 로드
# PDF 파일 목록 가져오기 (sample 폴더 안 모든 pdf)
pdf_files = glob.glob("pdf/*.pdf")  # 폴더 경로 수정

all_documents = []

# 1. PDF마다 로드
for file in pdf_files:
    loader = PyPDFLoader(file)
    docs = loader.load()
    all_documents.extend(docs)

# 2. 텍스트 쪼개기 (chunking)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)
docs = text_splitter.split_documents(all_documents)

# 3. 임베딩 (벡터화)
embedding = OpenAIEmbeddings()

# 4. 벡터 DB 저장 (FAISS)
db = FAISS.from_documents(docs, embedding)

# 5. 질문 입력
query = input("질문 입력: ")

# 6. 관련 문서 검색
retriever = db.as_retriever(search_kwargs={"k": 3})
retrieved_docs = retriever.invoke(query)

print("\n[검색된 문서 일부]")
for i, doc in enumerate(retrieved_docs):
    print(f"\n--- 문서 {i+1} ---")
    print(doc.page_content[:200])

# 7. LLM으로 답변 생성
llm = ChatOpenAI(model="gpt-4o-mini")

context = "\n\n".join([doc.page_content for doc in retrieved_docs])

prompt = f"""
다음 문서를 기반으로 질문에 답해라.

문서:
{context}

질문:
{query}
"""

response = llm.invoke(prompt)

print("\n[최종 답변]")
print(response.content)