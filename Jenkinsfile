
pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = 'ap-south-1'
        ECR_REGISTRY = '499989195436.dkr.ecr.ap-south-1.amazonaws.com'
        ECR_REPOSITORY = 'product-service'
        IMAGE_TAG = '1.0'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Jenkins checked out the source from GitHub'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'python3 --version'
                sh 'python3 -m venv .venv'
                sh '.venv/bin/python -m pip install --upgrade pip'
                sh '.venv/bin/python -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                sh '.venv/bin/python -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t product-service:1.0 .'
            }
        }
        stage('Trivy Security Scan') {
            steps {
                sh '''
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v "$HOME/.cache/trivy:/root/.cache/" \
                        aquasec/trivy:0.76.1 image \
                        --scanners vuln \
                        --severity CRITICAL \
                        --exit-code 1 \
                        product-service:1.0
                '''
            }
        }
        stage('Login to AWS ECR') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'aws-ecr-creds',
                    usernameVariable: 'AWS_ACCESS_KEY_ID',
                    passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                )]) {
                    sh '''
                        set +x
                        export AWS_DEFAULT_REGION=ap-south-1
                        aws ecr get-login-password --region "$AWS_DEFAULT_REGION" |
                            docker login --username AWS --password-stdin "$ECR_REGISTRY"
                    '''
                }
            }
        }

        stage('Push Image to AWS ECR') {
            steps {
                sh '''
                    docker tag product-service:$IMAGE_TAG \
                        $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

                    docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
                '''
            }
        }


        stage('Deploy to EC2') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'jenkins-ssm-deploy-creds',
                    usernameVariable: 'AWS_ACCESS_KEY_ID',
                    passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                )]) {
                    sh '''
                        set +x
                        set -e

                        export AWS_DEFAULT_REGION=ap-south-1

                        echo "Preparing EC2 deployment..."

                      cat > ssm-commands.json <<'EOF'
{
  "commands": [
    "set -e",
    "aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 499989195436.dkr.ecr.ap-south-1.amazonaws.com",
    "docker pull 499989195436.dkr.ecr.ap-south-1.amazonaws.com/product-service:1.0",
    "if docker inspect product-service >/dev/null 2>&1; then docker stop product-service; docker rm product-service; fi",
    "docker run -d --name product-service --restart unless-stopped -p 5000:5000 499989195436.dkr.ecr.ap-south-1.amazonaws.com/product-service:1.0",
    "for i in $(seq 1 15); do if curl -fsS http://localhost:5000/; then exit 0; fi; sleep 2; done",
    "echo Application health check failed",
    "exit 1"
  ]
}
EOF

                        COMMAND_ID=$(aws ssm send-command \
                            --instance-ids i-009945d6c8df46d10 \
                            --document-name AWS-RunShellScript \
                            --parameters file://ssm-commands.json \
                            --region "$AWS_DEFAULT_REGION" \
                            --query 'Command.CommandId' \
                            --output text)

                        echo "Deployment command ID: $COMMAND_ID"

                        for i in $(seq 1 30); do
                            STATUS=$(aws ssm get-command-invocation \
                                --command-id "$COMMAND_ID" \
                                --instance-id i-009945d6c8df46d10 \
                                --region "$AWS_DEFAULT_REGION" \
                                --query 'Status' \
                                --output text 2>/dev/null || true)

                            echo "Deployment status: $STATUS"

                            if [ "$STATUS" = "Success" ]; then
                                echo "EC2 deployment successful!"
                                exit 0
                            fi

                            if [ "$STATUS" = "Failed" ] || [ "$STATUS" = "Cancelled" ] || [ "$STATUS" = "TimedOut" ]; then
                                echo "EC2 deployment failed!"
                                aws ssm get-command-invocation \
                                    --command-id "$COMMAND_ID" \
                                    --instance-id i-009945d6c8df46d10 \
                                    --region "$AWS_DEFAULT_REGION"
                                exit 1
                            fi

                            sleep 5
                        done

                        echo "Deployment timed out while waiting for SSM."
                        exit 1
                    '''
                }
            }
        }



    }

    post {
        always {
            sh 'docker logout "$ECR_REGISTRY" || true'
        }
    }
}
