## Running Ollama Third-Party Service

## Setup a docker container with a persistent volume to store the model(s)
docker pull ollama/ollama
# create a persistent volume for the downloaded model
docker volume create ollama_data
# run container in interactive mode in order to download the model(s)
docker run --runtime=nvidia -it --name ollama_container -p 11434:11434 -h 0.0.0.0 --mount type=volume,source=ollama_data,target=/root/.ollama ollama/ollama:latest
# connect and download model(s)
docker exec -it ollama_container /bin/bash
ollama pull deepseek-r1
ls /root/.ollama/models/manifests/registry.ollama.ai/library
# stop the container and restart it in detached mode, check that model download(s) are still there
docker stop ollama_container
docker start ollama_container
docker exec -it ollama_container /bin/bash
# confirm downloaded models still exist (y)
ls /root/.ollama/models/manifests/registry.ollama.ai/library
du -h /root/.ollama/models
# get network details (wls2 IP)
wsl hostname -I
= 172.19.68.159 172.17.0.1
# install network tools in the container
docker exec -it ollama_container /bin/bash
apt-get update
apt-get install net-tools
ifconfig
netstat -an|grep 11434

# now test the model:
# verify model is loaded
curl -X POST http://172.19.68.159:11434/api/generate -H "Content-Type: application/json" -d '{
  "model": "deepseek-r1"
}'

# can also use localhost instead of wls2 ip
curl -X POST http://localhost:11434/api/generate -H "Content-Type: application/json" -d '{
  "model": "deepseek-r1"
}'

# test API char response
curl -X POST http://localhost:11434/api/generate -H "Content-Type: application/json" -d '{
  "model": "deepseek-r1",
  "prompt": "Why is the sky blue?"
}'

# generate a chat completion
curl -X POST http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{
  "model": "deepseek-r1",
  "messages": [
    {"role": "user", "content": "Why is the sky blue?"}
  ]
}'

# Example alternative model that I may download later: llama3.2

# Next investigate the OPEA components.
# vLLM, TGI (Text Generation Inference), and Ollama offer APIs with OpenAI compatibility.

# Convert to Docker compose:
Create docker-compose.yaml
-------
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: jaeger
    ports:
      - "16686:16686"
      - "4317:4317"
      - "4318:4318"
      - "9411:9411"
    ipc: host
    environment:
      no_proxy: ${no_proxy}
      http_proxy: ${http_proxy}
      https_proxy: ${https_proxy}
      COLLECTOR_ZIPKIN_HOST_PORT: 9411
    restart: unless-stopped
  ollama-server:
    image: ollama/ollama:latest
    runtime: nvidia
    ports:
      - ${LLM_ENDPOINT_PORT:-8008}:11434
    hostname: 0.0.0.0
    volumes:
      - ollama_data:/root/.ollama
    environment:
      no_proxy: ${no_proxy}
      http_proxy: ${http_proxy}
      https_proxy: ${https_proxy}
      LLM_MODEL_ID: ${LLM_MODEL_ID}
      host_ip: ${host_ip}

volumes:
  ollama_data:

networks:
  default:
    driver: host

----------------------
docker stop ollama_container
cd /mnt/d/free-genai-bootcamp-2025/local-dev/github/opea-comps/mega-service
LLM_ENDPOINT_PORT=9000 docker compose up

# encountered error for port 9411, in excluded list:
netsh int ipv4 show excludedportrange protocol=tcp

# Change line (and mapping line for 9411:9411):
      COLLECTOR_ZIPKIN_HOST_PORT: 9411
# To:
      COLLECTOR_ZIPKIN_HOST_PORT: 11433

# restart:
LLM_ENDPOINT_PORT=9000 docker compose up

# open jaeger
http://127.0.0.1:16686/search


curl http://localhost:9000/api/pull -d '{
  "model": "llama3.2:1b"
}'
curl http://localhost:9000/api/pull -d '{
  "model": "deepseek-r1"
}'

## create virtual environment
cd /mnt/d/free-genai-bootcamp-2025/local-dev
mkdir workspaces
cd workspaces
python3 -m venv venv
## activate
source venv/bin/activate

cd /mnt/d/free-genai-bootcamp-2025/local-dev/github/opea-comps/mega-service/

pip install -r requirements.txt

# create the application app.py

python3 app.py

# test application:

# llama3.2:1b model
curl -X POST http://localhost:8000/v1/example-service \
-H "Content-Type: application/json" \
-d '{
  "messages": [
    {
      "role": "user",
      "content": "Hello, this is a test message"
    },
    {
      "role": "assistant",
      "content": "No response content available"
    },
    {
      "role": "user",
      "content": "Why is the sky blue?"
    }
  ],
  "stream": false,
  "model": "llama3.2:1b",
  "max_tokens": 100,
  "temperature": 0.7
}' | jq '.' > output/$(date +%s)-response.json

# deepseek-r1 model
curl -X POST http://localhost:8000/v1/example-service \
-H "Content-Type: application/json" \
-d '{
  "messages": [
    {
      "role": "user",
      "content": "Hello, this is a test message"
    },
    {
      "role": "assistant",
      "content": "No response content available"
    },
    {
      "role": "user",
      "content": "Why is the sky blue?"
    }
  ],
  "stream": false,
  "model": "deepseek-r1",
  "max_tokens": 100,
  "temperature": 0.7
}' | jq '.' > output/$(date +%s)-response.json


# next install Code Rabbit and explore the software

