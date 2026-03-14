pipeline {
    agent any

    environment {
        REGISTRY = 'registry.gitlab.com'
        IMAGE_NAME = 'docappoint/DocAppoint'
        DOCKER_BUILDKIT = '1'
        CI = 'true'

        // Test database configs
        POSTGRES_DB = 'docappoint_test'
        POSTGRES_USER = 'postgres'
        POSTGRES_PASSWORD = 'password'
        DJANGO_SECRET_KEY = 'test-secret-key-for-ci'
        DJANGO_SETTINGS_MODULE = 'api.settings.development'
        EMAIL_VERIFY_SECRET = 'test-email-secret-for-ci'
        REDIS_URL = 'redis://localhost:6379/0'

        // KOYEB_API_KEY = credentials('RENDER_API_KEY')
        // KOYEB_BACKEND_SERVICE_ID = credentials('KOYEB_BACKEND_SERVICE_ID')
        // KOYEB_FRONTEND_SERVICE_ID = credentials('KOYEB_FRONTEND_SERVICE_ID')

        // External cache volume
        POETRY_CACHE_DIR = '/cache/poetry'
        npm_config_cache = '/cache/npm'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify Tools') {
            steps {
                sh '''
                    echo "=== Verifying Required Tools ==="
                    docker --version || { echo "Docker not installed"; exit 1; }
                    docker compose version || { echo "Docker Compose not installed"; exit 1; }
                    python3 --version || echo "Warning: Python not found"
                    node --version || echo "Warning: Node not found"
                    echo "✅ Tools verified"
                '''
            }
        }

        stage('Setup with Caching') {
            steps {
                script {
                    env.CACHE_BRANCH = env.BRANCH_NAME ?: 'main'

                    sh """
                        mkdir -p /cache/npm/${CACHE_BRANCH} /cache/poetry/${CACHE_BRANCH}
                        chmod -R 777 /cache/npm/${CACHE_BRANCH} /cache/poetry/${CACHE_BRANCH}
                    """
                }

                cache(maxCacheSize: 500, caches: [
                    arbitraryFileCache(
                        path: 'frontend/node_modules',
                        cacheValidityDecidingFile: 'frontend/package-lock.json'
                    ),
                    arbitraryFileCache(
                        path: 'backend/.venv',
                        cacheValidityDecidingFile: 'backend/poetry.lock'
                    )
                ]) {
                    script {
                        // Create symlink once inside cache block to ensure
                        // the paths are available
                        sh """
                            # Remove any existing directories/symlinks from previous failed builds
                            # but preserve the actual cache content
                            rm -rf frontend/node_modules backend/.venv
                            
                            # Create fresh symlinks to the cache directories
                            ln -sfn /cache/npm/${CACHE_BRANCH} frontend/node_modules
                            ln -sfn /cache/poetry/${CACHE_BRANCH} backend/.venv
                            
                            echo "Created symlinks to cache directories"
                        """

                        parallel(
                            'Setup Frontend': {
                                dir('frontend') {
                                    script {
                                        if (fileExists('node_modules') && sh(script: 'test -n "$(ls -A node_modules 2>/dev/null)"', returnStatus: true) == 0) {
                                            echo "Using frontend cache"
                                        } else {
                                            echo "Cache empty, installing frontend dependencies..."

                                            sh '''
                                                echo "=== Setting up Frontend ==="
                                                npm ci --cache /cache/npm --prefer-offline
                                            '''
                                        }
                                        sh '''
                                            # Verify setup
                                            npm --version
                                            node --version
                                            echo "Frontend setup complete"
                                        '''
                                    }
                                }
                            },
                            'Setup Backend': {
                                dir('backend') {
                                    script {
                                        if (fileExists('.venv/bin/activate') && fileExists('.venv/lib')) {
                                            echo 'Using backend cache'
                                        } else {
                                            echo "Cache empty, installing backend dependencies..."

                                            sh '''
                                                echo "=== Setting up Backend ==="
                                                # Install Poetry
                                                pip install poetry

                                                # Configure Poetry (venv in project)
                                                poetry config virtualenvs.create true
                                                poetry config virtualenvs.in-project true
                                                poetry config cache-dir /cache/poetry
                                                poetry install --with dev --no-interaction --no-root --no-ansi
                                            '''
                                        }
                                        sh '''
                                            # Verify setup
                                            poetry --version
                                            poetry show
                                            echo "Backend setup complete"
                                        '''
                                    }
                                }
                            }
                        )
                    }
                }
            }
        }

        stage('Static Checks') {
            parallel {
                stage('Frontend Lint & Type Check') {
                    steps {
                        dir('frontend') {
                            sh 'make ci-fe-lint'
                            sh 'make ci-fe-type-check'
                        }
                    }
                }

                stage('Backend Lint & Type Check') {
                    steps {
                        dir('backend') {
                            sh 'make ci-be-lint'
                            sh 'make ci-be-type-check'
                        }
                    }
                }

            }
        }

        stage('Start Docker') {
            steps {
                sh '''
                    make dev-restart-detached

                    # Wait for docker to finish
                    timeout 60s sh -c 'until curl -s -f http://localhost:8000/api/ > /dev/null; do sleep 3; done'
                '''
            }
        }

        stage('Database Migrations Check') {
            steps {
                sh '''
                    # Check migrations inside the running container
                    docker compose exec -T backend python manage.py makemigrations --check --dry-run
                    
                    # Apply migrations
                    docker compose exec -T backend python manage.py migrate
                '''
            }
        }

        stage('Run Tests') {
            parallel {
                stage('Backend Tests') {
                    steps {
                        dir('backend') {
                            sh 'make ci-be-test'
                        }
                    }
                }
                stage('Frontend Tests') {
                    steps {
                        dir('frontend') {
                            sh 'make ci-fe-test'
                        }
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def backendTag = "backend-${BUILD_NUMBER}"
                    def frontendTag = "frontend-${BUILD_NUMBER}"
                    
                    sh """
                        docker build -t ${REGISTRY}/${IMAGE_NAME}/backend:${backendTag} ./backend
                        docker build -t ${REGISTRY}/${IMAGE_NAME}/frontend:${frontendTag} ./frontend
                        
                        # Also tag as 'latest' for convenience
                        docker tag ${REGISTRY}/${IMAGE_NAME}/backend:${backendTag} ${REGISTRY}/${IMAGE_NAME}/backend:latest
                        docker tag ${REGISTRY}/${IMAGE_NAME}/frontend:${frontendTag} ${REGISTRY}/${IMAGE_NAME}/frontend:latest
                    """
                }
            }
        }

        stage('Docker Login') {
            steps {
                withCredentials([string(credentialsId: 'GITLAB_TOKEN', variable: 'TOKEN')]) {
                    sh '''
                        echo "$TOKEN" | docker login registry.gitlab.com -u your-gitlab-username --password-stdin
                    '''
                }
            }
        }

        stage('Push Images') {
            steps {
                sh """
                    docker push ${REGISTRY}/${IMAGE_NAME}/backend:backend-${BUILD_NUMBER}
                    docker push ${REGISTRY}/${IMAGE_NAME}/backend:latest
                    docker push ${REGISTRY}/${IMAGE_NAME}/frontend:frontend-${BUILD_NUMBER}
                    docker push ${REGISTRY}/${IMAGE_NAME}/frontend:latest
                """
            }
        }

        // stage('Deployment') {
        //     when {
        //         branch 'main'
        //     }
        //     steps {
        //         sh '''
        //             ansible-playbook deploy.yml \
        //                 --extra-vars "build_number=${BUILD_NUMBER}" \
        //                 --extra-vars "git_commit=${GIT_COMMIT}" \
        //                 --extra-vars "backend_service_id=${KOYEB_BACKEND_SERVICE_ID}" \
        //                 --extra-vars "frontend_service_id=${KOYEB_FRONTEND_SERVICE_ID}"
        //         '''
        //     }
        // }
    }

    post {
        always {
            script {
                sh '''
                    make dev-down
                    make ci-clean
                    curl -X POST https://us-central1-docappoint-devops.cloudfunctions.net/stop-vm

                    # Clean caches older than 30 days
                    find /cache/npm -type d -mtime +30 -exec rm -rf {} + 2>/dev/null || true
                    find /cache/poetry -type d -mtime +30 -exec rm -rf {} + 2>/dev/null || true
                '''
            }

            cleanWs()
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}