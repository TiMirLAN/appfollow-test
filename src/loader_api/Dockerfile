FROM python:3.7
ADD . /api
WORKDIR /api
#RUN apt-get update && apt-get install -y apt-utils && apt-get install -y python3-lxml
RUN pip install lxml
RUN pip install -r ./requirements.txt
CMD ping chromium
ENTRYPOINT ./run.py
