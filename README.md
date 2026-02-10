# Sage House Reviews Dashboard

Review aggregation and monitoring dashboard for Sage House assisted living facilities.

## Features
- Unified review feed from Google, Yelp, and Facebook (Scrapers modularly designed)
- Sentiment analysis and automated alerting for negative reviews
- Response tracking and management
- Aggregate statistics and trends

## Setup

### Backend
1. `cd backend`
2. `pip install -r requirements.txt`
3. Create `.env` from `.env.example`
4. `uvicorn main:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

### Docker
`docker-compose up --build`

## Deployment
- **Frontend:** Deploy to Vercel (connected to this repo)
- **Backend:** Deploy to Railway or Render using the included Dockerfile.
