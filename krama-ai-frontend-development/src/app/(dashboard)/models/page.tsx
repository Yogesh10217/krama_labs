"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BrainCircuit, Zap, CheckCircle2, Lock } from "lucide-react";

const models = [
  {
    id: "krama-extract-v2",
    name: "Krama Extract v2",
    description: "Our most advanced general-purpose document extraction model. High accuracy on unstructured data.",
    type: "Foundational",
    status: "active",
    latency: "~450ms",
    context: "128k",
  },
  {
    id: "krama-invoice-pro",
    name: "Invoice & Receipt Pro",
    description: "Specialized model fine-tuned specifically for financial documents, invoices, and receipts.",
    type: "Fine-tuned",
    status: "active",
    latency: "~200ms",
    context: "32k",
  },
  {
    id: "krama-legal-eagle",
    name: "Legal Contract Analyzer",
    description: "Trained on millions of legal contracts to extract clauses, entities, and obligations.",
    type: "Fine-tuned",
    status: "beta",
    latency: "~600ms",
    context: "256k",
  },
  {
    id: "acme-custom-model",
    name: "Acme Corp Custom HR Model",
    description: "Your organization's privately fine-tuned model for internal HR policies.",
    type: "Custom",
    status: "active",
    latency: "~300ms",
    context: "64k",
    private: true,
  }
];

export default function ModelsPage() {
  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Models</h1>
          <p className="text-muted-foreground mt-1">Manage foundational and fine-tuned extraction models.</p>
        </div>
        <Button className="gap-2">
          <Zap className="w-4 h-4" />
          Fine-tune Model
        </Button>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        {models.map((model, index) => (
          <motion.div
            key={model.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="h-full flex flex-col hover:border-primary/50 transition-colors relative overflow-hidden group">
              {model.private && (
                <div className="absolute top-0 right-0 p-4">
                  <Lock className="w-4 h-4 text-muted-foreground" />
                </div>
              )}
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-primary/10 text-primary rounded-lg">
                    <BrainCircuit className="w-5 h-5" />
                  </div>
                  <Badge variant={model.status === "active" ? "success" : "warning"} className="capitalize">
                    {model.status}
                  </Badge>
                  <Badge variant="outline">{model.type}</Badge>
                </div>
                <CardTitle className="text-xl">{model.name}</CardTitle>
                <CardDescription className="font-mono text-xs">{model.id}</CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <p className="text-sm text-muted-foreground mb-6">
                  {model.description}
                </p>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="bg-secondary/50 rounded-md p-3">
                    <span className="text-muted-foreground block mb-1 text-xs uppercase tracking-wider">Avg Latency</span>
                    <span className="font-medium">{model.latency}</span>
                  </div>
                  <div className="bg-secondary/50 rounded-md p-3">
                    <span className="text-muted-foreground block mb-1 text-xs uppercase tracking-wider">Context Window</span>
                    <span className="font-medium">{model.context}</span>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="border-t bg-muted/10 pt-4 flex justify-between items-center">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <CheckCircle2 className="w-4 h-4 text-green-500" /> API Available
                </div>
                <Button variant="ghost" size="sm">View Documentation</Button>
              </CardFooter>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
