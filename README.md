# ShopSecure

**ShopSecure** is a serverless microservices backend built on AWS that demonstrates secure DevOps practices, infrastructure-as-code, and automated CI/CD pipelines. The system exposes authentication, product, and order APIs through API Gateway and processes requests using AWS Lambda functions.

---

# Architecture Overview

ShopSecure uses a **serverless microservices architecture**:

Client → API Gateway → Lambda Services → AWS Services

Services included:

* **Auth Service** – user authentication and JWT token management
* **Product Service** – product catalog APIs
* **Order Service** – order processing APIs

Each service runs as an independent **AWS Lambda function**.

Infrastructure is managed using **Terraform** and deployed automatically through **GitHub Actions CI/CD**.

---

# Repository Structure

```
shopsecure/
│
├── services/
│   ├── auth-service/
│   │   └── app.py
│   ├── product-service/
│   │   └── app.py
│   └── order-service/
│       └── app.py
│
├── terraform/
│   └── main.tf
│
├── tests/
│
├── dist/
│   └── (generated lambda packages)
│
├── requirements.txt
└── .github/workflows/pipeline.yml
```

---

# Features

* Serverless architecture using AWS Lambda
* Infrastructure as Code with Terraform
* Automated CI/CD using GitHub Actions
* Secure secret management using AWS Secrets Manager
* JWT authentication
* API Gateway routing
* Security scanning integrated into CI pipeline
* CloudWatch logging and monitoring
* X-Ray tracing enabled

---

# Technology Stack

Backend

* Python 3.11
* AWS Lambda
* Amazon API Gateway

Infrastructure

* Terraform
* AWS IAM
* AWS Secrets Manager
* AWS CloudWatch

DevOps

* GitHub Actions
* Automated CI/CD pipeline
* Security scanning tools

Security Tools Used

* Bandit (Python SAST)
* pip-audit (dependency scanning)
* Checkov (Terraform security)
* Gitleaks (secret scanning)

---

# CI/CD Pipeline

The GitHub Actions workflow performs the following stages:

1. Build

   * Install dependencies
   * Package Lambda functions
   * Upload artifacts

2. Test

   * Run unit tests using pytest
   * Enforce minimum coverage

3. Security Scan

   * Static code analysis
   * Dependency vulnerability scanning
   * Infrastructure security scanning
   * Secret detection

4. Deploy Staging

   * Terraform infrastructure deployment
   * Lambda code update

5. Deploy Production

   * Triggered after successful staging deployment

Pipeline triggers:

* Push to main branch
* Pull request to main branch

---

# Infrastructure

Terraform provisions the following AWS resources:

* API Gateway
* Lambda functions
* IAM roles and policies
* Secrets Manager secrets
* CloudWatch log groups
* API Gateway routes and integrations

Terraform state is stored in **S3 with DynamoDB state locking**.

---

# API Endpoints

Base URL:

```
https://<api-id>.execute-api.<region>.amazonaws.com/<environment>
```

Authentication endpoints

```
POST /auth/register
POST /auth/login
POST /auth/validate
```

Product endpoints

```
GET /products
POST /products
```

Order endpoints

```
GET /orders
POST /orders
```

---

# Authentication

Authentication is implemented using **JWT tokens**.

The JWT signing key is securely stored in **AWS Secrets Manager**.

Flow:

1. User logs in through `/auth/login`
2. Auth Lambda validates credentials
3. Lambda signs JWT using secret from Secrets Manager
4. Token returned to client
5. Client includes token in future requests

---

# Security Practices

ShopSecure follows DevSecOps principles:

* Least privilege IAM roles
* Secrets stored in AWS Secrets Manager
* Automated vulnerability scanning in CI pipeline
* Terraform infrastructure security scanning
* Secret detection using Gitleaks
* CloudWatch logging enabled
* X-Ray tracing for observability

---

# Running Locally

Create virtual environment

```
python3 -m venv venv
source venv/bin/activate
```

Install dependencies

```
pip install -r requirements.txt
```

Run tests

```
pytest tests/
```

---

# Deployment

Infrastructure is deployed using Terraform.

Initialize Terraform

```
terraform init
```

Deploy staging

```
terraform apply -var="environment=staging"
```

Deploy production

```
terraform apply -var="environment=production"
```

Lambda code deployment is handled by the CI/CD pipeline.

---

# Environment Variables

| Variable    | Description            |
| ----------- | ---------------------- |
| AWS_REGION  | AWS region             |
| ENVIRONMENT | deployment environment |

---

# Observability

Logs are available in **CloudWatch Log Groups**.

Each Lambda has its own log group:

```
/aws/lambda/shopsecure-<env>-auth-service
/aws/lambda/shopsecure-<env>-product-service
/aws/lambda/shopsecure-<env>-order-service
```

Distributed tracing is enabled using AWS X-Ray.

---

# Future Improvements

* Add DynamoDB database
* Implement API Gateway authorizers
* Enable JWT validation middleware
* Implement rate limiting
* Add monitoring dashboards
* Add secret rotation

---

# License

This project is for educational and demonstration purposes.
