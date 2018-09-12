FROM python:3.7
ADD . /api
WORKDIR /api
# RUN apt-get update && apt-get install -y chromium
# CMD chromium --no-sandbox --incognito --remote-debugging-port=9222 --headless --disable-gpu --disable-software-rasterizer
RUN pip install -r ./requirements.txt
ENTRYPOINT ./run.py
