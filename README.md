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


<!-- 
### Create docker image 
```
docker build -t stt-fastapi-image .      
```

### Run using the .env file
```
docker run --env-file .env  -p 8000:8000 stt-fastapi-image 
``` -->

### Run the docker compose

```
docker compose up --build
```

### Create a request for registering user in DB
```
http://localhost:8000/register
```

#### Body
```
{
    "username": "Mehak Noor Singh",
    "password": "pass@123",
    "fmno": 123456
}
```

### Validate Token to get id
```
http://localhost:8000/validate_token
```

#### Body
```
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjQ1ODY2N2U1LWJlMTUtNDU5Yy1iZTU5LTczMzE5ODBkZDE4OSIsInVzZXJuYW1lIjoiTWVoYWsgTm9vciBTaW5naCIsImZtbm8iOjMyODc2MiwiZXhwIjoxNzEzNTE5MDgxfQ.MpWCPEgPyvWg6IbJvEuq8YRgEcxFjUVUVK-xNwkg6_0"
}
```

