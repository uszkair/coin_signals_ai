@echo off
echo Setting up React frontend...

cd static

echo Installing dependencies...
call npm install

echo Building frontend...
call npx vite build

echo Setup complete!
echo You can now run the application with: uvicorn main:app --reload