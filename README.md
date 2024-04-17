# HOW TO RUN LOCALLY


### Create an .env file with format
```
OPENAI_BASE_URL=https://openai.prod.ai-..............

OPENAI_API_KEY=eyJ..........

AWS_ACCESS_KEY_ID=A........

AWS_SECRET_ACCESS_KEY=D........

AWS_SESSION_TOKEN=F..........

S3_BUCKET=...........
```



### Create docker image 
```
docker build -t stt-fastapi-image .      
```

### Run using the .env file
```
docker run --env-file .env  -p 8000:8000 stt-fastapi-image 
```
