# Create image of python
FROM --platform=linux/arm64 python:3.12

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

# install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

