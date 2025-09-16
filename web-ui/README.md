# AIOM4B Web UI

A modern web interface for the AIOM4B MP3 to M4B conversion application.

## Features

- 🎵 **Source Folder Management**: Browse and select MP3 folders
- 🚀 **Conversion Jobs**: Start and monitor conversion jobs
- 📊 **Real-time Progress**: Live progress tracking with visual indicators
- 📥 **File Download**: Direct download of converted M4B files
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- 🎨 **Modern UI**: Clean interface built with shadcn/ui components

## Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **TailwindCSS** - Utility-first CSS framework
- **shadcn/ui** - Modern UI component library
- **TanStack Query** - Server state management
- **Axios** - HTTP client for API communication

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- AIOM4B backend running on port 8000

### Installation

1. **Install dependencies**

   ```bash
   npm install
   ```

2. **Set up environment variables**

   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your configuration
   ```

3. **Start development server**

   ```bash
   npm run dev
   ```

4. **Open in browser**
   ```
   http://localhost:3000
   ```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler

## Project Structure

```
web-ui/
├── app/                 # Next.js App Router
├── components/          # Reusable UI components
├── lib/                # Utility libraries
├── public/             # Static assets
└── styles/             # Global styles
```

## Configuration

### Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000/api/v1)
- `NEXT_PUBLIC_DEBUG` - Enable debug mode (default: false)

### API Integration

The web UI communicates with the AIOM4B backend through REST API endpoints:

- `GET /folders` - List source folders
- `POST /convert` - Start conversion job
- `GET /jobs` - List all jobs
- `GET /jobs/{id}` - Get job status
- `GET /download/{id}` - Download converted file
- `DELETE /jobs/{id}` - Cancel job

## Development

### Code Style

- TypeScript for type safety
- ESLint for code linting
- Prettier for code formatting
- TailwindCSS for styling

### Component Development

Components are built using shadcn/ui primitives and follow the design system:

```tsx
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function MyComponent() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>My Component</CardTitle>
      </CardHeader>
      <CardContent>
        <Button>Click me</Button>
      </CardContent>
    </Card>
  );
}
```

## Deployment

### Build for Production

```bash
npm run build
```

### Docker Deployment

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
