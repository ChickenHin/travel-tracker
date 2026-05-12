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

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Restaurant Tracker</h1>
        <p className="text-muted-foreground">
          Upload a receipt, rate it, and get friend-ready recommendations.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <ReceiptUpload onParsed={setParsedReceipt} />
          {parsedReceipt && <ReviewForm parsedReceipt={parsedReceipt} />}
        </div>

        <div>
          <Summary />
        </div>
      </div>
    </div>
  );
};

export default App;
