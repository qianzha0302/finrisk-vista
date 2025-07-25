# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
aiofiles==23.2.1
aiosqlite==0.19.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# LangChain and AI
langchain==0.1.0
langchain-community==0.0.10
langchain-openai==0.0.5
openai==1.3.0
pypdf2==3.0.1

# Data Processing
pandas==2.1.4
numpy==1.24.3
matplotlib==3.7.2
seaborn==0.12.2
plotly==5.17.0
wordcloud==1.9.2

# Graph and Visualization
networkx==3.2.1
pyvis==0.3.2

# Export and Reporting
openpyxl==3.1.2
jinja2==3.1.2
pdfkit==1.0.0
python-pptx==0.6.21

# Vector Database
faiss-cpu==1.7.4
chromadb==0.4.18

# Utilities
requests==2.31.0
validators==0.22.0
python-magic==0.4.27

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0

# .env file template
"""
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_here

# Database Configuration
DATABASE_URL=sqlite:///./finriskgpt.db

# Model Configuration
DEFAULT_MODEL=gpt-4o
BACKUP_MODEL=gpt-4-turbo

# File Storage Configuration
UPLOAD_DIR=./uploads
PROCESSED_DOCS_DIR=./processed_docs
VECTORSTORE_DIR=./vectorstores
EXPORT_DIR=./exports

# API Configuration
MAX_FILE_SIZE=50000000  # 50MB
MAX_PARAGRAPHS_PER_ANALYSIS=200
API_RATE_LIMIT=100  # requests per hour for free tier

# External Services
WKHTMLTOPDF_PATH=/usr/local/bin/wkhtmltopdf

# Environment
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO
"""

# docker-compose.yml
version: '3.8'

services:
  finriskgpt-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=sqlite:///./data/finriskgpt.db
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./processed_docs:/app/processed_docs
      - ./vectorstores:/app/vectorstores
      - ./exports:/app/exports
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - finriskgpt-backend
    restart: unless-stopped

volumes:
  redis_data:

# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads processed_docs vectorstores exports data templates

# Set environment variables
ENV PYTHONPATH=/app
ENV WKHTMLTOPDF_PATH=/usr/bin/wkhtmltopdf

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server finriskgpt-backend:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Increase timeout for large file uploads
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # WebSocket support
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }

        # Health check
        location /health {
            proxy_pass http://backend;
        }

        # Serve frontend static files (if hosting frontend with nginx)
        location / {
            root /var/www/html;
            try_files $uri $uri/ /index.html;
        }

        # File upload size limit
        client_max_body_size 50M;
    }
}

# deploy.sh - Deployment script
#!/bin/bash

set -e

echo "🚀 Starting FinRiskGPT deployment..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

# Create necessary directories
mkdir -p data uploads processed_docs vectorstores exports logs

# Build and start services
echo "📦 Building Docker containers..."
docker-compose build

echo "🔄 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Run health check
echo "🏥 Running health check..."
if curl -f http://localhost:8000/health; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

# Run database migrations if needed
echo "🗄️ Setting up database..."
docker-compose exec finriskgpt-backend python -c "
import asyncio
from utils.database import DatabaseManager
async def setup():
    db = DatabaseManager()
    await db.initialize_database()
    print('Database initialized successfully')
asyncio.run(setup())
"

echo "🎉 FinRiskGPT deployed successfully!"
echo "📍 API Documentation: http://localhost:8000/docs"
echo "📊 Backend Health: http://localhost:8000/health"

# run_dev.py - Development server script
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Development configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        workers=1  # Single worker for development
    )

# scripts/setup_dev.py - Development setup script
import os
import asyncio
from utils.database import DatabaseManager

async def setup_development_environment():
    """Setup development environment"""
    print("🔧 Setting up FinRiskGPT development environment...")
    
    # Create directories
    directories = [
        "uploads", "processed_docs", "vectorstores", 
        "exports", "data", "templates", "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Initialize database
    print("🗄️ Initializing database...")
    db_manager = DatabaseManager()
    await db_manager.initialize_database()
    print("✅ Database initialized")
    
    # Create sample templates
    await create_sample_templates()
    
    print("🎉 Development environment setup complete!")
    print("📍 Run 'python run_dev.py' to start the development server")

async def create_sample_templates():
    """Create sample HTML templates for exports"""
    
    # Summary template
    summary_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Risk Analysis Summary</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background-color: #f8f9fa; padding: 20px; border-radius: 8px; }
        .section { margin: 20px 0; }
        .risk-item { background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 4px; }
        .high-severity { background-color: #f8d7da; }
        .medium-severity { background-color: #fff3cd; }
        .low-severity { background-color: #d1f2eb; }
    </style>
</head>
<body>
    <div class="header">
        <h1>FinRiskGPT - Risk Analysis Summary</h1>
        <p><strong>Generated:</strong> {{ generation_date }}</p>
        <p><strong>Total Paragraphs Analyzed:</strong> {{ total_paragraphs }}</p>
        <p><strong>Processing Time:</strong> {{ processing_time }} seconds</p>
    </div>
    
    <div class="section">
        <h2>Top Risk Types</h2>
        {% for risk_type, count in top_risks %}
        <div class="risk-item">
            <strong>{{ risk_type }}:</strong> {{ count }} occurrences
        </div>
        {% endfor %}
    </div>
    
    <div class="section">
        <h2>High Severity Issues</h2>
        {% for issue in high_severity_issues %}
        <div class="risk-item high-severity">
            <strong>{{ issue.risk_type }} (Severity {{ issue.severity }}):</strong>
            <p>{{ issue.excerpt }}</p>
        </div>
        {% endfor %}
    </div>
    
    <div class="section">
        <h2>Summary Statistics</h2>
        <p><strong>Risk Categories Identified:</strong> {{ risk_categories }}</p>
        <p><strong>Average Confidence Score:</strong> {{ average_confidence | round(2) }}</p>
        <p><strong>Model Used:</strong> {{ model_used }}</p>
    </div>
</body>
</html>
    """
    
    os.makedirs("templates", exist_ok=True)
    with open("templates/summary_template.html", "w") as f:
        f.write(summary_template)
    
    print("✅ Created sample templates")

if __name__ == "__main__":
    asyncio.run(setup_development_environment())

# Frontend Integration Guide (README_FRONTEND.md)

# FinRiskGPT Frontend Integration Guide

## 🎯 Overview

This guide helps you integrate the FinRiskGPT backend with a modern frontend framework using Lovable or any other frontend platform.

## 🔗 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user  
- `GET /auth/me` - Get current user info

### Document Management
- `POST /api/documents/upload` - Upload PDF document
- `GET /api/documents/{document_id}/paragraphs` - Get extracted paragraphs

### Risk Analysis
- `POST /api/analysis/risk` - Start risk analysis (returns task_id)
- `GET /api/analysis/status/{task_id}` - Get analysis progress/results
- `POST /api/analysis/multi-model` - Multi-model comparison

### RAG Queries
- `POST /api/rag/query` - Query documents using RAG
- `POST /api/rag/vectorstore/build` - Build vector store

### Risk Graphs
- `POST /api/graph/generate` - Generate interactive risk graph

### Export
- `POST /api/export/pdf` - Export analysis as PDF
- `POST /api/export/excel` - Export analysis as Excel

### Analytics
- `GET /api/analytics/dashboard` - Get user dashboard data
- `GET /api/analytics/trends` - Get risk trend analysis

## 🖥️ Frontend Implementation Example

### React/TypeScript Example

```typescript
// types/api.ts
export interface RiskAnalysisRequest {
  document_id: string;
  selected_prompts: string[];
  custom_prompts?: Record<string, string>;
  max_paragraphs?: number;
}

export interface RiskAnalysisResponse {
  analysis_id: string;
  document_id: string;
  results: any[];
  summary_statistics: any;
  processing_time: number;
}

// services/api.ts
class FinRiskGPTAPI {
  private baseURL = 'http://localhost:8000';
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
  }

  private getHeaders() {
    return {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` })
    };
  }

  async uploadDocument(file: File, metadata: any) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', metadata.document_type);
    formData.append('company', metadata.company);
    formData.append('filing_date', metadata.filing_date);

    const response = await fetch(`${this.baseURL}/api/documents/upload`, {
      method: 'POST',
      headers: {
        ...(this.token && { Authorization: `Bearer ${this.token}` })
      },
      body: formData
    });

    return response.json();
  }

  async startRiskAnalysis(request: RiskAnalysisRequest) {
    const response = await fetch(`${this.baseURL}/api/analysis/risk`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(request)
    });

    return response.json();
  }

  async getAnalysisStatus(taskId: string) {
    const response = await fetch(`${this.baseURL}/api/analysis/status/${taskId}`, {
      headers: this.getHeaders()
    });

    return response.json();
  }

  async ragQuery(documentId: string, question: string) {
    const response = await fetch(`${this.baseURL}/api/rag/query`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        document_id: documentId,
        question: question,
        top_k: 5
      })
    });

    return response.json();
  }
}

export const api = new FinRiskGPTAPI();

// components/DocumentUpload.tsx
import React, { useState } from 'react';
import { api } from '../services/api';

export const DocumentUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [metadata, setMetadata] = useState({
    document_type: '10-K',
    company: '',
    filing_date: ''
  });

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    try {
      const result = await api.uploadDocument(file, metadata);
      console.log('Upload successful:', result);
      // Handle success
    } catch (error) {
      console.error('Upload failed:', error);
      // Handle error
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <h2>Upload 10-K Document</h2>
      
      <input
        type="file"
        accept=".pdf"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      
      <div className="metadata-form">
        <input
          type="text"
          placeholder="Company Name"
          value={metadata.company}
          onChange={(e) => setMetadata({...metadata, company: e.target.value})}
        />
        
        <input
          type="date"
          value={metadata.filing_date}
          onChange={(e) => setMetadata({...metadata, filing_date: e.target.value})}
        />
        
        <select
          value={metadata.document_type}
          onChange={(e) => setMetadata({...metadata, document_type: e.target.value})}
        >
          <option value="10-K">10-K</option>
          <option value="10-Q">10-Q</option>
          <option value="8-K">8-K</option>
        </select>
      </div>
      
      <button 
        onClick={handleUpload} 
        disabled={!file || uploading}
        className="upload-button"
      >
        {uploading ? 'Uploading...' : 'Upload Document'}
      </button>
    </div>
  );
};

// components/RiskAnalysis.tsx
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export const RiskAnalysis: React.FC<{ documentId: string }> = ({ documentId }) => {
  const [selectedPrompts, setSelectedPrompts] = useState<string[]>(['risk_classifier_v2']);
  const [analysisStatus, setAnalysisStatus] = useState<any>(null);
  const [results, setResults] = useState<any>(null);

  const startAnalysis = async () => {
    try {
      const response = await api.startRiskAnalysis({
        document_id: documentId,
        selected_prompts: selectedPrompts
      });

      const taskId = response.task_id;
      
      // Poll for results
      const pollInterval = setInterval(async () => {
        const status = await api.getAnalysisStatus(taskId);
        setAnalysisStatus(status);
        
        if (status.status === 'completed') {
          setResults(status.result);
          clearInterval(pollInterval);
        } else if (status.status === 'failed') {
          clearInterval(pollInterval);
          console.error('Analysis failed:', status.error_message);
        }
      }, 2000);
      
    } catch (error) {
      console.error('Failed to start analysis:', error);
    }
  };

  return (
    <div className="risk-analysis">
      <h2>Risk Analysis</h2>
      
      <div className="prompt-selection">
        <h3>Select Analysis Prompts</h3>
        {['risk_classifier_v2', 'compliance_audit_v2', 'esg_risk_v2'].map(prompt => (
          <label key={prompt}>
            <input
              type="checkbox"
              checked={selectedPrompts.includes(prompt)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedPrompts([...selectedPrompts, prompt]);
                } else {
                  setSelectedPrompts(selectedPrompts.filter(p => p !== prompt));
                }
              }}
            />
            {prompt}
          </label>
        ))}
      </div>
      
      <button onClick={startAnalysis} className="start-analysis-button">
        Start Analysis
      </button>
      
      {analysisStatus && (
        <div className="analysis-status">
          <p>Status: {analysisStatus.status}</p>
          <p>Progress: {analysisStatus.progress}%</p>
        </div>
      )}
      
      {results && (
        <div className="analysis-results">
          <h3>Results</h3>
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
```

## 🎨 Lovable Integration

When using Lovable to create your frontend, use these key integration points:

### 1. Authentication Flow
```javascript
// Login component in Lovable
const handleLogin = async (username, password) => {
  const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  if (data.access_token) {
    localStorage.setItem('token', data.access_token);
    // Redirect to dashboard
  }
};
```

### 2. Real-time Updates with WebSocket
```javascript
// WebSocket connection for real-time analysis updates
const ws = new WebSocket('ws://localhost:8000/ws/client_123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'analysis_progress') {
    updateProgressBar(data.progress);
  }
};
```

### 3. File Upload with Progress
```javascript
const uploadWithProgress = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const xhr = new XMLHttpRequest();
  
  xhr.upload.addEventListener('progress', (e) => {
    if (e.lengthComputable) {
      const percentComplete = (e.loaded / e.total) * 100;
      onProgress(percentComplete);
    }
  });
  
  xhr.open('POST', '/api/documents/upload');
  xhr.setRequestHeader('Authorization', `Bearer ${token}`);
  xhr.send(formData);
};
```

## 🚀 Deployment Options

### Option 1: Separate Deployment
- Deploy backend on server (e.g., DigitalOcean, AWS)
- Deploy frontend on Lovable or Vercel
- Configure CORS for cross-origin requests

### Option 2: Containerized Deployment
- Use Docker Compose with both frontend and backend
- Nginx reverse proxy for routing
- SSL termination at proxy level

### Option 3: Serverless Backend
- Deploy backend as serverless functions
- Use managed databases (PostgreSQL on RDS)
- Frontend on CDN with API gateway

## 📊 Key Features to Implement

1. **Dashboard**: Risk overview, recent analyses, trends
2. **Document Manager**: Upload, view, organize documents
3. **Analysis Studio**: Configure prompts, run analyses
4. **RAG Chat**: Interactive Q&A with documents
5. **Risk Graphs**: Interactive network visualizations
6. **Export Center**: PDF/Excel report generation
7. **Settings**: User preferences, API limits, billing

## 🔧 Environment Variables for Frontend

```env
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_MAX_FILE_SIZE=50000000
REACT_APP_SUPPORTED_FORMATS=.pdf
REACT_APP_ENABLE_ANALYTICS=true
```

This comprehensive backend provides all the functionality from your Streamlit app while adding enterprise features like authentication, rate limiting, analytics, and scalable architecture. The frontend can be built using Lovable or any modern framework to create a professional, user-friendly interface.