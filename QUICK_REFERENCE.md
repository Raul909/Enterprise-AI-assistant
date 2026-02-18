# Quick Reference Card

## 🚀 Start Development

```bash
# Quick start
./start-frontend.sh

# Or manually
cd frontend
npm install
npm run dev
```

## 📦 Build & Deploy

```bash
# Build
npm run build

# Deploy to Render
# 1. Create Static Site
# 2. Root: frontend
# 3. Build: npm install && npm run build
# 4. Publish: frontend/dist

# Deploy to Vercel
vercel --prod

# Deploy to Netlify
netlify deploy --prod --dir=dist
```

## ⚙️ Configuration

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000/api/v1
```

### Backend (environment variables)
```env
CORS_ORIGINS=http://localhost:3000,https://your-frontend.com
```

## 🎨 UI Components

### Login
- Email/password authentication
- Register new users
- JWT token management
- Error handling

### Chat
- Real-time messaging
- Tool usage badges
- Source citations
- Example queries
- Typing indicators

## 🔧 Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **Axios** - HTTP client
- **Lucide React** - Icons
- **CSS3** - Styling

## 📝 Key Files

| File | Purpose |
|------|---------|
| `src/App.jsx` | Main app logic |
| `src/api.js` | API client |
| `src/components/Login.jsx` | Auth UI |
| `src/components/Chat.jsx` | Chat UI |
| `vite.config.js` | Build config |
| `package.json` | Dependencies |

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| CORS error | Add frontend URL to backend CORS_ORIGINS |
| API connection failed | Check VITE_API_URL in .env |
| Auth not working | Clear localStorage |
| Build fails | Delete node_modules, reinstall |

## 📚 Documentation

- `frontend/README.md` - Quick start
- `frontend/SETUP.md` - Detailed setup
- `DEPLOYMENT.md` - Deployment guide
- `FRONTEND_CHECKLIST.md` - Deployment checklist

## 🎯 URLs

| Environment | URL |
|-------------|-----|
| Development | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Production | https://your-app.onrender.com |

## ✅ Testing Checklist

- [ ] Login works
- [ ] Register works
- [ ] Chat sends messages
- [ ] Responses display
- [ ] Tools show up
- [ ] Sources display
- [ ] Logout works
- [ ] Mobile responsive

## 🎨 Color Palette

- Primary: `#667eea` → `#764ba2`
- Background: `#ffffff`
- Text: `#1a202c`
- Secondary: `#718096`
- Border: `#e2e8f0`

## 📞 Support

Check documentation files for detailed information:
- Implementation: `FRONTEND_SUMMARY.md`
- UI Design: `frontend/UI_PREVIEW.md`
- Deployment: `DEPLOYMENT.md`
