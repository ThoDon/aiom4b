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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  apiService,
  type AudibleSearchResult,
  type ConversionJob,
  type ConversionRequest,
  type SourceFolder,
  type TaggedFile,
  type TaggingJob,
} from "@/lib/api";
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
  Search,
  Tag,
  Trash2,
  Zap,
} from "lucide-react";
import { useState } from "react";

export default function Home() {
  const [selectedFolders, setSelectedFolders] = useState<string[]>([]);
  const [outputFilenames, setOutputFilenames] = useState<
    Record<string, string>
  >({});
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<AudibleSearchResult[]>([]);
  const [selectedFile, setSelectedFile] = useState<TaggedFile | null>(null);
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searching, setSearching] = useState(false);
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

  const { data: readyFiles = [], isLoading: readyFilesLoading } = useQuery({
    queryKey: ["ready-files"],
    queryFn: apiService.getReadyFiles,
    refetchInterval: 5000, // Refetch every 5 seconds
  });

  // Use readyFiles instead of untaggedFiles for the new workflow
  const untaggedFiles = readyFiles.map((file) => ({
    id: file.path, // Use path as ID since ReadyFile doesn't have an ID
    file_path: file.path,
    filename: file.filename,
    size_mb: file.size_mb,
    is_tagged: false, // These files are ready for tagging, so they're not tagged yet
    created_at: file.created_at,
    updated_at: file.created_at, // Use created_at as updated_at since we don't have separate updated_at
  }));

  const { data: taggingJobs = [], isLoading: taggingJobsLoading } = useQuery({
    queryKey: ["tagging-jobs"],
    queryFn: apiService.getTaggingJobs,
    refetchInterval: 2000, // Refetch every 2 seconds for real-time updates
  });

  // Mutations
  const startConversionMutation = useMutation({
    mutationFn: apiService.startConversion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setSelectedFolders([]);
      setOutputFilenames({});
    },
  });

  const cancelJobMutation = useMutation({
    mutationFn: apiService.cancelJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const createTaggingJobMutation = useMutation({
    mutationFn: apiService.createTaggingJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tagging-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["ready-files"] });
    },
  });

  const applyMetadataMutation = useMutation({
    mutationFn: ({ fileId, asin }: { fileId: string; asin: string }) =>
      apiService.applyMetadata(fileId, asin),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ready-files"] });
      setSearchDialogOpen(false);
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
    setSelectedFolders((prev) => {
      const newSelected = prev.includes(folderPath)
        ? prev.filter((path) => path !== folderPath)
        : [...prev, folderPath];

      // Clean up output filenames for removed folders
      if (!newSelected.includes(folderPath)) {
        setOutputFilenames((prevFilenames) => {
          const newFilenames = { ...prevFilenames };
          delete newFilenames[folderPath];
          return newFilenames;
        });
      }

      return newSelected;
    });
  };

  const handleSelectAll = () => {
    if (selectedFolders.length === folders.length) {
      // Deselect all
      setSelectedFolders([]);
      setOutputFilenames({});
    } else {
      // Select all
      const allFolderPaths = folders.map((folder) => folder.path);
      setSelectedFolders(allFolderPaths);
    }
  };

  const handleStartConversion = () => {
    if (selectedFolders.length === 0) return;

    // Create folder conversions mapping
    const folderConversions: Record<string, string | null> = {};
    selectedFolders.forEach((folder) => {
      folderConversions[folder] = outputFilenames[folder] || null;
    });

    startConversionMutation.mutate({
      folder_conversions: folderConversions,
    });
  };

  // Tagging functions
  const searchAudible = async (filePath: string, query: string) => {
    setSearching(true);
    try {
      // First get the file UUID by path
      const fileInfo = await apiService.getFileByPath(filePath);
      if (!fileInfo) {
        console.error("File not found in database:", filePath);
        return;
      }

      // Then search using the UUID
      const results = await apiService.searchAudible(fileInfo.id, query);
      setSearchResults(results);
    } catch (error) {
      console.error("Error searching Audible:", error);
    } finally {
      setSearching(false);
    }
  };

  const startTaggingJob = async (fileId: string) => {
    const file = untaggedFiles.find((f) => f.id === fileId);
    if (!file) return;

    createTaggingJobMutation.mutate({
      file_path: file.file_path,
    });
  };

  const applyMetadata = async (filePath: string, asin: string) => {
    try {
      // First get the file UUID by path
      const fileInfo = await apiService.getFileByPath(filePath);
      if (!fileInfo) {
        console.error("File not found in database:", filePath);
        return;
      }

      // Then apply metadata using the UUID
      applyMetadataMutation.mutate({ fileId: fileInfo.id, asin });
    } catch (error) {
      console.error("Error applying metadata:", error);
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

  return (
    <>
      {/* File Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Folder className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium">Source Folders</p>
                <p className="text-2xl font-bold">{folders.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Tag className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">Ready to Tag</p>
                <p className="text-2xl font-bold">{readyFiles.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Play className="h-5 w-5 text-purple-500" />
              <div>
                <p className="text-sm font-medium">Active Jobs</p>
                <p className="text-2xl font-bold">
                  {jobs.filter((j) => j.status === "running").length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
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
                  queryClient.invalidateQueries({
                    queryKey: ["folders"],
                  })
                }
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </CardTitle>
            <CardDescription className="flex flex-col gap-2">
              Select folders containing MP3 files to convert
              {!foldersLoading && folders.length > 0 && (
                <div
                  className="flex items-center space-x-2 pb-3 border-b cursor-pointer"
                  onClick={handleSelectAll}
                >
                  <Checkbox
                    checked={
                      selectedFolders.length === folders.length &&
                      folders.length > 0
                    }
                    onCheckedChange={handleSelectAll}
                  />
                  <label className="text-sm font-medium cursor-pointer">
                    Select All ({folders.length} folders)
                  </label>
                </div>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="max-h-[500px] overflow-y-auto">
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
                    onClick={() => handleFolderToggle(folder.path)}
                    className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer"
                  >
                    <Checkbox
                      checked={selectedFolders.includes(folder.path)}
                      onCheckedChange={() => handleFolderToggle(folder.path)}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">
                        {folder.path.split("/").pop()}
                      </p>
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
          <CardContent className="space-y-4 ">
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              <p className="text-sm font-medium">
                Selected Folders ({selectedFolders.length})
              </p>
              {selectedFolders.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No folders selected
                </p>
              ) : (
                <div className="space-y-3">
                  {selectedFolders.map((folder) => (
                    <div
                      key={folder}
                      className="p-3 bg-accent rounded-lg space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium truncate">
                          {folder.split("/").pop()}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleFolderToggle(folder)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground">
                          Output Filename (optional)
                        </label>
                        <Input
                          placeholder="my_audiobook.m4b"
                          value={outputFilenames[folder] || ""}
                          onChange={(e) =>
                            setOutputFilenames((prev) => ({
                              ...prev,
                              [folder]: e.target.value,
                            }))
                          }
                          className="mt-1 text-sm"
                        />
                      </div>
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

        {/* Tagging Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Tag className="h-5 w-5" />
              <span>File Tagging</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  queryClient.invalidateQueries({
                    queryKey: ["untagged-files"],
                  })
                }
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </CardTitle>
            <CardDescription>
              Tag converted M4B files with metadata
            </CardDescription>
          </CardHeader>
          <CardContent className="max-h-[500px] overflow-y-auto">
            {readyFilesLoading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin" />
                <span className="ml-2">Loading files...</span>
              </div>
            ) : untaggedFiles.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Tag className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No untagged files found</p>
                <p className="text-sm">Convert some files to see them here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {untaggedFiles.slice(0, 5).map((file) => (
                  <div
                    key={file.id}
                    className="p-3 border rounded-lg space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium truncate">
                        {file.file_path.split("/").pop()}
                      </span>
                    </div>
                    <div className="flex space-x-2">
                      <Dialog
                        open={searchDialogOpen && selectedFile?.id === file.id}
                        onOpenChange={(open) => {
                          setSearchDialogOpen(open);
                          if (!open) setSelectedFile(null);
                        }}
                      >
                        <DialogTrigger asChild>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedFile(file);
                              const filename =
                                file.file_path.split("/").pop() || "";
                              const filenameWithoutExt = filename.replace(
                                /\.[^/.]+$/,
                                ""
                              );
                              setSearchQuery(filenameWithoutExt);
                            }}
                            disabled={file.is_tagged}
                          >
                            <Search className="h-4 w-4 mr-1" />
                            Search
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl">
                          <DialogHeader>
                            <DialogTitle>
                              Search Audible for Metadata
                            </DialogTitle>
                            <DialogDescription>
                              Search for "{file.file_path.split("/").pop()}" on
                              Audible
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4">
                            <div className="flex space-x-2">
                              <Input
                                placeholder="Enter search query..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyPress={(e) => {
                                  if (e.key === "Enter" && searchQuery.trim()) {
                                    searchAudible(file.file_path, searchQuery);
                                  }
                                }}
                              />
                              <Button
                                onClick={() =>
                                  searchAudible(file.file_path, searchQuery)
                                }
                                disabled={!searchQuery.trim() || searching}
                              >
                                {searching ? (
                                  <RefreshCw className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Search className="h-4 w-4" />
                                )}
                              </Button>
                            </div>
                            {searchResults.length > 0 && (
                              <div className="space-y-2">
                                <h4 className="font-medium">Search Results:</h4>
                                {searchResults.map((result) => (
                                  <Card key={result.asin} className="p-3">
                                    <div className="flex justify-between items-start">
                                      <div className="flex-1">
                                        <h5 className="font-medium">
                                          {result.title}
                                        </h5>
                                        <p className="text-sm text-muted-foreground">
                                          by {result.author}
                                        </p>
                                        {result.narrator && (
                                          <p className="text-sm text-muted-foreground">
                                            Narrated by {result.narrator}
                                          </p>
                                        )}
                                        {result.series && (
                                          <p className="text-sm text-muted-foreground">
                                            Series: {result.series}
                                          </p>
                                        )}
                                      </div>
                                      <Button
                                        size="sm"
                                        onClick={() =>
                                          applyMetadata(
                                            file.file_path,
                                            result.asin
                                          )
                                        }
                                      >
                                        Apply
                                      </Button>
                                    </div>
                                  </Card>
                                ))}
                              </div>
                            )}
                          </div>
                        </DialogContent>
                      </Dialog>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => startTaggingJob(file.id)}
                        disabled={file.is_tagged}
                      >
                        <Tag className="h-4 w-4 mr-1" />
                        Auto Tag
                      </Button>
                    </div>
                  </div>
                ))}
                {untaggedFiles.length > 5 && (
                  <p className="text-sm text-muted-foreground text-center">
                    ... and {untaggedFiles.length - 5} more files
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      {/* Active Jobs */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Active Jobs</CardTitle>
          <CardDescription>
            Monitor active and completed conversion and tagging jobs
          </CardDescription>
        </CardHeader>
        <CardContent>
          {jobsLoading || taggingJobsLoading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin" />
              <span className="ml-2">Loading jobs...</span>
            </div>
          ) : jobs.length === 0 && taggingJobs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Play className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No active jobs</p>
              <p className="text-sm">
                Start a conversion or tagging job to see them here
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Conversion Jobs */}
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
                    <p className="text-sm font-medium mb-2">Source Folders:</p>
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

              {/* Tagging Jobs */}
              {taggingJobs.map((job) => (
                <div key={job.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <h3 className="font-medium">
                        {job.file_path.split("/").pop()}
                      </h3>
                      {getStatusBadge(job.status)}
                      <Badge variant="outline" className="text-xs">
                        Tagging
                      </Badge>
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
                    <p className="text-sm font-medium mb-2">File Path:</p>
                    <p className="text-sm text-muted-foreground truncate">
                      {job.file_path}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}
