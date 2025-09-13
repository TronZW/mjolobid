@echo off
echo 🚀 Setting up Git repository and pushing to GitHub...

REM Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed or not in PATH
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
)

REM Initialize Git repository if not already initialized
if not exist .git (
    echo 📁 Initializing Git repository...
    git init
)

REM Add all files to staging
echo 📦 Adding files to staging...
git add .

REM Create initial commit
echo 💾 Creating initial commit...
git commit -m "Initial commit: MjoloBid Django application with deployment configuration"

REM Add remote origin
echo 🔗 Adding remote origin...
git remote add origin https://github.com/TronZW/mjolobid.git

REM Push to GitHub
echo 🚀 Pushing to GitHub...
git branch -M main
git push -u origin main

echo ✅ Successfully pushed to GitHub!
echo 🌐 Your repository is now available at: https://github.com/TronZW/mjolobid
pause
