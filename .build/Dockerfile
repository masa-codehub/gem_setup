# Python環境とgemini-cliを含むDockerfile
FROM python:3.13.3-slim-bullseye

# 作業ディレクトリを作成・設定
WORKDIR /app

# RUN命令を一つにまとめることでDockerイメージのレイヤー数を削減
RUN apt-get update && \
    apt-get install -y git && \
    apt-get install -y curl gnupg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# gemini-cliをグローバルにインストール
RUN npm install -g @google/gemini-cli

# 必要なPythonパッケージのインストール
RUN pip install --upgrade pip
COPY requirements.in .
RUN pip install pip-tools
RUN pip-compile requirements.in
RUN pip install --no-cache-dir -r requirements.txt


# # 開発モード
# COPY pyproject.toml .
# RUN pip install -e .

# Pythonが.pycファイルを生成しないようにします。
ENV PYTHONDONTWRITEBYTECODE=1
# Pythonの出力がバッファリングされないようにします。
ENV PYTHONUNBUFFERED=1
