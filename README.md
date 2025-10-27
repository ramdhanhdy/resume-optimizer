# AI Resume Optimizer

A full-stack AI-powered resume optimization application that uses a 5-agent pipeline to tailor your resume for specific job postings while maintaining ethical accuracy.

## Features

- 🤖 **5-Agent AI Pipeline**: Job analysis, resume optimization, implementation, validation, and polish
- 🎨 **Modern UI**: Beautiful React interface with smooth animations
- 📄 **Multi-format Support**: Upload PDF, DOCX, or images
- 🔍 **URL Ingestion**: Fetch job postings directly from URLs
- 📊 **Validation Scoring**: Multi-dimensional resume scoring
- 💾 **Application Tracking**: Save and compare multiple applications
- 📥 **Export Options**: Download in DOCX or PDF format
- 🛡️ **Ethical Grounding**: Built-in safeguards prevent fabrication

## Tech Stack

### Backend
- Python 3.11+
- FastAPI (REST API)
- OpenRouter (LLM provider)
- SQLite (database)
- Exa API (job posting retrieval)

### Frontend
- React 19
- TypeScript
- Vite
- Framer Motion (animations)
- TailwindCSS (styling)

## Project Structure

```
resume-optimizer/
├── backend/               # Python FastAPI server
│   ├── src/
│   │   ├── agents/       # AI agent implementations
│   │   ├── api/          # API clients (OpenRouter, Exa)
│   │   ├── database/     # SQLite database layer
│   │   └── utils/        # File processing utilities
│   ├── server.py         # FastAPI application
│   └── requirements.txt
├── frontend/             # React application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   └── package.json
└── README.md
```

## Setup

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file from the example:
```bash
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux
```

6. Add your API keys to `.env`:
```
OPENROUTER_API_KEY=your_actual_api_key
EXA_API_KEY=your_exa_api_key
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file:
```bash
copy .env.example .env.local  # Windows
cp .env.example .env.local    # macOS/Linux
```

4. Configure the backend URL (default is already set to `http://localhost:8000`)

## Running the Application

### Start the Backend

```bash
cd backend
python server.py
```

The API will be available at `http://localhost:8000`

### Start the Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

The application will open at `http://localhost:3000`

## Usage

1. **Upload Resume**: Upload your resume in PDF, DOCX, or image format
2. **Provide Job Details**: Paste the job posting URL or text
3. **Processing**: The 5-agent pipeline will:
   - Analyze the job posting
   - Generate optimization strategy
   - Implement changes
   - Validate accuracy
   - Polish final output
4. **Review**: Compare before/after versions with detailed explanations
5. **Export**: Download your optimized resume

## API Endpoints

- `POST /api/upload-resume` - Upload resume file
- `POST /api/analyze-job` - Analyze job posting (Agent 1)
- `POST /api/optimize-resume` - Generate strategy (Agent 2)
- `POST /api/implement` - Apply changes (Agent 3)
- `POST /api/validate` - Validate resume (Agent 4)
- `POST /api/polish` - Final polish (Agent 5)
- `GET /api/export/{id}` - Export resume
- `GET /api/applications` - List all applications
- `GET /api/application/{id}` - Get application details

## Development

### Backend Development

```bash
cd backend
uvicorn server:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Building for Production

Frontend:
```bash
cd frontend
npm run build
```

## Ethical Guidelines

All agents follow strict ethical guidelines:

- **No Fabrication**: Never create false employers, titles, dates, or metrics
- **Conservative Phrasing**: Use cautious language when uncertain
- **Validation Layer**: Agent 4 fact-checks all claims
- **Final Review**: Agent 5 removes any unsupported claims

The goal is to present your TRUE qualifications optimally, not to create fictional credentials.

## Troubleshooting

### Backend Issues

- **Import errors**: Ensure virtual environment is activated
- **API errors**: Verify API keys in `.env` file
- **Port conflicts**: Change PORT in `.env`

### Frontend Issues

- **Connection errors**: Ensure backend is running on correct port
- **CORS errors**: Check CORS_ORIGINS in backend `.env`
- **Build errors**: Delete `node_modules` and reinstall

## License

MIT License - Free to use and modify

## Credits

- Backend prototype: JobHunt Agent
- Frontend prototype: CVit
- Integrated and enhanced for full-stack operation
