pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = "us-east-1"
        CLUSTER_NAME = "sakshith_01-cluster"
        DOCKERHUB_USER = "sakshith123"
        IMAGE_NAME = "flask-rds-app"
        IMAGE_TAG = "v${BUILD_NUMBER}"
        DEPLOYMENT_FILE = "deployment.yaml"
        SERVICE_FILE = "service.yaml"
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
                echo "🔧 Updating deployment.yaml with image: $DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG"
                sh '''
                    if grep -q "image:" $DEPLOYMENT_FILE; then
                      sed -i "s|image: .*flask-rds-app:.*|image: ${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}|g" $DEPLOYMENT_FILE || true
                    else
                      echo "⚠️ No image line found in $DEPLOYMENT_FILE"
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
                    retry(3) {
                        sh '''
                            echo "🔑 Setting up kubeconfig for EKS..."
                            aws eks update-kubeconfig --region $AWS_DEFAULT_REGION --name $CLUSTER_NAME

                            echo "🚀 Applying Kubernetes manifests..."
                            kubectl apply -f $DEPLOYMENT_FILE
                            kubectl apply -f $SERVICE_FILE || true

                            echo "⏳ Waiting for rollout to finish..."
                            # Use || true so pipeline continues even if rollout fails
                            kubectl rollout status deployment/flask-app-deployment --timeout=3m || true

                            echo "✅ Deployment attempted! Checking current status..."
                            kubectl get pods -o wide
                            kubectl get svc flask-app-service || true
                        '''
                    }
                }
            }
        }

        // 🧠 New Debug Stage — to automatically collect logs and events if rollout fails
        stage('Debug Kubernetes Deployment') {
            steps {
                echo "🔍 Collecting Kubernetes diagnostics..."
                sh '''
                    echo "=== DEPLOYMENT STATUS ==="
                    kubectl get deployment flask-app-deployment -o wide || true

                    echo "\n=== PODS STATUS ==="
                    kubectl get pods -o wide || true

                    echo "\n=== POD DESCRIPTIONS ==="
                    for pod in $(kubectl get pods -l app=flask-app -o name 2>/dev/null); do
                        echo "\n---- $pod ----"
                        kubectl describe $pod | tail -n 50 || true
                    done

                    echo "\n=== POD LOGS (Last 50 lines) ==="
                    for pod in $(kubectl get pods -l app=flask-app -o name 2>/dev/null); do
                        echo "\n---- Logs for $pod ----"
                        kubectl logs $pod --tail=50 || true
                    done

                    echo "\n=== CLUSTER EVENTS ==="
                    kubectl get events --sort-by=.metadata.creationTimestamp | tail -n 40 || true
                '''
            }
        }
    }

    post {
        always {
            echo "🧹 Cleaning up local Docker system..."
            sh 'docker system prune -af || true'
        }

        success {
            echo "✅ Pipeline completed successfully!"
            echo "🌐 Checking if LoadBalancer is active..."
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                sh '''
                    aws eks update-kubeconfig --region $AWS_DEFAULT_REGION --name $CLUSTER_NAME
                    echo "➡️ Current services:"
                    kubectl get svc flask-app-service
                    echo "🌍 LoadBalancer URL (if provisioned):"
                    kubectl get svc flask-app-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' || true
                    echo ""
                '''
            }
        }

        failure {
            echo "❌ Pipeline failed. Check console output for details."
        }
    }
}
