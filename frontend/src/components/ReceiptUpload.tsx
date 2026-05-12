import { useState } from "react";
import type { ChangeEvent } from "react";
import { parseReceipt } from "../api/client";
import type { ParseReceiptResp } from "../types";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ReceiptUploadProps {
  onParsed: (data: ParseReceiptResp) => void;
}

const ReceiptUpload = ({ onParsed }: ReceiptUploadProps) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    setFile(selected || null);
    setError(null);
  };

  const handleParse = async () => {
    if (!file) {
      setError("Please select a file");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const data = await parseReceipt(file);
      onParsed(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Upload Receipt</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Input
          type="file"
          accept="image/*,application/pdf"
          onChange={handleFileChange}
        />

        <Button onClick={handleParse} disabled={loading || !file}>
          {loading ? "Parsing..." : "Parse Receipt"}
        </Button>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>❌ {error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default ReceiptUpload;
