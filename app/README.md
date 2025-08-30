# VAT policy simulator

A Docker Compose application for analysing VAT registration threshold reforms in the UK over the budget window (2025-26 to 2030-31).

## Getting started

### Prerequisites
- Docker and Docker Compose installed
- The synthetic firms data file at `../analysis/synthetic_firms.csv`

### Running the application

1. Navigate to the app directory:
```bash
cd app
```

2. Build and start the containers:
```bash
docker-compose up --build
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API documentation: http://localhost:8000/docs

### Features

The simulator allows you to:
- Set custom VAT registration thresholds
- Configure tapering options (none, moderate, aggressive, or custom)
- View revenue impacts by year across the budget window
- Analyse impacts by business sector
- See breakdowns by firm revenue bands

### Architecture

- **Backend**: FastAPI service that performs VAT calculations using the synthetic firms dataset
- **Frontend**: Next.js application with a modern interface for policy design and results visualisation

### API endpoints

- `GET /baseline` - Returns baseline VAT statistics
- `POST /analyze` - Analyses a VAT reform policy
- `GET /health` - Health check endpoint

### Development

To run in development mode with hot reloading:

```bash
docker-compose up
```

To rebuild after changes:

```bash
docker-compose up --build
```

To stop the application:

```bash
docker-compose down
```