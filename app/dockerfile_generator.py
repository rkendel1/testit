from pathlib import Path
from app.models import LanguageType


class DockerfileGenerator:
    """Generates Dockerfiles for different languages"""
    
    @staticmethod
    def generate_dockerfile(language: LanguageType, repo_path: str) -> str:
        """Generate a Dockerfile for the given language"""
        if language == LanguageType.PYTHON:
            return DockerfileGenerator._generate_python_dockerfile(repo_path)
        elif language == LanguageType.NODE:
            return DockerfileGenerator._generate_node_dockerfile(repo_path)
        elif language == LanguageType.JAVA:
            return DockerfileGenerator._generate_java_dockerfile(repo_path)
        elif language == LanguageType.GO:
            return DockerfileGenerator._generate_go_dockerfile(repo_path)
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    @staticmethod
    def _generate_python_dockerfile(repo_path: str) -> str:
        """Generate Dockerfile for Python projects"""
        repo_path_obj = Path(repo_path)
        has_requirements = (repo_path_obj / "requirements.txt").exists()
        has_setup_py = (repo_path_obj / "setup.py").exists()
        
        dockerfile = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . /app

"""
        
        if has_requirements:
            dockerfile += """# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

"""
        
        if has_setup_py:
            dockerfile += """# Install package in development mode
RUN pip install -e .

"""
        
        dockerfile += """# Expose common ports
EXPOSE 8000 8888

# Default command (can be overridden)
CMD ["python", "-m", "http.server", "8000"]
"""
        
        return dockerfile
    
    @staticmethod
    def _generate_node_dockerfile(repo_path: str) -> str:
        """Generate Dockerfile for Node.js projects"""
        repo_path_obj = Path(repo_path)
        has_package_json = (repo_path_obj / "package.json").exists()
        has_yarn_lock = (repo_path_obj / "yarn.lock").exists()
        
        dockerfile = """FROM node:20-slim

WORKDIR /app

# Install git
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Copy package files
"""
        
        if has_package_json:
            dockerfile += """COPY package*.json ./
"""
            if has_yarn_lock:
                dockerfile += """COPY yarn.lock ./
"""
        
        dockerfile += """
# Copy application files
COPY . /app

"""
        
        if has_package_json:
            if has_yarn_lock:
                dockerfile += """# Install dependencies with yarn
RUN yarn install

"""
            else:
                dockerfile += """# Install dependencies with npm
RUN npm install

"""
        
        dockerfile += """# Expose common ports
EXPOSE 3000 8080

# Default command (can be overridden)
CMD ["npm", "start"]
"""
        
        return dockerfile
    
    @staticmethod
    def _generate_java_dockerfile(repo_path: str) -> str:
        """Generate Dockerfile for Java projects"""
        repo_path_obj = Path(repo_path)
        has_pom = (repo_path_obj / "pom.xml").exists()
        has_gradle = (repo_path_obj / "build.gradle").exists() or (repo_path_obj / "build.gradle.kts").exists()
        
        if has_gradle:
            dockerfile = """FROM gradle:8-jdk17 AS build

WORKDIR /app

# Copy Gradle files
COPY build.gradle* settings.gradle* gradlew* ./
COPY gradle ./gradle

# Copy source code
COPY . /app

# Build application
RUN gradle build --no-daemon

# Runtime image
FROM openjdk:17-slim

WORKDIR /app

# Copy built artifacts
COPY --from=build /app/build/libs/*.jar app.jar

# Expose common ports
EXPOSE 8080

# Run application
CMD ["java", "-jar", "app.jar"]
"""
        elif has_pom:
            dockerfile = """FROM maven:3-openjdk-17 AS build

WORKDIR /app

# Copy Maven files
COPY pom.xml ./

# Copy source code
COPY . /app

# Build application
RUN mvn clean package -DskipTests

# Runtime image
FROM openjdk:17-slim

WORKDIR /app

# Copy built artifacts
COPY --from=build /app/target/*.jar app.jar

# Expose common ports
EXPOSE 8080

# Run application
CMD ["java", "-jar", "app.jar"]
"""
        else:
            dockerfile = """FROM openjdk:17-slim

WORKDIR /app

# Copy application files
COPY . /app

# Expose common ports
EXPOSE 8080

# Default command
CMD ["bash"]
"""
        
        return dockerfile
    
    @staticmethod
    def _generate_go_dockerfile(repo_path: str) -> str:
        """Generate Dockerfile for Go projects"""
        dockerfile = """FROM golang:1.21-alpine AS build

WORKDIR /app

# Copy go mod files
COPY go.* ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . /app

# Build application
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

# Runtime image
FROM alpine:latest

WORKDIR /app

# Copy binary from build stage
COPY --from=build /app/main .

# Expose common ports
EXPOSE 8080

# Run application
CMD ["./main"]
"""
        
        return dockerfile
