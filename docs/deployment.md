# Deployment Guide — AI Mock Interview

This guide covers two setups:
- **Local development** — Docker Compose with PostgreSQL + MinIO (S3 emulator)
- **Production on AWS EC2** — Docker Compose with PostgreSQL container + real AWS S3

---

## Prerequisites

- Docker and Docker Compose installed
- Git
- An AWS account (for production)

---

## Local Development

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd ai_mock_interview
```

### 2. Create the backend env file

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
JWT_SECRET_KEY=your-local-secret-key
ENV=dev
API_PREFIX=/api/v1
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/mock_interview_db
AWS_REGION=us-east-1
S3_RESUME_BUCKET=ai-interview-test
```

> `ENV=dev` tells the app to use MinIO instead of real AWS S3.

### 3. Start all services

```bash
docker compose up --build
```

This starts:
- `api` — FastAPI on `http://localhost:8000`
- `db` — PostgreSQL on port `5432`
- `minio` — MinIO on `http://localhost:9000` (console at `http://localhost:9001`)

### 4. Run database migrations

```bash
docker compose exec api alembic upgrade head
```

### 5. Create the MinIO bucket

Open `http://localhost:9001`, log in with `minio / minio123`, and create a bucket named `ai-interview-test`.

### 6. Verify

```bash
curl http://localhost:8000/api/v1/health
# → {"status": "ok"}
```

---

## Production — AWS EC2

### AWS Prerequisites

#### A. Create an S3 bucket

1. Go to **S3** in the AWS console
2. Click **Create bucket**
3. Name it (e.g. `ai-mock-interview-resumes`), choose a region
4. Block all public access — leave enabled
5. Note the bucket name and region

#### B. Create an IAM Role for EC2

1. Go to **IAM → Roles → Create role**
2. Trusted entity: **AWS service → EC2**
3. Attach policy: **AmazonS3FullAccess** (later scope to your bucket only)
4. Name it `ec2-ai-mock-interview-role`

> With an IAM Role, the EC2 instance can access S3 without any access keys in your env file — boto3 picks up credentials automatically from instance metadata.

#### C. Launch an EC2 instance

1. Go to **EC2 → Launch Instance**
2. Choose **Ubuntu Server 22.04 LTS**
3. Instance type: `t3.small` (recommended) or `t3.micro` (free tier)
4. Under **Advanced Details → IAM instance profile**, select `ec2-ai-mock-interview-role`
5. **Security Group** — add inbound rules:
   | Type | Port | Source |
   |------|------|--------|
   | SSH  | 22   | Your IP |
   | Custom TCP | 8000 | 0.0.0.0/0 |
6. Create or select a key pair — download the `.pem` file
7. Launch the instance

---

### EC2 Setup

SSH into your instance:

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
```

#### Install Docker

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker ubuntu
newgrp docker
```

Verify:

```bash
docker --version
docker compose version
```

#### Clone the repo

```bash
git clone <your-repo-url>
cd ai_mock_interview
```

#### Create the production env file

```bash
cp backend/.env.example backend/.env.prod
nano backend/.env.prod
```

Fill in:

```env
JWT_SECRET_KEY=<generate-with: openssl rand -hex 32>
ENV=prod
API_PREFIX=/api/v1
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/mock_interview_db
AWS_REGION=us-east-1
S3_RESUME_BUCKET=ai-mock-interview-resumes
```

> Do NOT set `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` — the IAM Role handles this automatically.

#### Start the production stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

#### Run database migrations

```bash
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

#### Verify

```bash
curl http://localhost:8000/api/v1/health
# or from your machine:
curl http://<EC2-PUBLIC-IP>:8000/api/v1/health
```

---

## Environment Variable Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET_KEY` | Yes | Secret for signing JWTs. Generate with `openssl rand -hex 32` |
| `ENV` | Yes | `dev` (uses MinIO) or `prod` (uses real AWS S3) |
| `API_PREFIX` | Yes | URL prefix, e.g. `/api/v1` |
| `OPENAI_API_KEY` | Yes | OpenAI API key for resume parsing |
| `DATABASE_URL` | Yes | Full asyncpg connection string |
| `AWS_REGION` | Yes | AWS region for S3, e.g. `us-east-1` |
| `S3_RESUME_BUCKET` | Yes | S3 bucket name for resume uploads |

---

## Useful Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f api

# Restart the API
docker compose -f docker-compose.prod.yml restart api

# Stop everything
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (deletes DB data)
docker compose -f docker-compose.prod.yml down -v

# Open a shell inside the container
docker compose -f docker-compose.prod.yml exec api bash
```

---

## Troubleshooting

**Container won't start**
```bash
docker compose -f docker-compose.prod.yml logs api
```

**Database connection refused**
- Make sure the `db` container is healthy before the `api` starts (the compose file handles this with `depends_on: condition: service_healthy`)
- Check `DATABASE_URL` uses `db` as the hostname, not `localhost`

**S3 upload fails in production**
- Confirm the EC2 instance has the IAM Role attached (EC2 console → Instance → Security tab)
- Confirm the role has S3 access to your bucket
- Check `AWS_REGION` and `S3_RESUME_BUCKET` match what's in the AWS console

**Resume parsing stuck at `processing`**
- Check API logs for OpenAI API errors
- Verify `OPENAI_API_KEY` is set correctly in the env file
