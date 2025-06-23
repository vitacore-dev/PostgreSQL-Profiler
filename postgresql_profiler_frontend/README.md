# PostgreSQL Profiler Frontend

React-based frontend application for PostgreSQL database performance monitoring and profiling.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or pnpm

### Installation

```bash
# Install dependencies
npm install
# or
pnpm install
```

### Environment Configuration

1. Copy the environment template:
```bash
cp .env.example .env.local
```

2. Configure your API URL in `.env.local`:
```bash
# Backend API URL
VITE_API_URL=http://localhost:5000/api
```

### Development

```bash
# Start development server
npm run dev
# or
pnpm dev
```

The application will be available at `http://localhost:3000`

### Production Build

```bash
# Build for production
npm run build
# or
pnpm build

# Preview production build
npm run preview
# or
pnpm preview
```

## 🔧 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:5000/api` | Yes |

### Environment Examples

**Development:**
```bash
VITE_API_URL=http://localhost:5000/api
```

**Production:**
```bash
VITE_API_URL=https://your-api-domain.com/api
```

**Docker:**
```bash
VITE_API_URL=http://postgresql-profiler-backend:5000/api
```

## 📁 Project Structure

```
src/
├── components/          # React components
│   ├── Dashboard.jsx    # Main dashboard
│   ├── DatabaseConnections.jsx
│   ├── PerformanceMetrics.jsx
│   ├── Alerts.jsx
│   ├── Recommendations.jsx
│   └── ui/             # UI components
├── lib/                # Utilities
├── main.jsx           # Application entry point
└── App.jsx            # Root component
```

## 🔌 API Integration

All components use the `VITE_API_URL` environment variable for backend communication:

```javascript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
```

### Key Components:

#### Recommendations Component
- **Endpoint**: `/api/recommendations`
- **Features**: AI-powered optimization recommendations
- **Response Format**: `{ status: 'success', data: [...] }`
- **Apply Endpoint**: `POST /api/recommendations/{id}/apply`

#### Other Components
- **Dashboard**: Overview and statistics
- **DatabaseConnections**: Database management
- **PerformanceMetrics**: Real-time metrics
- **Alerts**: System alerts and notifications

## 🛠 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🐳 Docker Support

The frontend can be containerized and deployed with Docker. Make sure to set the correct `VITE_API_URL` for your environment.

## 📝 Notes

- This project uses Vite as the build tool
- Environment variables must be prefixed with `VITE_` to be accessible in the browser
- The application automatically falls back to `http://localhost:5000/api` if `VITE_API_URL` is not set

