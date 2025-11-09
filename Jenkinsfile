pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = "us-east-1"
        CLUSTER_NAME = "sakshith_01-cluster"
        DOCKERHUB_USER = "sakshith123"
        IMAGE_NAME = "flask-rds-app"
        IMAGE_TAG = "v${BUILD_NUMBER}"
        DEPLOYMENT_FILE = "deployment.yaml"
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
                // Uses username+password credential type already configured in Jenkins
                withCredentials([usernamePassword(credentialsId: 'dockerhub-token', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    retry(3) {
                        sh '''
                            echo "🔐 Logging in to DockerHub..."
                            echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                            docker push $DOCKER_USER/$IMAGE_NAME:$IMAGE_TAG
                            docker logout
                        '''
                    }
                }
            }
        }

        stage('Update Kubernetes YAML') {
            steps {
                echo "🔧 Updating $DEPLOYMENT_FILE with image: $DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG"
                // Replace the image line in deployment.yaml (works if image appears as "<user>/<name>:<tag>" or similar)
                sh '''
                    if grep -q "image:" $DEPLOYMENT_FILE; then
                      # Replace any existing image line for this image name
                      sed -i "s|image: .*${IMAGE_NAME}:.*|image: ${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}|g" $DEPLOYMENT_FILE || true
                    else
                      echo "Warning: no image line found in $DEPLOYMENT_FILE"
                    fi
                    echo "---- deployment.yaml (excerpt) ----"
                    grep -E "image:|name:|containerPort" -n $DEPLOYMENT_FILE || true
                '''
            }
        }

        stage('Configure and Deploy to EKS') {
            steps {
                echo "☸️ Configuring kubectl and deploying app..."
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                    // Wrap the whole deploy into a retry to handle transient API errors
                    retry(3) {
                        sh '''
                            echo "🔑 Setting up kubeconfig for EKS..."
                            aws eks update-kubeconfig --region $AWS_DEFAULT_REGION --name $CLUSTER_NAME

                            echo "🚀 Applying Kubernetes manifest..."
                            kubectl apply -f $DEPLOYMENT_FILE

                            echo "⏳ Waiting for rollout to finish..."
                            kubectl rollout status deployment/flask-app-deployment --timeout=3m

                            echo "✅ Deployment complete! Checking status..."
                            kubectl get pods -o wide
                            kubectl get svc flask-app-service || true
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            echo "🧹 Cleaning up local docker system to free space..."
            // best-effort cleanup; avoid failing pipeline on prune errors
            sh 'docker system prune -af || true'
        }

        success {
            echo "✅ Pipeline completed successfully!"
            echo "🌐 Your app should be available via the LoadBalancer."

            // Re-authenticate for this post step so kubectl works here too
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                sh '''
                    aws eks update-kubeconfig --region $AWS_DEFAULT_REGION --name $CLUSTER_NAME
                    kubectl get svc flask-app-service
                '''
            }
        }

        failure {
            echo "❌ Pipeline failed. Check console output for details."
        }
    }
}
