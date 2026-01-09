import os
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from app.models import LanguageType


class LanguageDetector:
    """Detects programming language and dependencies from repository"""
    
    # File patterns for language detection
    LANGUAGE_PATTERNS = {
        LanguageType.PYTHON: ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
        LanguageType.NODE: ["package.json", "package-lock.json", "yarn.lock"],
        LanguageType.JAVA: ["pom.xml", "build.gradle", "build.gradle.kts"],
        LanguageType.GO: ["go.mod", "go.sum"],
    }
    
    @staticmethod
    def detect_language(repo_path: str) -> LanguageType:
        """Detect language from repository files"""
        repo_path_obj = Path(repo_path)
        
        # Check for language-specific files
        for lang, patterns in LanguageDetector.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if (repo_path_obj / pattern).exists():
                    return lang
        
        # Check file extensions as fallback
        extensions = {
            ".py": LanguageType.PYTHON,
            ".js": LanguageType.NODE,
            ".ts": LanguageType.NODE,
            ".java": LanguageType.JAVA,
            ".go": LanguageType.GO,
        }
        
        for file in repo_path_obj.rglob("*"):
            if file.is_file() and file.suffix in extensions:
                return extensions[file.suffix]
        
        return LanguageType.UNKNOWN
    
    @staticmethod
    def detect_dependencies(repo_path: str, language: LanguageType) -> Dict[str, List[str]]:
        """Detect dependencies for the given language"""
        repo_path_obj = Path(repo_path)
        dependencies = {}
        
        try:
            if language == LanguageType.PYTHON:
                dependencies = LanguageDetector._detect_python_deps(repo_path_obj)
            elif language == LanguageType.NODE:
                dependencies = LanguageDetector._detect_node_deps(repo_path_obj)
            elif language == LanguageType.JAVA:
                dependencies = LanguageDetector._detect_java_deps(repo_path_obj)
            elif language == LanguageType.GO:
                dependencies = LanguageDetector._detect_go_deps(repo_path_obj)
        except Exception as e:
            dependencies["error"] = [str(e)]
        
        return dependencies
    
    @staticmethod
    def _detect_python_deps(repo_path: Path) -> Dict[str, List[str]]:
        """Detect Python dependencies"""
        deps = {"packages": []}
        
        # Check requirements.txt
        req_file = repo_path / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        deps["packages"].append(line)
        
        # Check setup.py (basic parsing)
        setup_file = repo_path / "setup.py"
        if setup_file.exists():
            deps["has_setup_py"] = ["true"]
        
        # Check pyproject.toml
        pyproject_file = repo_path / "pyproject.toml"
        if pyproject_file.exists():
            deps["has_pyproject_toml"] = ["true"]
        
        return deps
    
    @staticmethod
    def _detect_node_deps(repo_path: Path) -> Dict[str, List[str]]:
        """Detect Node.js dependencies"""
        deps = {"packages": []}
        
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    
                if "dependencies" in data:
                    deps["dependencies"] = list(data["dependencies"].keys())
                
                if "devDependencies" in data:
                    deps["devDependencies"] = list(data["devDependencies"].keys())
                
                if "scripts" in data:
                    deps["scripts"] = list(data["scripts"].keys())
            except json.JSONDecodeError:
                deps["error"] = ["Invalid package.json"]
        
        return deps
    
    @staticmethod
    def _detect_java_deps(repo_path: Path) -> Dict[str, List[str]]:
        """Detect Java dependencies"""
        deps = {}
        
        # Check for Maven
        pom_xml = repo_path / "pom.xml"
        if pom_xml.exists():
            deps["build_tool"] = ["maven"]
        
        # Check for Gradle
        build_gradle = repo_path / "build.gradle"
        build_gradle_kts = repo_path / "build.gradle.kts"
        if build_gradle.exists() or build_gradle_kts.exists():
            deps["build_tool"] = ["gradle"]
        
        return deps
    
    @staticmethod
    def _detect_go_deps(repo_path: Path) -> Dict[str, List[str]]:
        """Detect Go dependencies"""
        deps = {"packages": []}
        
        go_mod = repo_path / "go.mod"
        if go_mod.exists():
            try:
                with open(go_mod, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("require"):
                            deps["has_go_mod"] = ["true"]
                            break
            except Exception:
                pass
        
        return deps
    
    @staticmethod
    def has_dockerfile(repo_path: str) -> bool:
        """Check if repository has a Dockerfile"""
        repo_path_obj = Path(repo_path)
        return (repo_path_obj / "Dockerfile").exists()
