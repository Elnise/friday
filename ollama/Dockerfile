FROM ollama/ollama

WORKDIR .

COPY ./friday-llama3_1 ./friday-llama3_1
COPY entrypoint.sh ./entrypoint.sh

RUN apt-get update && rm -rf /var/lib/apt/lists/*

RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
