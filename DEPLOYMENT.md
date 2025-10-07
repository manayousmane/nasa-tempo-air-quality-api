# NASA TEMPO Air Quality API - Deployment Guide

## Production Deployment Options

### Docker Deployment (Recommended)

```bash
# Build the image
docker build -t nasa-tempo-api .

# Run with environment variables
docker run -p 8000:8000 \
  -e NASA_EARTHDATA_USERNAME="your_username" \
  -e NASA_EARTHDATA_PASSWORD="your_password" \
  -e NASA_EARTHDATA_TOKEN="your_token" \
  nasa-tempo-api
```

### Render.com Deployment

1. **Connect Repository**: Link your GitHub repo to Render
2. **Service Type**: Web Service
3. **Environment**: Docker
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `python start_production.py`

**Required Environment Variables:**
```
NASA_EARTHDATA_USERNAME=your_nasa_username
NASA_EARTHDATA_PASSWORD=your_nasa_password
NASA_EARTHDATA_TOKEN=your_nasa_token
DEBUG=False
LOG_LEVEL=INFO
```

### Heroku Deployment

```bash
# Login and create app
heroku login
heroku create your-nasa-tempo-api

# Set environment variables
heroku config:set NASA_EARTHDATA_USERNAME="your_username"
heroku config:set NASA_EARTHDATA_PASSWORD="your_password"
heroku config:set NASA_EARTHDATA_TOKEN="your_token"

# Deploy
git push heroku main
```

### Local Production

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (Linux/Mac)
export NASA_EARTHDATA_USERNAME="your_username"
export NASA_EARTHDATA_PASSWORD="your_password"
export NASA_EARTHDATA_TOKEN="your_token"

# Start production server
python start_production.py
```

## Pre-Deployment Checklist

### Required Credentials
- [ ] NASA Earthdata account created at https://earthdata.nasa.gov/
- [ ] NASA_EARTHDATA_USERNAME configured
- [ ] NASA_EARTHDATA_PASSWORD configured  
- [ ] NASA_EARTHDATA_TOKEN obtained and configured

### Environment Setup
- [ ] Python 3.11+ installed
- [ ] All dependencies from requirements.txt installed
- [ ] Environment variables configured
- [ ] Health check endpoint responding at `/health`

### API Functionality
- [ ] `/api/v1/location/full` endpoint working
- [ ] NASA TEMPO authentication successful
- [ ] OpenAQ global data integration working
- [ ] Error handling and logging configured

## API Endpoints

Once deployed, your API will be available at:

- **Documentation**: `https://your-api-url/docs`
- **Health Check**: `https://your-api-url/health`
- **Status**: `https://your-api-url/status`

### Primary Endpoints:
- `GET /api/v1/location/full?latitude={lat}&longitude={lon}`
- `GET /api/v1/location/aqi?latitude={lat}&longitude={lon}`
- `GET /api/v1/location/pollutants?latitude={lat}&longitude={lon}`

### Enhanced Endpoints (if available):
- `GET /api/v2/location/comprehensive?latitude={lat}&longitude={lon}`
- `GET /api/v2/location/tempo-coverage?latitude={lat}&longitude={lon}`
- `GET /api/v2/location/who-analysis?latitude={lat}&longitude={lon}`

## 📊 Data Sources

The API integrates real-time data from:

- 🛰️ **NASA TEMPO Satellite** (North America)
- 🌍 **OpenAQ Global Network** (150+ countries)
- 🔬 **NASA Ground Stations** (Pandora, TOLNet)
- 🏥 **WHO Air Quality Guidelines** (2021)
- 🌎 **International Space Agencies** (CSA, Brazil)

## 🔍 Monitoring & Health Checks

### Health Check Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-07T12:00:00Z",
  "checks": {
    "nasa_credentials": "✅ configured",
    "api_endpoints": "✅ operational",
    "external_apis": "✅ configured"
  }
}
```

### Log Files:
- Application logs: `nasa_tempo_api.log`
- Access logs: via uvicorn
- Error tracking: via logging module

## 🚨 Troubleshooting

### Common Issues:

1. **Missing NASA Credentials**
   ```
   Error: Missing required environment variables
   Solution: Configure NASA_EARTHDATA_* variables
   ```

2. **Dependency Errors**
   ```
   Error: ModuleNotFoundError: No module named 'geopy'
   Solution: pip install -r requirements.txt
   ```

3. **Authentication Failures**
   ```
   Error: NASA authentication failed
   Solution: Verify credentials at https://earthdata.nasa.gov/
   ```

### Support:
- 📧 GitHub Issues: https://github.com/manayousmane/nasa-tempo-air-quality-api/issues
- 📚 Documentation: `/docs` endpoint
- 🔍 Health Check: `/health` endpoint

## 📈 Performance

- **Response Time**: < 2 seconds for most queries
- **Rate Limits**: Depends on external API limits
- **Caching**: Not implemented (stateless design)
- **Concurrent Requests**: Supports async operations

## 🔒 Security

- ✅ Environment variables for secrets
- ✅ CORS configured for production
- ✅ Non-root Docker user
- ✅ Input validation on all endpoints
- ✅ Error handling without sensitive data exposure