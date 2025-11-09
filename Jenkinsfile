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
                git branch: 'main', url: 'https://github.com/SAKSHITH22/flask-rds-app.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "🐳 Building Docker image..."
                sh '''
                    echo "➡️ Current directory: $(pwd)"
                    echo "➡️ Files: $(ls -1)"
                    docker build -t $DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG .
                '''
            }
        }

        stage('Push to DockerHub') {
            steps {
                echo "⬆️ Pushing image to DockerHub..."
                withCredentials([usernamePassword(credentialsId: 'dockerhub-token', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "🔐 Logging in to DockerHub..."
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push $DOCKER_USER/$IMAGE_NAME:$IMAGE_TAG
                        docker logout
                    '''
                }
            }
        }

        stage('Configure and Deploy to EKS') {
            steps {
                echo "☸️ Configuring kubectl and deploying app..."
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                    sh '''
                        echo "🔑 Setting up kubeconfig for EKS..."
                        aws eks update-kubeconfig --region $AWS_DEFAULT_REGION --name $CLUSTER_NAME

                        echo "🚀 Deploying new Docker image..."
                        kubectl set image deployment/flask-app-deployment flask-app=$DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG
                        echo "⏳ Waiting for rollout..."
                        kubectl rollout status deployment/flask-app-deployment

                        echo "✅ Deployment complete! Checking status..."
                        kubectl get pods -o wide
                        kubectl get svc flask-app-service
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completed successfully!"
            echo "🌐 Your app is live on AWS EKS LoadBalancer!"

            // ✅ FIX: Wrap in AWS credentials again so kubectl works here
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                sh '''
                    aws eks update-kubeconfig --region $AWS_DEFAULT_REGION --name $CLUSTER_NAME
                    kubectl get svc flask-app-service
                '''
            }
        }

        failure {
            echo "❌ Pipeline failed. Check console output for error details."
        }
    }
}
