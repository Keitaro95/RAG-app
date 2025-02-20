# 3.11-busterから変更
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1

WORKDIR /src

# 最新の SQLite3 と libsqlite3-dev をインストール
RUN apt-get update && apt-get install -y sqlite3 libsqlite3-dev

RUN pip install poetry

# # pysqlite3-binary をインストール
# RUN pip install pysqlite3-binary

# docker内にpoetry関連ファイルをコピーして、poetryの内容で環境構築する
COPY pyproject.toml* poetry.lock* ./

RUN poetry config virtualenvs.in-project true
RUN if [ -f pyproject.toml ]; then poetry install --no-root; fi

ENTRYPOINT ["poetry", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--reload"]