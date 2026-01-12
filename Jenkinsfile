pipeline {
    agent any

    environment {
        REPOHOST = 'registry.biergartenrajis.fi'
        IMAGE = 'ruuvi2mqtt'
        DISTRO = 'alpine'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                script {
                    echo "Running unit tests"
                    sh 'make test'
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    echo "Building Docker image for ${env.REPOHOST}"
                    sh 'make build REPOHOST=${REPOHOST}'
                }
            }
        }

        stage('Push') {
            steps {
                script {
                    echo "Pushing Docker image to ${env.REPOHOST}"
                    sh 'make push REPOHOST=${REPOHOST}'
                }
            }
        }
    }

    post {
        success {
            echo 'Build and push completed successfully!'
        }
        failure {
            echo 'Build or push failed!'
        }
        always {
            cleanWs()
        }
    }
}
