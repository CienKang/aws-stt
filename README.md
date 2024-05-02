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


### just compose up 
```
docker compose up --build
```


### Steps to deploy on ec2 instance

1. Upgrade the existing packages
```
sudo apt update -y
sudo apt upgrade -y
```

2. Install docker

```
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo chmod 777 /var/run/docker.sock
```

3. Clone the repo inside ec2 instance
```
git clone https://github.com/CienKang/aws-stt.git
cd aws-stt
git fetch
``` 

4. Create the .env file and update the contents inside it.
```
touch .env
vi .env
```

5. Run the docker compose up
```
docker compose up
```
