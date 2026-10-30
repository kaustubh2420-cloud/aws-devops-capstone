
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

        stage('Test SSM Deployment Connection') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'jenkins-ssm-deploy-creds',
                    usernameVariable: 'AWS_ACCESS_KEY_ID',
                    passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                )]) {
                    sh '''
                        set +x
                        export AWS_DEFAULT_REGION=ap-south-1

                        aws sts get-caller-identity

                        COMMAND_ID=$(aws ssm send-command \
                            --instance-ids i-009945d6c8df46d10 \
                            --document-name AWS-RunShellScript \
                            --parameters '{"commands":["echo Jenkins SSM connectivity test successful"]}' \
                            --region "$AWS_DEFAULT_REGION" \
                            --query 'Command.CommandId' \
                            --output text)

                        echo "SSM test command submitted: $COMMAND_ID"
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
