FROM python:3.7
ADD . /api
WORKDIR /api
RUN pip install -r ./requirements.txt
ENTRYPOINT ./run.py
