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
};
