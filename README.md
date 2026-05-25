# ShelfSight 🏬

A computer vision analytics system that monitors retail store foot traffic using YOLOv8, Flask, and AI-powered reporting.

## Tech Stack
- **Backend:** Flask, SQLite, pandas
- **Computer Vision:** YOLOv8, OpenCV, Pillow
- **Cart Detection:** Roboflow API
- **AI Reports:** Groq API (Llama 3.3)
- **Frontend:** Vanilla JS, HTML/CSS
- **DevOps:** Docker

## Features
- Real-time people detection via YOLOv8
- Congestion classification (LOW/MEDIUM/HIGH)
- SQLite traffic logging
- pandas traffic analysis
- AI-generated executive reports
- Interactive analytics dashboard
- Docker containerization

## Run with Docker
```bash
docker-compose up --build
```

## Run locally
```bash
cd backend
python app.py
```