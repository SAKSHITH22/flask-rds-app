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
        SECRET_FILE = "k8s-secret.yaml"
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/SAKSHITH22/flask-rds-app.git'
            }
        }

        stage('Build & Push Docker Image') {
            steps {
                echo "🐳 Building Docker image..."
                withCredentials([usernamePassword(credentialsId: 'dockerhub-token', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        docker build -t $DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG .
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push $DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG
                        docker logout
                    '''
                }
            }
        }

        stage('Update Deployment Image') {
            steps {
                echo "🛠️ Updating image reference in deployment.yaml..."
                sh '''
                    if command -v yq >/dev/null 2>&1; then
                        yq e '.spec.template.spec.containers[0].image = "'$DOCKERHUB_USER'/'$IMAGE_NAME':'$IMAGE_TAG'"' -i $DEPLOYMENT_FILE
                    else
                        sed -i "s|image: .*flask-rds-app:.*|image: ${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}|g" $DEPLOYMENT_FILE
                    fi
                '''
            }
        }

        stage('Configure Kubeconfig') {
            steps {
                echo "⚙️ Configuring kubeconfig for EKS..."
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                    sh '''
                        echo "🔍 Checking AWS identity..."
                        aws sts get-caller-identity || { echo "❌ Invalid AWS credentials"; exit 1; }

                        echo "🔧 Updating kubeconfig..."
                        aws eks update-kubeconfig --region $AWS_DEFAULT_REGION --name $CLUSTER_NAME || { echo "❌ Failed to configure kubeconfig"; exit 1; }

                        echo "✅ Kubeconfig successfully configured."
                    '''
                }
            }
        }

        stage('Apply Secrets & Deploy') {
            steps {
                echo "🚀 Deploying to EKS..."
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                    sh '''
                        kubectl apply -f $SECRET_FILE || true
                        kubectl apply -f $DEPLOYMENT_FILE
                        kubectl apply -f $SERVICE_FILE
                        kubectl rollout restart deployment/flask-app-deployment
                        kubectl rollout status deployment/flask-app-deployment --timeout=3m || true
                    '''
                }
            }
        }

        stage('Diagnostics') {
            steps {
                echo "🩺 Running diagnostics..."
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                    sh '''
                        kubectl get pods -o wide
                        kubectl get svc flask-app-service
                        kubectl get events --sort-by=.metadata.creationTimestamp | tail -n 40
                        kubectl logs -l app=flask-app --tail=50 || true
                    '''
                }
            }
        }

        // Optional: DB initialization stage (disabled by default)
        // stage('Initialize DB') {
        //     steps {
        //         echo "🧱 Initializing database..."
        //         sh '''
        //             APP_URL=$(kubectl get svc flask-app-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
        //             curl -s http://$APP_URL/initdb || true
        //         '''
        //     }
        // }
    }

    post {
        always {
            sh 'docker system prune -af || true'
        }
        success {
            echo "✅ Deployment completed successfully!"
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                sh '''
                    kubectl get svc flask-app-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' || true
                '''
            }
        }
        failure {
            echo "❌ Pipeline failed. Check logs above."
        }
    }
}
