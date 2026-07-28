"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Search, Filter, Upload, MoreHorizontal, FileText, Download, Trash2, Eye } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/shared/states";
import { PageContainer, PageHeader } from "@/components/shared/page";
import { StatusBadge } from "@/components/shared/status-badge";

const documents = [
  { id: "DOC-8921", name: "Commercial_Invoice_INV-8921.pdf", type: "PDF", size: "2.4 MB", status: "extracted", date: "Oct 24, 2024" },
  { id: "DOC-8920", name: "Health_Insurance_Claim_CLM-8920.pdf", type: "PDF", size: "1.8 MB", status: "processing", date: "Oct 24, 2024" },
  { id: "DOC-8919", name: "Master_Service_Agreement_MSA-8919.docx", type: "DOCX", size: "5.7 MB", status: "extracted", date: "Oct 23, 2024" },
  { id: "DOC-8918", name: "Bill_of_Lading_BOL-8918.jpg", type: "IMAGE", size: "850 KB", status: "failed", date: "Oct 23, 2024" },
  { id: "DOC-8917", name: "Purchase_Order_PO-8917.pdf", type: "PDF", size: "3.2 MB", status: "extracted", date: "Oct 22, 2024" },
  { id: "DOC-8916", name: "W2_Tax_Form_2024.pdf", type: "PDF", size: "1.5 MB", status: "extracted", date: "Oct 21, 2024" },
];

export default function DocumentsPage() {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredDocs = documents.filter(doc => 
    doc.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <PageContainer className="h-full flex flex-col">
      <PageHeader title="Documents" description="Manage and extract data from your enterprise documents.">
          <Button variant="outline" className="gap-2">
            <Filter className="w-4 h-4" aria-hidden="true" />
            Filters
          </Button>
          <Dialog>
            <DialogTrigger asChild>
              <Button className="gap-2 shadow-lg shadow-primary/20">
                <Upload className="w-4 h-4" />
                Upload Files
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Upload Documents</DialogTitle>
                <DialogDescription>
                  Drag and drop your enterprise documents here for AI extraction.
                </DialogDescription>
              </DialogHeader>
              <div className="mt-4 border-2 border-dashed border-muted-foreground/25 rounded-lg p-10 flex flex-col items-center justify-center text-center hover:bg-muted/10 transition-colors cursor-pointer group">
                <div className="p-3 bg-secondary rounded-full mb-4 group-hover:scale-110 transition-transform">
                  <Upload className="w-6 h-6 text-muted-foreground" />
                </div>
                <p className="font-medium">Click or drag files to upload</p>
                <p className="text-xs text-muted-foreground mt-1">PDF, DOCX, JPG, PNG (max 50MB)</p>
              </div>
              <DialogFooter className="mt-6">
                <DialogClose asChild>
                  <Button variant="outline">Cancel</Button>
                </DialogClose>
                <Button>Process Files</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
      </PageHeader>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass lift rounded-xl flex-1 flex flex-col overflow-hidden"
      >
        <div className="p-4 border-b bg-muted/20 flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input 
              placeholder="Search documents by name or ID..." 
              className="pl-9 bg-background"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="flex-1 overflow-auto">
          <Table>
            <TableHeader className="bg-muted/50 sticky top-0 backdrop-blur-sm">
              <TableRow>
                <TableHead className="w-[400px]">Document</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date Added</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDocs.map((doc, i) => (
                <TableRow key={doc.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-primary/10 text-primary flex items-center justify-center shrink-0">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="overflow-hidden">
                        <p className="font-medium truncate text-sm">{doc.name}</p>
                        <p className="text-xs text-muted-foreground">{doc.id}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-xs font-mono bg-secondary px-2 py-1 rounded text-secondary-foreground">
                      {doc.type}
                    </span>
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">{doc.size}</TableCell>
                  <TableCell>
                    <StatusBadge status={doc.status} />
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">{doc.date}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-48">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem className="gap-2 cursor-pointer">
                          <Eye className="w-4 h-4" /> View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem className="gap-2 cursor-pointer">
                          <Download className="w-4 h-4" /> Download Original
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="gap-2 text-destructive focus:text-destructive cursor-pointer">
                          <Trash2 className="w-4 h-4" /> Delete Document
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
              {filteredDocs.length === 0 && (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={6}>
                    <EmptyState
                      icon={Search}
                      title="No documents found"
                      description={`Nothing matches "${searchTerm}". Try a different name or document ID.`}
                      action={{ label: "Clear search", onClick: () => setSearchTerm("") }}
                    />
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </motion.div>
    </PageContainer>
  );
}
