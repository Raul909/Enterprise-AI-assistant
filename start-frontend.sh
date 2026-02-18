#!/bin/bash

echo "🚀 Starting Enterprise AI Assistant Frontend..."
echo ""

cd frontend

if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
fi

echo "✨ Starting development server..."
npm run dev
