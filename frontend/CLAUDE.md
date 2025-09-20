# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
npm run dev          # Start development server on http://localhost:3000
npm run build        # Build production version
npm start           # Start production server
npm run lint        # Run ESLint
```

### Testing AI Features
```bash
node test-ai-client.js  # Test OpenAI integration directly
```

## Architecture Overview

This is a Next.js 14 application that generates HTML5 games through a multi-agent AI system. The architecture follows a specialized agent pattern where different AI agents handle specific aspects of game generation.

### Core System Components

**Multi-Agent Game Generation Flow**:
1. **GameAgents** (app/lib/gameAgents.ts) - Main orchestrator coordinating all agents
2. **GameLogicAgent** (app/lib/agents/gameLogicAgent.ts) - Designs core game mechanics
3. **GameFileGenerateAgent** (app/lib/agents/fileGnerateAgent.ts) - Creates HTML/CSS/JS files
4. **ImageResourceAgent** (app/lib/agents/imageResourceAgent.ts) - Handles visual assets
5. **AudioResourceAgent** (app/lib/agents/audioResourceAgent.ts) - Manages audio resources
6. **ScriptIntegrationAgent** (app/lib/agents/scriptIntegrationAgent.ts) - Combines all outputs

**Frontend Structure**:
- **Split Interface**: Left panel for game preview, right panel for chat
- **GamePreview** (app/components/GamePreview.tsx) - Renders games in iframe sandbox
- **ChatHistory** (app/components/ChatHistory.tsx) - Shows conversation and version history
- **SourceViewer** (app/components/SourceViewer.tsx) - Code editing with Monaco Editor

### Game Generation Pipeline

1. **Input Processing**: User natural language → Game type classification
2. **Template Selection**: Platform, Snake, or Collect games from gameTemplates.ts
3. **File Generation**: HTML structure + CSS styling + JS game logic
4. **Resource Integration**: Images and audio assets embedded
5. **Version Management**: Each generation creates new GameVersion with full file sets

### Data Models

- **GameVersion**: Contains complete game state (HTML, CSS, JS files)
- **GameFiles**: Three-file structure for each game
- **Message**: Chat history between user and AI
- **GameGenerationResult**: Complete output from multi-agent system

### Key Files

- **app/page.tsx**: Main application container with state management
- **app/lib/aiClient.ts**: OpenAI API integration layer
- **app/lib/htmlGenerator.ts**: Creates complete HTML5 game structure
- **app/types.ts**: TypeScript interfaces for all data models

### Development Notes

- Uses Next.js App Router with TypeScript
- Tailwind CSS for styling with dark theme on chat panel
- Monaco Editor for real-time code editing
- Games run in sandboxed iframes for security
- No database - all state managed in React state
- Environment variable: OPENAI_API_KEY required for AI features