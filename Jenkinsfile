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

        stage('Python Environment') {
            steps {
                bat '"C:\\Users\\Atharva\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" --version'
bat '"C:\\Users\\Atharva\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" -m venv .venv'
                bat '.venv\\Scripts\\python.exe -m pip install --upgrade pip'
                bat '.venv\\Scripts\\python.exe -m pip install -r requirements.txt'
            }
        }

        stage('Test Application') {
            steps {
                bat '.venv\\Scripts\\python.exe -m py_compile app.py'
                bat '.venv\\Scripts\\python.exe -c "import app; app.init_db(); client=app.app.test_client(); response=client.get(\'/\'); assert response.status_code == 200, response.status_code; print(\'Flask smoke test passed\')"'
            }
        }

        stage('Docker Check') {
            steps {
                bat 'docker version'
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