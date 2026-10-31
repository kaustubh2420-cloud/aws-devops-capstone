pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = 'ap-south-1'
        ECR_REGISTRY = '499989195436.dkr.ecr.ap-south-1.amazonaws.com'
        ECR_REPOSITORY = 'product-service'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Source checked out from GitHub'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 --version
                    python3 -m venv .venv
                    .venv/bin/python -m pip install --upgrade pip
                    .venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '.venv/bin/python -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t product-service:$IMAGE_TAG .
                '''
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
                        product-service:$IMAGE_TAG
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

                    docker push \
                        $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
                '''
            }
        }

        stage('Production Approval') {
            steps {
                timeout(time: 30, unit: 'MINUTES') {
                    input message: "Approve deployment of Product Service image ${IMAGE_TAG} to EC2?",
                          ok: 'Approve Deployment'
                }
            }
        }

        stage('Deploy to EC2 with Automatic Rollback') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'jenkins-ssm-deploy-creds',
                    usernameVariable: 'AWS_ACCESS_KEY_ID',
                    passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                )]) {
                    sh '''
                        set +x
                        set -e
                        export IMAGE_TAG="$BUILD_NUMBER"

                        cat > /tmp/deploy-ec2.sh <<'DEPLOY_EOF'
#!/bin/bash
set -e

REGISTRY="499989195436.dkr.ecr.ap-south-1.amazonaws.com"
NEW_IMAGE="$REGISTRY/product-service:__IMAGE_TAG__"

echo "New image: $NEW_IMAGE"

OLD_IMAGE=$(docker inspect --format='{{.Config.Image}}' product-service 2>/dev/null || true)

echo "Previous image: ${OLD_IMAGE:-none}"

# Pull the new release before stopping the current application.
docker pull "$NEW_IMAGE"

# Replace the currently running container.
docker rm -f product-service 2>/dev/null || true

if docker run -d \
    --name product-service \
    --restart unless-stopped \
    -p 5000:5000 \
    "$NEW_IMAGE"; then

    for i in $(seq 1 15); do
        if curl -fsS http://localhost:5000/; then
            echo "New deployment is healthy."
            exit 0
        fi
        sleep 2
    done
fi

echo "New deployment failed. Starting rollback."

docker rm -f product-service 2>/dev/null || true

if [ -n "$OLD_IMAGE" ]; then
    echo "Restoring previous image: $OLD_IMAGE"

    if docker run -d \
        --name product-service \
        --restart unless-stopped \
        -p 5000:5000 \
        "$OLD_IMAGE"; then

        for i in $(seq 1 15); do
            if curl -fsS http://localhost:5000/; then
                echo "Rollback successful. Previous version restored."
                exit 1
            fi
            sleep 2
        done
    fi
fi

echo "Rollback could not restore a healthy application."
exit 1
DEPLOY_EOF

                        python3 - <<'PY'
import json
import os

with open('/tmp/deploy-ec2.sh') as f:
    script = f.read()

script = script.replace('__IMAGE_TAG__', os.environ['IMAGE_TAG'])

with open('ssm-commands.json', 'w') as f:
    json.dump({"commands": [script]}, f)
PY

                        python3 -m json.tool ssm-commands.json >/dev/null

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

                            if [ "$STATUS" = "Failed" ] || \
                               [ "$STATUS" = "Cancelled" ] || \
                               [ "$STATUS" = "TimedOut" ]; then

                                echo "EC2 deployment failed or rollback was triggered."

                                aws ssm get-command-invocation \
                                    --command-id "$COMMAND_ID" \
                                    --instance-id i-009945d6c8df46d10 \
                                    --region "$AWS_DEFAULT_REGION" \
                                    --output json

                                exit 1
                            fi

                            sleep 5
                        done

                        echo "Timed out waiting for SSM deployment."
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
