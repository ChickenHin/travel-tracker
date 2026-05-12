import { useState } from "react";
import type {
  ParseReceiptResp,
  Merchant,
  DishWithReview,
  StatusMessage,
} from "../types";

import { saveReview } from "@/api/client";

import StarRating from "./StarRating";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ReviewFormProps {
  parsedReceipt: ParseReceiptResp;
  onSaved: () => void;
}

const ReviewForm = ({ parsedReceipt, onSaved }: ReviewFormProps) => {
  const [merchant] = useState<Merchant>(parsedReceipt.merchant);
  const [dishes, setDishes] = useState<DishWithReview[]>(
    parsedReceipt.dishes.map((d) => ({ ...d, dish_rating: 0, dish_note: "" })),
  );
  const [myRating, setMyRating] = useState(0);
  const [myNote, setMyNote] = useState("");
  const [total, setTotal] = useState(parsedReceipt.total);
  const [currency, setCurrency] = useState(parsedReceipt.currency);
  const [visitDate, setVisitDate] = useState(
    new Date().toISOString().slice(0, 10),
  );

  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [loading, setLoading] = useState(false);

  const updateDishName = (i: number, v: string) =>
    setDishes(dishes.map((d, idx) => (idx === i ? { ...d, name: v } : d)));

  const updateDishPrice = (i: number, v: number) =>
    setDishes(dishes.map((d, idx) => (idx === i ? { ...d, price: v } : d)));

  const updateDishRating = (i: number, v: number) =>
    setDishes(
      dishes.map((d, idx) => (idx === i ? { ...d, dish_rating: v } : d)),
    );

  const updateDishNote = (i: number, v: string) =>
    setDishes(dishes.map((d, idx) => (idx === i ? { ...d, dish_note: v } : d)));

  const handleSave = async () => {
    if (!myRating) {
      setStatus({ type: "error", message: "Merchant rating cannot be empty" });
      return;
    }

    setLoading(true);
    setStatus({ type: "info", message: "Saving..." });

    try {
      const result = await saveReview({
        merchant,
        dishes,
        my_rating: myRating,
        my_note: myNote,
        total: total,
        currency,
        visit_date: visitDate,
      });
      setStatus({ type: "success", message: `✅ Saved (id: ${result.id})` });
      onSaved();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setStatus({ type: "error", message: `❌ ${message}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Review</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label htmlFor="visitDate">Visit Date</Label>
            <Input
              id="visitDate"
              type="date"
              value={visitDate}
              onChange={(e) => setVisitDate(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-1">
          <Label>My Rating</Label>
          <div>
            <StarRating value={myRating} onChange={setMyRating} />
          </div>
        </div>

        <div className="space-y-1">
          <Label htmlFor="myNote">Your Note</Label>
          <Textarea
            id="myNote"
            rows={2}
            value={myNote}
            onChange={(e) => setMyNote(e.target.value)}
          />
        </div>

        <div className="space-y-1">
          <Label>Dishes</Label>
          <div className="space-y-2">
            {dishes.map((dish, i) => (
              <div
                key={i}
                className="grid grid-cols-[2fr_1fr_auto_2fr] gap-2 items-center"
              >
                <Input
                  value={dish.name}
                  onChange={(e) => updateDishName(i, e.target.value)}
                  placeholder="Dish name"
                />
                <Input
                  type="number"
                  step="0.01"
                  value={dish.price}
                  onChange={(e) =>
                    updateDishPrice(i, parseFloat(e.target.value) || 0)
                  }
                />
                <StarRating
                  value={dish.dish_rating ?? 0}
                  onChange={(v) => updateDishRating(i, v)}
                />
                <Input
                  value={dish.dish_note ?? ""}
                  onChange={(e) => updateDishNote(i, e.target.value)}
                  placeholder="Notes"
                />
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label htmlFor="totalCost">Total Cost</Label>
            <Input
              id="totalCost"
              type="number"
              step="0.01"
              value={total}
              onChange={(e) => setTotal(parseFloat(e.target.value) || 0)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="currency">Currency</Label>
            <Input
              id="currency"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
            />
          </div>
        </div>

        <Button onClick={handleSave} disabled={loading}>
          {loading ? "Saving..." : "Save Review"}
        </Button>

        {status && (
          <Alert variant={status.type === "error" ? "destructive" : "default"}>
            <AlertDescription>{status.message}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default ReviewForm;
