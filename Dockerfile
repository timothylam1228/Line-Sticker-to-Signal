FROM python:latest
RUN apt-get update -y
RUN apt-get install software-properties-common -y
RUN apt-add-repository ppa:savoury1/ffmpeg4 -y
RUN apt-add-repository ppa:savoury1/ffmpeg5 -y
RUN apt-get upgrade -y
RUN apt-get install -y ffmpeg
COPY app /app
WORKDIR /app
RUN mkdir /output
RUN pip install -r ./requirements.txt
CMD [ "python", "./start.py" ]
