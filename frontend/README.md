# Enterprise AI Assistant - Frontend

Modern React frontend for the Enterprise AI Assistant.

## Features

- 🎨 Beautiful, professional UI with gradient design
- 🔐 JWT authentication (login/register)
- 💬 Real-time chat interface
- 🛠️ Visual display of tools used
- 📚 Source citations
- 📱 Responsive design

## Development

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000

## Build for Production

```bash
npm run build
```

The `dist/` folder contains the production build.

## Environment Variables

Create `.env` file:

```
VITE_API_URL=http://localhost:8000/api/v1
```

For production, set this to your backend URL.

## Deployment

See [DEPLOYMENT.md](../DEPLOYMENT.md) for hosting instructions.
