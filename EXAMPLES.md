# Example Test Repositories

This document lists sample repositories you can use to test the TestIt platform.

## ✅ Working Examples

### 1. Simple Python Flask Application
**URL**: `https://github.com/pallets/flask`
- **Language**: Python
- **Has Dockerfile**: No (will be auto-generated)
- **Dependencies**: requirements.txt
- **Expected Result**: Container with Flask installed, can run Python REPL

### 2. Docker Welcome Example
**URL**: `https://github.com/docker/welcome-to-docker`
- **Language**: Multiple
- **Has Dockerfile**: Yes
- **Expected Result**: Pre-configured container

### 3. Simple Node.js Express App
**URL**: `https://github.com/expressjs/express`
- **Language**: Node.js
- **Has Dockerfile**: No (will be auto-generated)
- **Dependencies**: package.json
- **Expected Result**: Container with Express installed

### 4. Python Requests Library
**URL**: `https://github.com/psf/requests`
- **Language**: Python
- **Has Dockerfile**: No
- **Dependencies**: setup.py
- **Expected Result**: Container with requests library installed

### 5. Simple Go Application
**URL**: `https://github.com/golang/example`
- **Language**: Go
- **Has Dockerfile**: Varies by subdirectory
- **Dependencies**: go.mod
- **Expected Result**: Go development environment

## 🧪 Testing Workflow

For each repository:

1. **Submit the repository URL** through the web interface or API
2. **Monitor the build process** - check the status endpoint
3. **Access the terminal** once the build succeeds
4. **Verify the environment**:
   - For Python: `python --version` and `pip list`
   - For Node.js: `node --version` and `npm list`
   - For Go: `go version`
   - For Java: `java -version`
5. **Test running commands** specific to the repository
6. **Stop the session** or wait for auto-destroy

## 📋 Test Checklist

- [ ] Repository with existing Dockerfile builds successfully
- [ ] Python project with requirements.txt builds and installs dependencies
- [ ] Node.js project with package.json builds and installs dependencies
- [ ] Terminal connection works via WebSocket
- [ ] Commands execute properly in the terminal
- [ ] Session appears in active sessions list
- [ ] Session can be manually stopped
- [ ] Build failures are properly logged and reported

## 🚫 Known Limitations

The following will NOT work in v1:

- Repositories requiring GPU access
- Windows-specific projects
- Multi-container docker-compose projects
- Projects requiring external databases
- Very large repositories (>1GB)
- Projects with long build times (>5 minutes)

## 💡 Tips

- Start with simple, small repositories
- Check that the repository has clear dependency files
- Monitor build logs for any issues
- Use the terminal to verify the environment
- Test with public repositories first
