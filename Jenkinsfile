pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t expense-tracker:%BUILD_NUMBER% .'
            }
        }
    }

    post {
        success {
            echo 'EXPENSE TRACKER CI PIPELINE SUCCESS'
        }

        failure {
            echo 'EXPENSE TRACKER CI PIPELINE FAILURE'
        }
    }
}
