# Frontend Setup Guide

## Quick Start

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Visit http://localhost:3000

## Features

### Authentication
- Login with existing account
- Register new account
- JWT token management
- Automatic token refresh

### Chat Interface
- Real-time messaging
- Typing indicators
- Message history
- Tool usage display
- Source citations

### User Experience
- Responsive design
- Smooth animations
- Example queries
- Error handling
- Loading states

## Configuration

### Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

For production:
```env
VITE_API_URL=https://your-backend.onrender.com/api/v1
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Login.jsx       # Authentication UI
│   │   ├── Login.css
│   │   ├── Chat.jsx        # Chat interface
│   │   └── Chat.css
│   ├── App.jsx             # Main app component
│   ├── api.js              # API client
│   ├── main.jsx            # Entry point
│   └── index.css           # Global styles
├── index.html
├── vite.config.js
└── package.json
```

## API Integration

The frontend communicates with the backend via REST API:

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/chat` - Send chat message

All authenticated requests include JWT token in Authorization header.

## Styling

- CSS-in-JS approach with separate CSS files
- Gradient theme (purple/blue)
- Responsive breakpoints
- Smooth transitions and animations

## Building for Production

```bash
npm run build
```

Output in `dist/` directory ready for deployment.

## Deployment Options

### Render
- Static Site service
- Automatic builds from Git
- Free tier available

### Vercel
```bash
npm install -g vercel
vercel --prod
```

### Netlify
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

## Troubleshooting

### CORS Errors
Ensure backend `CORS_ORIGINS` includes your frontend URL.

### API Connection Failed
Check `VITE_API_URL` in `.env` points to correct backend.

### Build Errors
Clear cache and reinstall:
```bash
rm -rf node_modules dist
npm install
npm run build
```

### Authentication Issues
Clear localStorage and try again:
```javascript
localStorage.clear()
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## Performance

- Code splitting with Vite
- Lazy loading components
- Optimized bundle size
- Fast refresh in development
