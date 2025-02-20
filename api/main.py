# ここで pysqlite3 の上書きを試みる（必要に応じて）
try:
    import pysqlite3 as sqlite3
    import sys
    # sqlite3 が既にインポートされていなければ上書き
    if "sqlite3" not in sys.modules or sys.modules["sqlite3"].sqlite_version_info < (3, 35, 0):
        sys.modules["sqlite3"] = sqlite3
        print("sqlite3 module is overridden by pysqlite3")
except ImportError:
    print("pysqlite3 not installed, using built-in sqlite3")

import os
import requests
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import openai


from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser



# OpenAI API キー
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]


# リクエストで使用するモデルの定義
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]


embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
persist_directory = "../db/chroma/chroma_v0_250218.sqlite3"
chroma_db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

# Chroma のインデックスを retriever として利用
retriever = chroma_db.as_retriever()

# プロンプトテンプレートを定義
prompt = ChatPromptTemplate.from_template('''\
以下の文脈だけを踏まえて質問に回答してください。

文脈: """
{context}
"""

質問: {question}
''')

# 使用するLLMを定義（例：gpt-4o-mini）
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Chain の構築
# Chain の入力は辞書形式で、「question」キーには RunnablePassthrough() によりクエリがそのまま渡され、
# 「context」キーには retriever による検索結果が自動的に取得されます。
chain = (
    {"question": RunnablePassthrough(), "context": retriever}
    | prompt
    | model
    | StrOutputParser()
)

# FastAPI アプリケーションの定義
app = FastAPI()

@app.post("/chat")
async def generate_answer(request: ChatRequest):
    """
    Next.js からのPOSTリクエストを受け取り、Chroma のインデックスから関連文脈を検索、
    LLM による回答生成（RAG）を実行し、その結果を返すエンドポイント
    """
    try:
        # 最新のメッセージの内容をクエリとして使用
        query = request.messages[-1].content

        # Chain にクエリを渡して回答を生成（Chainの入力は辞書形式）
        result = chain.invoke(query)
        
        return JSONResponse(
            content={"response": result},
            status_code=200,
            media_type="application/json"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
