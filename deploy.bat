@echo off
echo ==========================================
echo Deploying LMS_EA to GitHub...
echo ==========================================

git init
git add .
git commit -m "Update logo to square icon, align navbar, and add full offline PWA support"

echo Setting remote URL to MEME repository...
git remote remove origin 2>nul
git remote add origin https://github.com/hirensoni233/MEME.git

echo Pushing to main branch...
git push -u origin main -f

echo ==========================================
echo Done! Vercel should start building now.
echo ==========================================
pause
