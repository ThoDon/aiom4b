"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiService, type ConversionJob, type TaggingJob } from "@/lib/api";
import { formatDate, formatFileSize } from "@/lib/utils";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Calendar,
  Clock,
  Download,
  Eye,
  Filter,
  MoreHorizontal,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import { useState } from "react";

export default function JobsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [page, setPage] = useState(1);
  const [selectedJob, setSelectedJob] = useState<ConversionJob | null>(null);
  const queryClient = useQueryClient();

  const perPage = 10;

  // Queries
  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ["jobs", { status: statusFilter, page, per_page: perPage }],
    queryFn: () =>
      apiService.getJobs({
        status: statusFilter || undefined,
        page,
        per_page: perPage,
      }),
    refetchInterval: 2000, // Refetch every 2 seconds for real-time updates
  });

  const { data: taggingJobs, isLoading: taggingJobsLoading } = useQuery({
    queryKey: ["tagging-jobs"],
    queryFn: apiService.getTaggingJobs,
    refetchInterval: 2000, // Refetch every 2 seconds for real-time updates
  });

  // Mutations
  const deleteJobMutation = useMutation({
    mutationFn: apiService.deleteJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const clearOldJobsMutation = useMutation({
    mutationFn: apiService.clearOldJobs,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const downloadFile = async (jobId: string, filename: string) => {
    try {
      const blob = await apiService.downloadFile(jobId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Download failed:", error);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "queued":
        return <Badge variant="secondary">Queued</Badge>;
      case "running":
        return <Badge variant="default">Running</Badge>;
      case "completed":
        return (
          <Badge variant="default" className="bg-green-500">
            Completed
          </Badge>
        );
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "queued":
        return "text-yellow-600";
      case "running":
        return "text-blue-600";
      case "completed":
        return "text-green-600";
      case "failed":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  const filteredJobs =
    jobsData?.jobs.filter(
      (job) =>
        job.output_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.source_folders.some((folder) =>
          folder.toLowerCase().includes(searchTerm.toLowerCase())
        )
    ) || [];

  const totalPages = jobsData ? Math.ceil(jobsData.total / perPage) : 0;

  return (
    <main className="container mx-auto px-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Job Management</h1>
            <p className="text-muted-foreground mt-2">
              Monitor and manage conversion and tagging jobs
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={() => clearOldJobsMutation.mutate(30)}
              disabled={clearOldJobsMutation.isPending}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear Old Jobs
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ["jobs"] });
                queryClient.invalidateQueries({
                  queryKey: ["tagging-jobs"],
                });
              }}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      <Tabs defaultValue="conversion" className="space-y-4">
        <TabsList>
          <TabsTrigger value="conversion">Conversion Jobs</TabsTrigger>
          <TabsTrigger value="tagging">Tagging Jobs</TabsTrigger>
        </TabsList>
        <TabsContent value="conversion" className="space-y-4">
          {/* Filters and Search */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Filter className="h-5 w-5" />
                <span>Filters</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search by filename or folder..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant={statusFilter === "" ? "default" : "outline"}
                    onClick={() => setStatusFilter("")}
                    size="sm"
                  >
                    All
                  </Button>
                  <Button
                    variant={statusFilter === "queued" ? "default" : "outline"}
                    onClick={() => setStatusFilter("queued")}
                    size="sm"
                  >
                    Queued
                  </Button>
                  <Button
                    variant={statusFilter === "running" ? "default" : "outline"}
                    onClick={() => setStatusFilter("running")}
                    size="sm"
                  >
                    Running
                  </Button>
                  <Button
                    variant={
                      statusFilter === "completed" ? "default" : "outline"
                    }
                    onClick={() => setStatusFilter("completed")}
                    size="sm"
                  >
                    Completed
                  </Button>
                  <Button
                    variant={statusFilter === "failed" ? "default" : "outline"}
                    onClick={() => setStatusFilter("failed")}
                    size="sm"
                  >
                    Failed
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Jobs Table */}
          <Card>
            <CardHeader>
              <CardTitle>Conversion Jobs</CardTitle>
              <CardDescription>
                {jobsData?.total || 0} total jobs found
              </CardDescription>
            </CardHeader>
            <CardContent>
              {jobsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin" />
                  <span className="ml-2">Loading jobs...</span>
                </div>
              ) : filteredJobs.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No jobs found</p>
                  <p className="text-sm">
                    {searchTerm || statusFilter
                      ? "Try adjusting your filters"
                      : "Start a conversion to see jobs here"}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredJobs.map((job) => (
                    <div key={job.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <h3 className="font-medium">{job.output_filename}</h3>
                          {getStatusBadge(job.status)}
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setSelectedJob(job)}
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            View Details
                          </Button>
                          {job.status === "completed" && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                downloadFile(job.id, job.output_filename)
                              }
                            >
                              <Download className="h-4 w-4 mr-2" />
                              Download
                            </Button>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => deleteJobMutation.mutate(job.id)}
                            disabled={deleteJobMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>Progress</span>
                          <span>{job.progress.toFixed(1)}%</span>
                        </div>
                        <Progress value={job.progress} className="h-2" />
                      </div>

                      <Separator className="my-3" />

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="font-medium">Created</p>
                          <p className="text-muted-foreground">
                            {formatDate(job.created_at)}
                          </p>
                        </div>
                        {job.started_at && (
                          <div>
                            <p className="font-medium">Started</p>
                            <p className="text-muted-foreground">
                              {formatDate(job.started_at)}
                            </p>
                          </div>
                        )}
                        {job.completed_at && (
                          <div>
                            <p className="font-medium">Completed</p>
                            <p className="text-muted-foreground">
                              {formatDate(job.completed_at)}
                            </p>
                          </div>
                        )}
                      </div>

                      {job.error_message && (
                        <div className="mt-3 p-3 bg-destructive/10 border border-destructive/20 rounded">
                          <p className="text-sm text-destructive font-medium">
                            Error:
                          </p>
                          <p className="text-sm text-destructive">
                            {job.error_message}
                          </p>
                        </div>
                      )}

                      <div className="mt-3">
                        <p className="text-sm font-medium mb-2">
                          Source Folders ({job.source_folders.length}
                          ):
                        </p>
                        <div className="space-y-1">
                          {job.source_folders.slice(0, 3).map((folder) => (
                            <p
                              key={folder}
                              className="text-sm text-muted-foreground truncate"
                            >
                              {folder}
                            </p>
                          ))}
                          {job.source_folders.length > 3 && (
                            <p className="text-sm text-muted-foreground">
                              ... and {job.source_folders.length - 3} more
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6">
                  <p className="text-sm text-muted-foreground">
                    Page {page} of {totalPages}
                  </p>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(Math.max(1, page - 1))}
                      disabled={page === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(Math.min(totalPages, page + 1))}
                      disabled={page === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Job Details Modal */}
          {selectedJob && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
              <Card className="w-full max-w-2xl max-h-[80vh] overflow-y-auto">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Job Details</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedJob(null)}
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-medium">
                      {selectedJob.output_filename}
                    </h3>
                    {getStatusBadge(selectedJob.status)}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Progress</span>
                      <span>{selectedJob.progress.toFixed(1)}%</span>
                    </div>
                    <Progress value={selectedJob.progress} className="h-2" />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="font-medium">Job ID</p>
                      <p className="text-muted-foreground font-mono text-xs">
                        {selectedJob.id}
                      </p>
                    </div>
                    <div>
                      <p className="font-medium">Created</p>
                      <p className="text-muted-foreground">
                        {formatDate(selectedJob.created_at)}
                      </p>
                    </div>
                    {selectedJob.started_at && (
                      <div>
                        <p className="font-medium">Started</p>
                        <p className="text-muted-foreground">
                          {formatDate(selectedJob.started_at)}
                        </p>
                      </div>
                    )}
                    {selectedJob.completed_at && (
                      <div>
                        <p className="font-medium">Completed</p>
                        <p className="text-muted-foreground">
                          {formatDate(selectedJob.completed_at)}
                        </p>
                      </div>
                    )}
                  </div>

                  {selectedJob.error_message && (
                    <div className="p-3 bg-destructive/10 border border-destructive/20 rounded">
                      <p className="text-sm text-destructive font-medium">
                        Error:
                      </p>
                      <p className="text-sm text-destructive">
                        {selectedJob.error_message}
                      </p>
                    </div>
                  )}

                  <div>
                    <p className="text-sm font-medium mb-2">
                      Source Folders ({selectedJob.source_folders.length}
                      ):
                    </p>
                    <div className="space-y-1">
                      {selectedJob.source_folders.map((folder) => (
                        <p
                          key={folder}
                          className="text-sm text-muted-foreground break-all"
                        >
                          {folder}
                        </p>
                      ))}
                    </div>
                  </div>

                  {selectedJob.status === "completed" && (
                    <div className="flex justify-end">
                      <Button
                        onClick={() =>
                          downloadFile(
                            selectedJob.id,
                            selectedJob.output_filename
                          )
                        }
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download File
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="tagging" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Tagging Jobs</CardTitle>
              <CardDescription>
                Background jobs for tagging files with metadata
              </CardDescription>
            </CardHeader>
            <CardContent>
              {taggingJobsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin" />
                </div>
              ) : !taggingJobs || taggingJobs.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No tagging jobs found
                </div>
              ) : (
                <div className="space-y-4">
                  {taggingJobs.map((job) => (
                    <Card key={job.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium">
                              {job.file_path.split("/").pop()}
                            </h4>
                            {getStatusBadge(job.status)}
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                            <span>Created: {formatDate(job.created_at)}</span>
                            {job.started_at && (
                              <span>Started: {formatDate(job.started_at)}</span>
                            )}
                            {job.completed_at && (
                              <span>
                                Completed: {formatDate(job.completed_at)}
                              </span>
                            )}
                          </div>
                          {job.status === "running" && (
                            <div className="mt-2">
                              <Progress
                                value={job.progress}
                                className="w-full"
                              />
                              <p className="text-sm text-muted-foreground mt-1">
                                {job.progress}% complete
                              </p>
                            </div>
                          )}
                          {job.error_message && (
                            <p className="text-sm text-red-600 mt-2">
                              Error: {job.error_message}
                            </p>
                          )}
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </main>
  );
}
