import { useState } from "react";
import { getSummary } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import type { SummaryResp, Summary, CitySummary } from "@/types";

const SummaryView = () => {
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("");
  const [data, setData] = useState<SummaryResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoad = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await getSummary({
        city: city.trim() || undefined,
        country: country.trim() || undefined,
      });
      setData(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationVariant = (
    my_rating?: number,
  ): "default" | "secondary" | "destructive" => {
    if (!my_rating) return "destructive";
    if (my_rating > 4) return "default";
    if (my_rating > 3) return "secondary";
    return "destructive";
  };

  const getMerchants = (city: CitySummary): Summary[] => {
    return city.merchants || [];
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label htmlFor="filterCity">City</Label>
            <Input
              id="filterCity"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="Venice"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="filterCountry">Country</Label>
            <Input
              id="filterCountry"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              placeholder="USA"
            />
          </div>
        </div>

        <Button onClick={handleLoad} disabled={loading}>
          {loading ? "Loading..." : "Get Summary"}
        </Button>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>❌ {error}</AlertDescription>
          </Alert>
        )}

        {data && (
          <div>
            {/* <p className="text-sm text-muted-foreground mb-4">
              Found {data.total_reviews} reviews
            </p> */}

            {data.countries.length === 0 ? (
              <p className="text-muted-foreground">No reviews found.</p>
            ) : (
              data.countries.map((country) => (
                <div key={country.country} className="mb-6">
                  <h3 className="text-base font-semibold mb-2">
                    🌍 {country.country}
                  </h3>
                  {country.cities.map((city) => (
                    <div key={city.city} className="ml-4 mb-4">
                      <h4 className="text-sm font-medium text-muted-foreground mb-2">
                        📍 {city.city}
                      </h4>
                      {getMerchants(city).map((r, i) => {
                        const rating = r.my_rating ?? 0;
                        return (
                          <div
                            key={i}
                            className="border-l-4 border-primary bg-muted/40 rounded-r-md p-3 mb-2"
                          >
                            <div className="flex justify-between items-center mb-1">
                              <span className="font-semibold">{r.name}</span>
                              <Badge
                                variant={getRecommendationVariant(r.my_rating)}
                              >
                                {`★ ${rating}`}
                              </Badge>
                            </div>
                            <div className="text-sm text-muted-foreground mb-2">
                              {r.address && <span>{r.address} · </span>}
                              {r.google_rating && (
                                <span>Google: {r.google_rating}⭐ · </span>
                              )}
                              {r.cost_total && (
                                <span>
                                  Spent: {r.currency} {r.cost_total}
                                </span>
                              )}
                            </div>
                            {r.dishes && r.dishes.length > 0 && (
                              <ul className="text-sm pl-4 list-disc">
                                {r.dishes
                                  .filter((d) => d.dish_rating)
                                  .slice(0, 3)
                                  .map((d, j) => (
                                    <li key={j}>
                                      {d.name} —{" "}
                                      {"★".repeat(d.dish_rating ?? 0)}
                                      {d.dish_note && (
                                        <span className="text-muted-foreground">
                                          {" "}
                                          ({d.dish_note})
                                        </span>
                                      )}
                                    </li>
                                  ))}
                              </ul>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              ))
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default SummaryView;
