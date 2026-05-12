import { useState } from "react";
import ReceiptUpload from "@/components/ReceiptUpload";
import ReviewForm from "@/components/ReviewForm";
import Summary from "@/components/Summary";
import type { ParseReceiptResp } from "@/types";
import "./App.css";

const App = () => {
  const [parsedReceipt, setParsedReceipt] = useState<ParseReceiptResp | null>(
    null,
  );

  const handleSaved = () => {
    setParsedReceipt(null);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">🍽️ Restaurant Tracker</h1>
      <p className="text-muted-foreground mb-8">
        Upload a receipt, rate it, and get recommendations.
      </p>

      <ReceiptUpload onParsed={setParsedReceipt} />

      {parsedReceipt && (
        <ReviewForm parsedReceipt={parsedReceipt} onSaved={handleSaved} />
      )}

      <Summary />
    </div>
  );
};

export default App;
