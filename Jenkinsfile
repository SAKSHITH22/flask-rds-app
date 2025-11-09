pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = "us-east-1"
        CLUSTER_NAME = "sakshith_01-cluster"
        DOCKERHUB_USER = "sakshith123"
        IMAGE_NAME = "flask-rds-app"
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo "📦 Cloning Flask app repo from GitHub..."
                git 'https://github.com/SAKSHITH22/flask-rds-app.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "🐳 Building Docker image..."
                sh 'docker build -t $DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG .'
            }
        }

        stage('Push to DockerHub') {
            steps {
                echo "⬆️ Pushing image to DockerHub..."
                withCredentials([string(credentialsId: 'dockerhub-token', variable: 'DOCKERHUB_PASS')]) {
                    sh '''
                        echo $DOCKERHUB_PASS | docker login -u $DOCKERHUB_USER --password-stdin
                        docker push $DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG
                    '''
                }
            }
        }

        stage('Configure Kubectl') {
            steps {
                echo "🔑 Configuring kubectl with EKS credentials..."
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                    sh 'aws eks update-kubeconfig --region $AWS_DEFAULT_REGION --name $CLUSTER_NAME'
                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                echo "🚀 Deploying to EKS..."
                sh '''
                    kubectl set image deployment/flask-app-deployment flask-app=$DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG --record
                    kubectl rollout status deployment/flask-app-deployment
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                echo "🔍 Verifying service..."
                sh '''
                    kubectl get svc flask-app-service
                    kubectl get pods -o wide
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Deployment successful!"
        }
        failure {
            echo "❌ Pipeline failed. Check console output for details."
        }
    }
}
