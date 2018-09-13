FROM python:3.7
ADD . /api
WORKDIR /api
RUN pip install -r ./requirements.txt
CMD ping chromium
ENTRYPOINT ./run.py
