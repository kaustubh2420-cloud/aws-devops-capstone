# AWS DevOps CI/CD Pipeline – Product Service

## Project Overview

This project demonstrates an automated CI/CD pipeline for a Python Flask-based Product Service using Jenkins, Docker, AWS, and Trivy.

The pipeline automates code checkout, dependency installation, application testing, Docker image creation, vulnerability scanning, image publishing to Amazon ECR, production approval, and deployment to an Amazon EC2 instance.

It also includes automatic rollback logic intended to restore the previous application image if a new deployment fails its health check.

## Architecture

Developer → GitHub → Jenkins → Automated Tests → Docker Build → Trivy Scan → Amazon ECR → Production Approval → AWS Systems Manager → Amazon EC2

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development |
| Flask | REST API |
| Pytest | Automated testing |
| Git & GitHub | Source code management |
| Jenkins | CI/CD automation |
| Docker | Containerization |
| Trivy | Container vulnerability scanning |
| AWS ECR | Docker image registry |
| AWS EC2 | Application hosting |
| AWS Systems Manager | Remote deployment |
| AWS IAM | Access management |

## Application Features

The Product Service provides the following endpoints:

| Endpoint | Description |
|---|---|
| `GET /` | Application health check |
| `GET /products` | Returns all products |
| `GET /products/search?name=Laptop` | Searches products by name |

The application currently uses sample product data stored in memory.

## CI/CD Pipeline Stages

1. **Source Checkout:** Jenkins retrieves the source code from GitHub.
2. **Dependency Installation:** Installs Python application dependencies.
3. **Automated Testing:** Runs Pytest to validate application functionality.
4. **Docker Build:** Builds the application Docker image.
5. **Security Scanning:** Trivy scans the Docker image for CRITICAL severity vulnerabilities.
6. **ECR Authentication:** Jenkins authenticates with Amazon ECR.
7. **Image Push:** Publishes the versioned Docker image to Amazon ECR.
8. **Production Approval:** Requires manual approval before production deployment.
9. **EC2 Deployment:** AWS Systems Manager executes deployment commands on EC2.
10. **Health Check and Rollback:** Checks the deployed application and attempts to restore the previous image if the health check fails.

## AWS Infrastructure

- AWS Region: `ap-south-1`
- Container Registry: Amazon ECR
- Compute: Amazon EC2
- Remote execution: AWS Systems Manager
- Access control: AWS IAM

## Docker Image Versioning

Each Jenkins build uses its build number as the Docker image tag.

Example:

`product-service:11`

This allows different pipeline builds to be identified and deployed independently.

## Deployment Verification

The deployment was successfully verified on EC2 using AWS Systems Manager.

Verified running image:

`499989195436.dkr.ecr.ap-south-1.amazonaws.com/product-service:11`

Jenkins deployment result: `SUCCESS`

## Automated Testing

The project includes five Pytest test cases:

- Health endpoint validation
- Product listing validation
- Product search validation
- Case-insensitive product search
- Missing search parameter validation

All five tests passed in the successful pipeline run.

## Security

Trivy is integrated into the CI/CD pipeline to scan the Docker image for CRITICAL severity vulnerabilities.

Note: The configured scan checks CRITICAL severity findings; it does not represent a scan with zero vulnerabilities at every severity level.

## Rollback

The deployment script captures the currently running image before deploying a new version. If the new application fails its health check, the script attempts to restore the previous image.

The rollback logic is implemented but still requires a controlled failure test to verify its behaviour.

## Future Improvements

- Add SonarQube code quality analysis.
- Expand the application into multiple microservices.
- Add Docker Compose orchestration.
- Add monitoring using Prometheus and Grafana.
- Add notifications for pipeline results.
- Test and document automatic rollback.

## Project Status

The main CI/CD pipeline has successfully deployed the Product Service to AWS EC2 using Jenkins, Docker, Amazon ECR, and AWS Systems Manager.

**Project focus:** AWS Cloud and DevOps CI/CD Automation.
