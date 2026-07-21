# AI Powered Supply Chain Risk Management Dashboard

This is the frontend dashboard for the AI Powered Supply Chain Risk Management system. It provides a premium, modern, and responsive user interface to visualize global supply chain risks, simulate scenarios, recommend alternative suppliers, and optimize strategic reserves.

## Features
- **Live Risk Intelligence**: Monitor global risks with real-time API integrations.
- **Scenario Impact Analysis**: Visualize AI-simulated disruptions and their downstream effects.
- **Alternative Supplier Recommendation**: Execute intelligent multi-criteria supplier rankings.
- **Strategic Reserve Optimization**: AI-driven inventory and buffer stock optimization.
- **Integrated Analysis**: Run end-to-end orchestration workflows connecting all modules.
- **Premium UI**: Glassmorphism, modern gradients, dark/light modes, and Framer Motion animations.

## Tech Stack
- ReactJS (Vite)
- Bootstrap 5
- React Router DOM
- Axios
- Framer Motion
- Recharts
- React Icons

## Folder Structure
```
src/
├── assets/          # Static files and images
├── components/      # Reusable UI components (Sidebar, Navbar, KPICard, Loader)
├── contexts/        # React Context API (ThemeContext, AnalysisContext)
├── hooks/           # Custom React hooks
├── layouts/         # Layout components (MainLayout)
├── pages/           # Application pages (Dashboard, LiveRisk, FinalReport, etc.)
├── services/        # Axios API configurations and endpoints
├── styles/          # Global styles, variables, glassmorphism CSS
├── utils/           # Utility functions
├── App.jsx          # Routing configuration
└── main.jsx         # Application entry point
```

## Dependencies
Ensure you have Node.js installed.
- `react`, `react-dom`
- `bootstrap`
- `react-router-dom`
- `axios`
- `framer-motion`
- `recharts`
- `react-icons`

## Installation
1. Navigate to the frontend directory:
   ```bash
   cd d:/Project/Frontend
   ```
2. Install the required dependencies:
   ```bash
   npm install
   ```

## Environment Variables
Create a `.env` file in the root of the `Frontend` directory with the following content:
```env
VITE_API_BASE_URL=http://127.0.0.1:8080
```
*Note: Make sure the URL matches the address where your backend API is running.*

## Running the Application
### Connecting to Backend
1. Ensure the unified FastAPI backend server is running (e.g., `uvicorn unified_server:app --host 127.0.0.1 --port 8080`).
2. The frontend automatically detects the `.env` configuration.

### Running Frontend
Start the Vite development server:
```bash
npm run dev
```
Open the provided local URL (usually `http://localhost:5173`) in your browser to view the application.
