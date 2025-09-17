# Web UI Documentation

## Overview

The AIOM4B web interface is built with Next.js 15, TypeScript, and Tailwind CSS. It provides a modern, responsive interface for managing MP3 to M4B conversions with real-time job tracking and comprehensive job management features.

## Technology Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **React Query** - Server state management
- **Lucide React** - Icon library
- **Axios** - HTTP client

## Project Structure

```
web-ui/
├── app/                    # Next.js App Router
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout component
│   ├── page.tsx           # Home page (conversion interface)
│   ├── tagging/           # Tagging management pages
│   │   └── page.tsx       # Tagging dashboard
│   ├── jobs/              # Jobs management pages
│   │   └── page.tsx       # Jobs dashboard
│   └── providers.tsx      # React Query provider
├── components/            # Reusable UI components
│   └── ui/               # Base UI components
│       ├── badge.tsx     # Status badges
│       ├── button.tsx    # Button component
│       ├── card.tsx      # Card layout
│       ├── checkbox.tsx  # Checkbox input
│       ├── input.tsx     # Text input
│       ├── progress.tsx  # Progress bar
│       └── separator.tsx # Visual separator
├── lib/                  # Utilities and API client
│   ├── api.ts           # API service functions
│   └── utils.ts         # Utility functions
├── package.json         # Dependencies and scripts
├── tailwind.config.js   # Tailwind configuration
└── tsconfig.json        # TypeScript configuration
```

## Pages and Components

### 1. Home Page (`/`)

The main conversion interface where users can:

- **Browse Source Folders**: View available MP3 folders with metadata
- **Select Folders**: Choose multiple folders for conversion
- **Configure Individual Outputs**: Set custom output filename for each selected folder
- **Start Multiple Conversions**: Initiate separate conversion jobs for each folder
- **Monitor Active Jobs**: View real-time job progress for all active conversions

#### Key Features

- **Real-time Updates**: Auto-refresh every 2 seconds
- **Folder Selection**: Multi-select with checkboxes
- **Individual Filename Configuration**: Each selected folder gets its own output filename input
- **Separate Job Creation**: Each folder creates its own conversion job and M4B file
- **Progress Tracking**: Visual progress bars for each job
- **Status Badges**: Color-coded job status indicators
- **Download Links**: Direct download for completed jobs
- **Error Handling**: User-friendly error messages

#### Components Used

- `Card` - Layout containers
- `Checkbox` - Folder selection
- `Input` - Output filename
- `Button` - Actions and controls
- `Progress` - Job progress visualization
- `Badge` - Status indicators
- `Separator` - Visual organization

### 2. Tagging Dashboard (`/tagging`)

The tagging management interface provides comprehensive file tagging capabilities:

- **File List**: View all converted but untagged M4B files
- **Search Interface**: Manual search with custom queries for Audible API
- **Result Selection**: Choose from multiple search results with book details
- **Progress Tracking**: Real-time job status updates for tagging operations
- **File Management**: Delete untagged files if needed
- **Metadata Display**: Show current tagging status and metadata

#### Key Features

- **Untagged File Detection**: Automatically identifies files needing metadata
- **Audible API Integration**: Search across multiple Audible locales
- **Interactive Search**: Custom search queries with real-time results
- **Metadata Application**: One-click metadata application to files
- **Job Tracking**: Background job processing with progress monitoring
- **File Management**: Delete unwanted files from the system

#### Components Used

- `Tabs` - Separate tabs for files and jobs
- `Table` - File listing with metadata
- `Dialog` - Search interface modal
- `Card` - Search result display
- `Button` - Actions and controls
- `Progress` - Job progress visualization
- `Badge` - Status indicators

### 3. Jobs Dashboard (`/jobs`)

Comprehensive job management interface featuring:

- **Job Listing**: Paginated table of all conversion and tagging jobs
- **Filtering**: Filter by status (queued, running, completed, failed) and type (conversion, tagging)
- **Search**: Search by filename or folder path
- **Pagination**: Navigate through large job lists
- **Job Details**: Modal with detailed job information
- **Bulk Operations**: Clear old jobs, delete individual jobs
- **Tabbed Interface**: Separate tabs for conversion and tagging jobs

#### Key Features

- **Advanced Filtering**: Status-based filtering
- **Search Functionality**: Text search across jobs
- **Pagination**: Handle large numbers of jobs
- **Job Details Modal**: Comprehensive job information
- **Bulk Cleanup**: Remove old completed/failed jobs
- **Real-time Updates**: Live job status updates

#### Components Used

- `Card` - Main layout containers
- `Input` - Search functionality
- `Button` - Actions and navigation
- `Badge` - Status indicators
- `Progress` - Job progress
- `Separator` - Visual organization

## API Integration

### API Service (`lib/api.ts`)

Centralized API client with the following functions:

```typescript
export const apiService = {
  // Folder management
  getFolders: () => Promise<SourceFolder[]>,

  // Job management
  getAllJobs: () => Promise<ConversionJob[]>,
  getJobs: (params?) => Promise<JobListResponse>,
  createJob: (data: JobCreate) => Promise<JobResponse>,
  getJobDetails: (id: string) => Promise<ConversionJob>,
  deleteJob: (id: string) => Promise<{ message: string }>,
  clearOldJobs: (days: number) => Promise<{ message: string }>,

  // Conversion
  startConversion: (data: ConversionRequest) => Promise<JobResponse[]>,
  getJobStatus: (id: string) => Promise<ConversionJob>,
  downloadFile: (id: string) => Promise<Blob>,
  cancelJob: (id: string) => Promise<{ message: string }>,
};
```

### Data Types

```typescript
interface ConversionJob {
  id: string;
  source_folders: string[];
  output_filename: string;
  status: "queued" | "running" | "completed" | "failed";
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  progress: number;
  output_path?: string;
}

interface SourceFolder {
  path: string;
  mp3_count: number;
  total_size_mb: number;
  last_modified: string;
}

interface JobListResponse {
  jobs: ConversionJob[];
  total: number;
  page: number;
  per_page: number;
}

interface ConversionRequest {
  folder_conversions: Record<string, string | null>;
}
```

## State Management

### React Query Integration

The application uses React Query for server state management:

```typescript
// Auto-refreshing queries
const { data: jobs = [], isLoading: jobsLoading } = useQuery({
  queryKey: ["jobs", { status: statusFilter, page, per_page: perPage }],
  queryFn: () =>
    apiService.getJobs({
      status: statusFilter || undefined,
      page,
      per_page: perPage,
    }),
  refetchInterval: 2000, // Real-time updates
});

// Mutations with cache invalidation
const deleteJobMutation = useMutation({
  mutationFn: apiService.deleteJob,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["jobs"] });
  },
});
```

### Local State

- **Selected Folders**: Array of selected folder paths
- **Output Filenames**: Record mapping folder paths to custom output filenames
- **Search Term**: Job search filter
- **Status Filter**: Job status filter
- **Pagination**: Current page and items per page
- **Selected Job**: Job details modal state

## Styling and Design

### Tailwind CSS Configuration

```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: "hsl(var(--primary))",
        secondary: "hsl(var(--secondary))",
        muted: "hsl(var(--muted))",
        accent: "hsl(var(--accent))",
        destructive: "hsl(var(--destructive))",
      },
    },
  },
  plugins: [],
};
```

### Design System

- **Color Scheme**: CSS custom properties for theming
- **Typography**: Consistent font sizing and spacing
- **Spacing**: Tailwind's spacing scale
- **Components**: Reusable UI components with consistent styling
- **Responsive**: Mobile-first responsive design

## User Experience Features

### Real-time Updates

- **Auto-refresh**: Jobs list updates every 2 seconds
- **Progress Tracking**: Live progress bar updates
- **Status Changes**: Immediate status badge updates
- **Error Handling**: Real-time error message display

### Interactive Elements

- **Folder Selection**: Multi-select with visual feedback
- **Job Actions**: Download, cancel, delete operations
- **Search and Filter**: Instant filtering and search
- **Pagination**: Smooth navigation through job lists
- **Modal Dialogs**: Detailed job information display

### Accessibility

- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: Proper ARIA labels and roles
- **Color Contrast**: WCAG compliant color combinations
- **Focus Management**: Clear focus indicators

## Performance Optimizations

### Code Splitting

- **Route-based Splitting**: Automatic code splitting by route
- **Component Lazy Loading**: Lazy load heavy components
- **Bundle Optimization**: Tree shaking and minification

### Data Fetching

- **Query Caching**: React Query caching for API responses
- **Background Refetching**: Automatic background updates
- **Optimistic Updates**: Immediate UI feedback
- **Error Boundaries**: Graceful error handling

### UI Performance

- **Virtual Scrolling**: For large job lists (future enhancement)
- **Debounced Search**: Optimized search input
- **Memoization**: React.memo for expensive components
- **Efficient Re-renders**: Optimized state updates

## Development Workflow

### Local Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Environment Configuration

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Code Quality

- **TypeScript**: Full type safety
- **ESLint**: Code linting and formatting
- **Prettier**: Code formatting
- **Husky**: Git hooks for quality checks

## Future Enhancements

### Planned Features

- **WebSocket Support**: Real-time job updates
- **Drag and Drop**: File upload interface
- **Job Scheduling**: Scheduled conversions
- **User Authentication**: Multi-user support
- **Job Templates**: Saved conversion configurations
- **Analytics Dashboard**: Conversion statistics
- **Mobile App**: React Native mobile interface

### Performance Improvements

- **Virtual Scrolling**: Handle thousands of jobs
- **Infinite Scrolling**: Load jobs on demand
- **Service Worker**: Offline functionality
- **PWA Support**: Progressive Web App features

## Deployment

### Build Process

```bash
# Production build
npm run build

# Static export (if needed)
npm run export
```

### Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_APP_NAME` - Application name
- `NEXT_PUBLIC_APP_VERSION` - Application version

### Docker Support

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```
