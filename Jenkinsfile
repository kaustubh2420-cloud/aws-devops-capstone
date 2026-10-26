pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Source code is available in the workspace'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'python3 --version'
                sh 'python3 -m pip --version'
                sh 'python3 -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'python3 -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t product-service:1.0 .'
            }
        }
    }
}
