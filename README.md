# PDF2JSON

PDF2JSON is a full‑stack web application that converts PDF documents and images to structured JSON using OCR. The backend is built with FastAPI and PaddleOCR, and the frontend uses React.

## Features

- OCR-based PDF/image to JSON conversion  
- Grouping of text and table cells  
- JSON download option

## Tech Stack

- **Backend:** FastAPI, Python, Uvicorn, PaddleOCR  
- **Frontend:** React, Node.js, TypeScript
- **Deployment:** Full‑stack monorepo deployment (planned for future)

## Project Structure

```
.
├── main.py           # FastAPI application
├── requirements.txt  # Python dependencies (to be done)
├── Procfile          # Deployment command for backend (for future use)
├── .gitignore
├── README.md
└── frontend/         # React frontend
    ├── public/
    ├── src/
    └── package.json
```

## Getting Started

### Backend

1. **Clone the Repo & Navigate:**
   - Open your terminal and run:  
     `git clone https://github.com/Timenspace11/PDF2JSON.git`  
     `cd PDF2JSON`

2. **Create & Activate a Virtual Environment:**
   - **Windows:**  
     `python -m venv venv`  
     `venv\Scripts\activate`
   - **macOS/Linux:**  
     `python3 -m venv venv`  
     `source venv/bin/activate`

3. **Install Dependencies:**
   - Run:  
     `pip install -r requirements.txt`

4. **Run the Backend:**
   - Start the server with:  
     `uvicorn main:app --reload`  
   - The API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

### Frontend

1. **Navigate to the Frontend Folder:**
   - Run:  
     `cd frontend`

2. **Install Packages:**
   - Run:  
     `npm install`

3. **Run the Frontend:**
   - Start the app with:  
     `npm start`  
   - The app will run at [http://localhost:3000](http://localhost:3000).

## Usage

- **Upload:** Use the upload form on the frontend to select a PDF or image file.
- **Conversion:** The file is processed by the FastAPI backend using OCR.
- **Output:** View and download the resulting JSON.

## Future Deployment

We plan to deploy PDF2JSON as a public web application in the near future. Stay tuned for updates!
