FROM python:3-slim

RUN apt update
RUN apt -y install git

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT [ "python", "./main.py" ]
CMD []
