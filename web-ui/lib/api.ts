import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Types
export interface SourceFolder {
  path: string;
  mp3_count: number;
  total_size_mb: number;
  last_modified: string;
}

export interface ConversionJob {
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

export interface ConversionRequest {
  folder_conversions: Record<string, string | null>;
}

export interface JobResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface JobCreate {
  input_folders: string[];
}

export interface JobListResponse {
  jobs: ConversionJob[];
  total: number;
  page: number;
  per_page: number;
}

// Tagging types
export interface TaggedFile {
  id: string;
  file_path: string;
  asin?: string;
  title?: string;
  author?: string;
  narrator?: string;
  series?: string;
  series_part?: string;
  description?: string;
  cover_url?: string;
  cover_path?: string;
  is_tagged: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaggedFileListResponse {
  files: TaggedFile[];
  total: number;
  page: number;
  per_page: number;
}

export interface AudibleSearchResult {
  title: string;
  author: string;
  narrator?: string;
  series?: string;
  asin: string;
  locale: string;
}

export interface TaggingJob {
  id: string;
  file_path: string;
  status: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  progress: number;
  metadata?: any;
}

export interface UnifiedJob {
  id: string;
  job_type: "conversion" | "tagging";
  status: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  progress: number;

  // Conversion job fields
  source_folders?: string[];
  output_filename?: string;
  output_path?: string;
  backup_paths?: string[];

  // Tagging job fields
  file_path?: string;
  metadata?: any;
}

export interface UnifiedJobListResponse {
  jobs: UnifiedJob[];
  total: number;
  page: number;
  per_page: number;
}

export interface TaggingJobCreate {
  file_path: string;
  asin?: string;
}

export interface ReadyFile {
  filename: string;
  path: string;
  size_mb: number;
  created_at: string;
}

// API functions
export const apiService = {
  // Get all source folders
  getFolders: async (): Promise<SourceFolder[]> => {
    const response = await api.get("/folders");
    return response.data;
  },

  // Start conversion jobs (one per folder)
  startConversion: async (
    request: ConversionRequest
  ): Promise<JobResponse[]> => {
    const response = await api.post("/convert", request);
    return response.data;
  },

  // Get job status
  getJobStatus: async (jobId: string): Promise<ConversionJob> => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },

  // Get all jobs
  getAllJobs: async (): Promise<ConversionJob[]> => {
    const response = await api.get("/jobs");
    return response.data;
  },

  // Get jobs with pagination and filtering
  getJobs: async (params?: {
    status?: string;
    page?: number;
    per_page?: number;
  }): Promise<JobListResponse> => {
    const response = await api.get("/jobs/paginated", { params });
    return response.data;
  },

  // Create a new job
  createJob: async (jobData: JobCreate): Promise<JobResponse> => {
    const response = await api.post("/jobs", jobData);
    return response.data;
  },

  // Get job details
  getJobDetails: async (jobId: string): Promise<ConversionJob> => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },

  // Delete a job
  deleteJob: async (jobId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/jobs/${jobId}`);
    return response.data;
  },

  // Clear old jobs
  clearOldJobs: async (daysOld: number = 30): Promise<{ message: string }> => {
    const response = await api.post("/jobs/clear", null, {
      params: { days_old: daysOld },
    });
    return response.data;
  },

  // Download converted file
  downloadFile: async (jobId: string): Promise<Blob> => {
    const response = await api.get(`/download/${jobId}`, {
      responseType: "blob",
    });
    return response.data;
  },

  // Cancel job
  cancelJob: async (jobId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/jobs/${jobId}`);
    return response.data;
  },

  // Tagging API functions
  // Get untagged files
  getUntaggedFiles: async (params?: {
    page?: number;
    per_page?: number;
  }): Promise<TaggedFileListResponse> => {
    const response = await api.get("/files/untagged", { params });
    return response.data;
  },

  // Create tagging job
  createTaggingJob: async (jobData: TaggingJobCreate): Promise<JobResponse> => {
    const response = await api.post("/jobs/tagging", jobData);
    return response.data;
  },

  // Get file by path to get UUID
  getFileByPath: async (filePath: string): Promise<TaggedFile | null> => {
    const response = await api.get("/files/by-path", {
      params: { file_path: filePath },
    });
    return response.data;
  },

  // Search Audible API
  searchAudible: async (
    fileId: string,
    query: string
  ): Promise<AudibleSearchResult[]> => {
    const response = await api.post(`/files/${fileId}/search`, null, {
      params: { query },
    });
    return response.data;
  },

  // Apply metadata to file
  applyMetadata: async (
    fileId: string,
    asin: string
  ): Promise<{ message: string }> => {
    const response = await api.post(`/files/${fileId}/apply`, null, {
      params: { asin },
    });
    return response.data;
  },

  // Get tagging jobs
  getTaggingJobs: async (): Promise<TaggingJob[]> => {
    const response = await api.get("/jobs/tagging");
    return response.data;
  },

  // Get tagging job details
  getTaggingJobDetails: async (jobId: string): Promise<TaggingJob> => {
    const response = await api.get(`/jobs/tagging/${jobId}`);
    return response.data;
  },

  // Delete tagged file
  deleteTaggedFile: async (fileId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/files/${fileId}`);
    return response.data;
  },

  // Unified jobs API functions
  // Get unified jobs (conversion and tagging)
  getUnifiedJobs: async (params?: {
    status?: string;
    type?: string;
    page?: number;
    per_page?: number;
  }): Promise<UnifiedJobListResponse> => {
    const response = await api.get("/jobs/unified", { params });
    return response.data;
  },

  // Get ready files (still needed for home page tagging section)
  getReadyFiles: async (): Promise<ReadyFile[]> => {
    const response = await api.get("/files/ready");
    return response.data;
  },
};
