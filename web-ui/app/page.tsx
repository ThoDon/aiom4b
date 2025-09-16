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
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { apiService, type ConversionJob, type SourceFolder } from "@/lib/api";
import { formatDate, formatFileSize } from "@/lib/utils";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Calendar,
  Download,
  Folder,
  Music,
  Pause,
  Play,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { useState } from "react";

export default function Home() {
  const [selectedFolders, setSelectedFolders] = useState<string[]>([]);
  const [outputFilename, setOutputFilename] = useState("");
  const queryClient = useQueryClient();

  // Queries
  const { data: folders = [], isLoading: foldersLoading } = useQuery({
    queryKey: ["folders"],
    queryFn: apiService.getFolders,
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  const { data: jobs = [], isLoading: jobsLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: apiService.getAllJobs,
    refetchInterval: 2000, // Refetch every 2 seconds for real-time updates
  });

  // Mutations
  const startConversionMutation = useMutation({
    mutationFn: apiService.startConversion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setSelectedFolders([]);
      setOutputFilename("");
    },
  });

  const cancelJobMutation = useMutation({
    mutationFn: apiService.cancelJob,
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

  const handleFolderToggle = (folderPath: string) => {
    setSelectedFolders((prev) =>
      prev.includes(folderPath)
        ? prev.filter((path) => path !== folderPath)
        : [...prev, folderPath]
    );
  };

  const handleStartConversion = () => {
    if (selectedFolders.length === 0) return;

    startConversionMutation.mutate({
      source_folders: selectedFolders,
      output_filename: outputFilename || undefined,
    });
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

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Music className="h-8 w-8 text-primary" />
              <h1 className="text-3xl font-bold">AIOM4B</h1>
              <Badge variant="outline" className="ml-2">
                v0.1.0
              </Badge>
            </div>
            <Button
              variant="outline"
              onClick={() => (window.location.href = "/jobs")}
            >
              <Calendar className="h-4 w-4 mr-2" />
              View All Jobs
            </Button>
          </div>
          <p className="text-muted-foreground mt-2">
            Convert MP3 files to M4B format with ease
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Source Folders */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Folder className="h-5 w-5" />
                <span>Source Folders</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    queryClient.invalidateQueries({ queryKey: ["folders"] })
                  }
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </CardTitle>
              <CardDescription>
                Select folders containing MP3 files to convert
              </CardDescription>
            </CardHeader>
            <CardContent>
              {foldersLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin" />
                  <span className="ml-2">Loading folders...</span>
                </div>
              ) : folders.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Folder className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No source folders found</p>
                  <p className="text-sm">
                    Place MP3 folders in the source directory
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {folders.map((folder) => (
                    <div
                      key={folder.path}
                      className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-accent/50 transition-colors"
                    >
                      <Checkbox
                        checked={selectedFolders.includes(folder.path)}
                        onCheckedChange={() => handleFolderToggle(folder.path)}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{folder.path}</p>
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                          <span>{folder.mp3_count} files</span>
                          <span>
                            {formatFileSize(folder.total_size_mb * 1024 * 1024)}
                          </span>
                          <span>{formatDate(folder.last_modified)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Conversion Controls */}
          <Card>
            <CardHeader>
              <CardTitle>Start Conversion</CardTitle>
              <CardDescription>
                Configure and start the MP3 to M4B conversion
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">
                  Output Filename (optional)
                </label>
                <Input
                  placeholder="my_audiobook.m4b"
                  value={outputFilename}
                  onChange={(e) => setOutputFilename(e.target.value)}
                  className="mt-1"
                />
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium">
                  Selected Folders ({selectedFolders.length})
                </p>
                {selectedFolders.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No folders selected
                  </p>
                ) : (
                  <div className="space-y-1">
                    {selectedFolders.map((folder) => (
                      <div
                        key={folder}
                        className="flex items-center justify-between p-2 bg-accent rounded"
                      >
                        <span className="text-sm truncate">{folder}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleFolderToggle(folder)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <Button
                onClick={handleStartConversion}
                disabled={
                  selectedFolders.length === 0 ||
                  startConversionMutation.isPending
                }
                className="w-full"
              >
                {startConversionMutation.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Starting...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Start Conversion
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Active Jobs */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Conversion Jobs</CardTitle>
            <CardDescription>
              Monitor active and completed conversion jobs
            </CardDescription>
          </CardHeader>
          <CardContent>
            {jobsLoading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin" />
                <span className="ml-2">Loading jobs...</span>
              </div>
            ) : jobs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Play className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No active jobs</p>
                <p className="text-sm">Start a conversion to see jobs here</p>
              </div>
            ) : (
              <div className="space-y-4">
                {jobs.map((job) => (
                  <div key={job.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <h3 className="font-medium">{job.output_filename}</h3>
                        {getStatusBadge(job.status)}
                      </div>
                      <div className="flex items-center space-x-2">
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
                        {(job.status === "queued" ||
                          job.status === "running") && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => cancelJobMutation.mutate(job.id)}
                            disabled={cancelJobMutation.isPending}
                          >
                            <Pause className="h-4 w-4 mr-2" />
                            Cancel
                          </Button>
                        )}
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
                        Source Folders:
                      </p>
                      <div className="space-y-1">
                        {job.source_folders.map((folder) => (
                          <p
                            key={folder}
                            className="text-sm text-muted-foreground truncate"
                          >
                            {folder}
                          </p>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
