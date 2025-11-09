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

        // ✅ Fixed: Git checkout (explicit branch = main)
        stage('Checkout Code') {
            steps {
                echo "📦 Cloning Flask app repo from GitHub..."
                git branch: 'main', url: 'https://github.com/SAKSHITH22/flask-rds-app.git'
            }
        }

        // 🐳 Build the Docker image
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

        // ✅ FIXED: Push image to DockerHub using username+password credentials
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

        // ☸️ Configure kubectl for AWS EKS
        stage('Configure Kubectl') {
            steps {
                echo "🔑 Configuring kubectl with EKS credentials..."
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                    sh '''
                        aws eks update-kubeconfig --region $AWS_DEFAULT_REGION --name $CLUSTER_NAME
                        kubectl get nodes
                    '''
                }
            }
        }

        // 🚀 Deploy the app to EKS
        stage('Deploy to EKS') {
            steps {
                echo "🚀 Deploying latest image to EKS..."
                sh '''
                    set -e
                    kubectl set image deployment/flask-app-deployment flask-app=$DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG --record
                    echo "⏳ Waiting for rollout to finish..."
                    kubectl rollout status deployment/flask-app-deployment
                '''
            }
        }

        // 🔍 Verify deployment
        stage('Verify Deployment') {
            steps {
                echo "🔍 Checking EKS status..."
                sh '''
                    echo "➡️ Service status:"
                    kubectl get svc flask-app-service
                    echo "➡️ Pod status:"
                    kubectl get pods -o wide
                '''
            }
        }
    }

    // ✅ Post-build actions
    post {
        success {
            echo "✅ Pipeline completed successfully!"
            echo "🌐 Your app is live on AWS EKS LoadBalancer!"
            sh 'kubectl get svc flask-app-service'
        }
        failure {
            echo "❌ Pipeline failed. Check console output for error details."
        }
    }
}
