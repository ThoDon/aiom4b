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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  CheckCircle,
  Clock,
  Download,
  RefreshCw,
  Search,
  Tag,
  Trash2,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

interface TaggedFile {
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

interface AudibleSearchResult {
  title: string;
  author: string;
  narrator?: string;
  series?: string;
  asin: string;
  locale: string;
}

interface TaggingJob {
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

export default function TaggingPage() {
  const [files, setFiles] = useState<TaggedFile[]>([]);
  const [taggingJobs, setTaggingJobs] = useState<TaggingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<AudibleSearchResult[]>([]);
  const [selectedFile, setSelectedFile] = useState<TaggedFile | null>(null);
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [searching, setSearching] = useState(false);

  // Fetch untagged files
  const fetchFiles = async () => {
    try {
      const response = await fetch("/api/v1/files/untagged");
      if (response.ok) {
        const data = await response.json();
        setFiles(data.files || []);
      } else {
        toast.error("Failed to fetch files");
      }
    } catch (error) {
      toast.error("Error fetching files");
    } finally {
      setLoading(false);
    }
  };

  // Fetch tagging jobs
  const fetchTaggingJobs = async () => {
    try {
      const response = await fetch("/api/v1/jobs/tagging");
      if (response.ok) {
        const data = await response.json();
        setTaggingJobs(data || []);
      }
    } catch (error) {
      console.error("Error fetching tagging jobs:", error);
    }
  };

  useEffect(() => {
    fetchFiles();
    fetchTaggingJobs();
  }, []);

  // Search Audible API
  const searchAudible = async (fileId: string, query: string) => {
    setSearching(true);
    try {
      const response = await fetch(
        `/api/v1/files/${fileId}/search?query=${encodeURIComponent(query)}`,
        {
          method: "POST",
        }
      );
      if (response.ok) {
        const results = await response.json();
        setSearchResults(results);
      } else {
        toast.error("Failed to search Audible");
      }
    } catch (error) {
      toast.error("Error searching Audible");
    } finally {
      setSearching(false);
    }
  };

  // Apply metadata to file
  const applyMetadata = async (fileId: string, asin: string) => {
    try {
      const response = await fetch(
        `/api/v1/files/${fileId}/apply?asin=${asin}`,
        {
          method: "POST",
        }
      );
      if (response.ok) {
        toast.success("Metadata applied successfully");
        setSearchDialogOpen(false);
        fetchFiles(); // Refresh files list
      } else {
        toast.error("Failed to apply metadata");
      }
    } catch (error) {
      toast.error("Error applying metadata");
    }
  };

  // Start tagging job
  const startTaggingJob = async (fileId: string) => {
    try {
      const file = files.find((f) => f.id === fileId);
      if (!file) return;

      const response = await fetch("/api/v1/jobs/tagging", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          file_path: file.file_path,
        }),
      });

      if (response.ok) {
        toast.success("Tagging job started");
        fetchTaggingJobs(); // Refresh jobs list
      } else {
        toast.error("Failed to start tagging job");
      }
    } catch (error) {
      toast.error("Error starting tagging job");
    }
  };

  // Delete file
  const deleteFile = async (fileId: string) => {
    if (!confirm("Are you sure you want to delete this file?")) return;

    try {
      const response = await fetch(`/api/v1/files/${fileId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        toast.success("File deleted successfully");
        fetchFiles(); // Refresh files list
      } else {
        toast.error("Failed to delete file");
      }
    } catch (error) {
      toast.error("Error deleting file");
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "running":
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800";
      case "failed":
        return "bg-red-100 text-red-800";
      case "running":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-yellow-100 text-yellow-800";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <main className="container mx-auto px-4">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">File Tagging</h1>
            <p className="text-muted-foreground">
              Manage and tag your converted M4B files with Audible metadata
            </p>
          </div>
          <Button onClick={fetchFiles} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        <Tabs defaultValue="files" className="space-y-4">
          <TabsList>
            <TabsTrigger value="files">Untagged Files</TabsTrigger>
            <TabsTrigger value="jobs">Tagging Jobs</TabsTrigger>
          </TabsList>

          <TabsContent value="files" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Converted Files</CardTitle>
                <CardDescription>
                  Files that have been converted but not yet tagged with
                  metadata
                </CardDescription>
              </CardHeader>
              <CardContent>
                {files.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No untagged files found
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Filename</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Title</TableHead>
                        <TableHead>Author</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {files.map((file) => (
                        <TableRow key={file.id}>
                          <TableCell className="font-medium">
                            {file.file_path.split("/").pop()}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={file.is_tagged ? "default" : "secondary"}
                            >
                              {file.is_tagged ? "Tagged" : "Untagged"}
                            </Badge>
                          </TableCell>
                          <TableCell>{file.title || "Unknown"}</TableCell>
                          <TableCell>{file.author || "Unknown"}</TableCell>
                          <TableCell>
                            {new Date(file.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <div className="flex space-x-2">
                              <Dialog
                                open={
                                  searchDialogOpen &&
                                  selectedFile?.id === file.id
                                }
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
                                      // Set default search query to filename (without extension)
                                      const filename =
                                        file.file_path.split("/").pop() || "";
                                      const filenameWithoutExt =
                                        filename.replace(/\.[^/.]+$/, "");
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
                                      Search for "
                                      {file.file_path.split("/").pop()}" on
                                      Audible
                                    </DialogDescription>
                                  </DialogHeader>
                                  <div className="space-y-4">
                                    <div className="flex space-x-2">
                                      <Input
                                        placeholder="Enter search query..."
                                        value={searchQuery}
                                        onChange={(e) =>
                                          setSearchQuery(e.target.value)
                                        }
                                        onKeyPress={(e) => {
                                          if (
                                            e.key === "Enter" &&
                                            searchQuery.trim()
                                          ) {
                                            searchAudible(file.id, searchQuery);
                                          }
                                        }}
                                      />
                                      <Button
                                        onClick={() =>
                                          searchAudible(file.id, searchQuery)
                                        }
                                        disabled={
                                          !searchQuery.trim() || searching
                                        }
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
                                        <h4 className="font-medium">
                                          Search Results:
                                        </h4>
                                        {searchResults.map((result, index) => (
                                          <Card
                                            key={result.asin}
                                            className="p-3"
                                          >
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
                                                    Narrated by{" "}
                                                    {result.narrator}
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
                                                    file.id,
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
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => deleteFile(file.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="jobs" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Tagging Jobs</CardTitle>
                <CardDescription>
                  Background jobs for tagging files with metadata
                </CardDescription>
              </CardHeader>
              <CardContent>
                {taggingJobs.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No tagging jobs found
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>File</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Progress</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Duration</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {taggingJobs.map((job) => (
                        <TableRow key={job.id}>
                          <TableCell className="font-medium">
                            {job.file_path.split("/").pop()}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              {getStatusIcon(job.status)}
                              <Badge className={getStatusColor(job.status)}>
                                {job.status}
                              </Badge>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <Progress value={job.progress} className="w-20" />
                              <span className="text-sm">{job.progress}%</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            {new Date(job.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            {job.completed_at && job.started_at
                              ? `${Math.round(
                                  (new Date(job.completed_at).getTime() -
                                    new Date(job.started_at).getTime()) /
                                    1000
                                )}s`
                              : job.started_at
                              ? `${Math.round(
                                  (Date.now() -
                                    new Date(job.started_at).getTime()) /
                                    1000
                                )}s`
                              : "-"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}
