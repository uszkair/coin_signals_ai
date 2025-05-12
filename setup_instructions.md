# Crypto Trading Assistant Setup Instructions

## Prerequisites

Before running the application, you need to install:

1. **Node.js and npm**
   - Download and install from [nodejs.org](https://nodejs.org/)
   - Verify installation with:
     ```
     node --version
     npm --version
     ```

## Setup Steps

1. **Install Backend Dependencies**
   ```
   pip install -r requirements.txt
   ```

2. **Install Frontend Dependencies**
   ```
   cd static
   npm install
   ```

3. **Build the Frontend**
   ```
   cd static
   npm run build
   ```
   
   Note: If you encounter the error "'vite' is not recognized", make sure:
   - Node.js and npm are properly installed
   - You've run `npm install` in the static directory
   - Your PATH environment variable includes npm's global bin directory

4. **Start the Backend**
   ```
   uvicorn main:app --reload
   ```

5. **Access the Application**
   Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## Alternative Development Setup

If you prefer to run the frontend in development mode with hot-reloading:

1. **Start the Backend**
   ```
   uvicorn main:app --reload
   ```

2. **Start the Frontend Development Server**
   ```
   cd static
   npx vite
   ```
   
   Using `npx vite` instead of `npm run dev` can help if the vite command isn't in your PATH.

3. **Access the Development Server**
   ```
   http://localhost:5173