@echo off
echo =====================================
echo   GitHub Deployment Script
echo =====================================
echo.
echo This script will help you deploy your web application to GitHub
echo.
echo Step 1: Initialize Git Repository
echo -----------------------------------
echo.
echo Running: git init
git init
echo.
echo Step 2: Add All Files
echo --------------------
echo.
echo Running: git add .
git add .
echo.
echo Step 3: Create Initial Commit
echo -----------------------------
echo.
echo Running: git commit -m "Initial commit - Enterprise Web Application"
git commit -m "Initial commit - Enterprise Web Application"
echo.
echo Step 4: Instructions for GitHub
echo -------------------------------
echo.
echo 1. Go to https://github.com
echo 2. Click "+" → "New repository"
echo 3. Name it: enterprise-web-application
echo 4. Make it Public or Private
echo 5. Click "Create repository"
echo 6. Copy the repository URL
echo.
echo Step 5: Connect to GitHub
echo -------------------------
echo.
echo Run these commands (replace YOUR_USERNAME with your GitHub username):
echo git remote add origin https://github.com/YOUR_USERNAME/enterprise-web-application.git
echo git branch -M main
echo git push -u origin main
echo.
echo =====================================
echo   Git Repository Ready!
echo =====================================
echo.
echo Your repository is now ready to push to GitHub.
echo Follow the steps above to complete the deployment.
echo.
pause