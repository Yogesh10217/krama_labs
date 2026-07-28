"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  UploadCloud, 
  File, 
  X, 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  Image as ImageIcon,
  Loader2,
  Trash2,
  Settings2,
  Sparkles
} from "lucide-react";
import { cn, formatBytes } from "@/lib/utils";
import { PageContainer, PageHeader } from "@/components/shared/page";

// Mock upload history
const uploadHistory = [
  { id: "h1", name: "Q3_Earnings_Report.pdf", size: "4.2 MB", date: "Today, 10:42 AM", status: "completed" },
  { id: "h2", name: "Contract_AcmeCorp_Signed.pdf", size: "1.8 MB", date: "Today, 09:15 AM", status: "completed" },
  { id: "h3", name: "Receipt_Scan_001.jpg", size: "3.1 MB", date: "Yesterday, 16:30 PM", status: "failed", error: "Blurry image" },
];

interface UploadFile extends File {
  id: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

export default function UploadPage() {
  const [files, setFiles] = useState<UploadFile[]>([]);
  // Track all timers so we can clean them up on unmount (prevents leaks
  // and setState-after-unmount warnings).
  const timersRef = useRef<Set<ReturnType<typeof setInterval>>>(new Set());

  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      timers.forEach((t) => {
        clearInterval(t);
        clearTimeout(t);
      });
      timers.clear();
    };
  }, []);

  const isUploading = files.some(f => f.status === 'uploading' || f.status === 'processing');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => Object.assign(file, {
      id: Math.random().toString(36).substring(7),
      progress: 0,
      status: 'uploading' as const
    }));

    setFiles(prev => [...prev, ...newFiles]);
    simulateUpload(newFiles);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({ 
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  const simulateUpload = (newFiles: UploadFile[]) => {
    newFiles.forEach(file => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
          timersRef.current.delete(interval);
          setFiles(current =>
            current.map(f => f.id === file.id ? { ...f, progress, status: 'processing' } : f)
          );

          // Simulate processing time
          const timeout = setTimeout(() => {
            timersRef.current.delete(timeout);
            setFiles(current =>
              current.map(f => f.id === file.id ? { ...f, status: 'completed' } : f)
            );
          }, 2000 + Math.random() * 2000);
          timersRef.current.add(timeout);
        } else {
          setFiles(current =>
            current.map(f => f.id === file.id ? { ...f, progress } : f)
          );
        }
      }, 300);
      timersRef.current.add(interval);
    });
  };

  const removeFile = (id: string) => {
    setFiles(current => current.filter(f => f.id !== id));
  };

  const getFileIcon = (type: string) => {
    if (type.includes('image')) return <ImageIcon className="w-8 h-8 text-blue-500" />;
    if (type.includes('pdf')) return <FileText className="w-8 h-8 text-red-500" />;
    return <File className="w-8 h-8 text-primary" />;
  };

  return (
    <PageContainer size="wide">
      <PageHeader title="Upload Documents" description="Add files to the processing queue for AI extraction.">
        <Button variant="outline" className="gap-2">
          <Settings2 className="w-4 h-4" aria-hidden="true" /> Extraction Settings
        </Button>
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Dropzone */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
          >
          <div
            {...getRootProps()}
            className={cn(
              "relative group overflow-hidden rounded-3xl glass gradient-border p-12 transition-all duration-500 ease-out flex flex-col items-center justify-center text-center cursor-pointer min-h-[320px] lift",
              isDragActive && "ai-glow-md scale-[1.01]",
              isDragReject && "border-destructive"
            )}
          >
            {/* Hover aura */}
            <div
              className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"
              style={{
                background:
                  "radial-gradient(600px circle at 50% 50%, hsl(262 90% 65% / 0.08), transparent 60%)",
              }}
              aria-hidden="true"
            />
              <input {...getInputProps()} />
              
              <div className={cn(
                "p-4 rounded-full mb-4 transition-transform duration-300",
                isDragActive ? "bg-primary text-primary-foreground scale-110" : "bg-secondary text-muted-foreground group-hover:scale-110 group-hover:bg-primary/10 group-hover:text-primary"
              )}>
                <UploadCloud className="w-8 h-8" />
              </div>
              
              <h3 className="text-xl font-semibold mb-2">
                {isDragActive ? "Drop files here..." : "Click or drag files to upload"}
              </h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Supported formats: PDF, DOCX, JPG, PNG. Maximum file size: 50MB.
                Batches up to 100 files supported.
              </p>
            </div>
          </motion.div>

          {/* Upload Queue */}
          <AnimatePresence>
            {files.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
              >
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between pb-4 border-b">
                    <div>
                      <CardTitle className="text-lg">Processing Queue</CardTitle>
                      <CardDescription>
                        {files.filter(f => f.status === 'completed').length} of {files.length} files processed
                      </CardDescription>
                    </div>
                    {files.length > 0 && !isUploading && (
                      <Button variant="ghost" size="sm" onClick={() => setFiles([])}>
                        Clear All
                      </Button>
                    )}
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="divide-y max-h-[400px] overflow-y-auto custom-scrollbar">
                      <AnimatePresence>
                        {files.map((file) => (
                          <motion.div
                            key={file.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="p-4 flex items-center gap-4 hover:bg-muted/30 transition-colors"
                          >
                            <div className="p-2 bg-secondary rounded-lg shrink-0">
                              {getFileIcon(file.type)}
                            </div>
                            
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between mb-1">
                                <p className="text-sm font-medium truncate pr-4">{file.name}</p>
                                <span className="text-xs text-muted-foreground whitespace-nowrap">
                                  {formatBytes(file.size)}
                                </span>
                              </div>
                              
                              <div className="flex items-center gap-3">
                                <div className="flex-1">
                                  <Progress 
                                    value={file.progress} 
                                    className={cn(
                                      "h-1.5", 
                                      file.status === 'error' ? "[&>div]:bg-destructive" :
                                      file.status === 'completed' ? "[&>div]:bg-green-500" : ""
                                    )} 
                                  />
                                </div>
                                <span className="text-xs font-medium w-8 text-right shrink-0">
                                  {Math.round(file.progress)}%
                                </span>
                              </div>
                              
                              <div className="flex items-center gap-2 mt-2">
                                {file.status === 'uploading' && (
                                  <Badge variant="secondary" className="text-[10px] uppercase gap-1"><Loader2 className="w-3 h-3 animate-spin" /> Uploading</Badge>
                                )}
                                {file.status === 'processing' && (
                                  <Badge variant="warning" className="text-[10px] uppercase gap-1"><Sparkles className="w-3 h-3 animate-pulse" /> Extracting AI</Badge>
                                )}
                                {file.status === 'completed' && (
                                  <Badge variant="success" className="text-[10px] uppercase gap-1"><CheckCircle2 className="w-3 h-3" /> Ready</Badge>
                                )}
                                {file.status === 'error' && (
                                  <Badge variant="destructive" className="text-[10px] uppercase gap-1"><AlertCircle className="w-3 h-3" /> Failed</Badge>
                                )}
                              </div>
                            </div>

                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="shrink-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                              onClick={() => removeFile(file.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </motion.div>
                        ))}
                      </AnimatePresence>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Sidebar */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-6"
        >
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Upload History</CardTitle>
              <CardDescription>Recent file submissions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {uploadHistory.map((item) => (
                <div key={item.id} className="flex gap-3">
                  <div className="mt-0.5 shrink-0">
                    {item.status === 'completed' ? (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-destructive" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{item.name}</p>
                    <div className="flex items-center text-xs text-muted-foreground mt-1 gap-2">
                      <span>{item.size}</span>
                      <span>•</span>
                      <span>{item.date}</span>
                    </div>
                    {item.error && (
                      <p className="text-xs text-destructive mt-1">{item.error}</p>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </PageContainer>
  );
}
