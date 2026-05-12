export interface Merchant {
  name: string;
  city: string;
  country: string;
  address: string | null;
  place_id: string | null;
  google_rating: number | null;
  google_rating_count: number | null;
}

export interface Dish {
  name: string;
  price: number;
}

export interface DishWithReview extends Dish {
  dish_rating: number | null;
  dish_note: string | null;
}

export interface ParseReceiptResp {
  merchant: Merchant;
  dishes: Dish[];
  total: number;
  currency: string;
}

export interface ReviewReq {
  merchant: Merchant;
  dishes: DishWithReview[];
  my_rating: number;
  my_note: string | null;
  total: number;
  currency: string;
  visit_date: string | null;
  participant_count: number;
}

export interface ReviewResp {
  status: string;
  id: string;
}

export interface Summary {
  name: string;
  city: string;
  country: string;
  address: string | null;
  place_id: string | null;
  google_rating: number | null;
  google_rating_count: number | null;
  dishes: DishWithReview[];
  my_rating: number;
  my_note: string | null;
  cost_total: number;
  cost_per_person: number | null;
  currency: string;
  visit_count: number;
  latest_visit_date: string | null;
}

export interface CitySummary {
  city: string;
  merchants: Summary[];
}

export interface CountrySummary {
  country: string;
  cities: CitySummary[];
}

export interface SummaryFiltersQuery {
  country?: string;
  city?: string;
  from?: string;
  to?: string;
}
export interface SummaryResp {
  countries: CountrySummary[];
  total_reviews: number;
  filters: {
    country: string | null;
    city: string | null;
    from: string | null;
    to: string | null;
  };
}

export type StatusType = "success" | "error" | "info";

export interface StatusMessage {
  type: StatusType;
  message: string;
}
