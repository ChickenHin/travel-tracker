import { useState } from "react";

interface StarRatingProps {
  value: number;
  onChange: (rating: number) => void;
}

const StarRating = ({ value, onChange }: StarRatingProps) => {
  const [hovered, setHovered] = useState(0);
  const displayValue = hovered || value;

  return (
    <div
      className="inline-flex gap-0.5 cursor-pointer"
      onMouseLeave={() => setHovered(0)}
    >
      {[1, 2, 3, 4, 5].map((n) => (
        <span
          key={n}
          className={`text-2xl transition-colors select-none ${
            n <= displayValue ? "text-yellow-400" : "text-gray-300"
          } hover:text-yellow-400`}
          onMouseEnter={() => setHovered(n)}
          onClick={() => onChange(n)}
        >
          ★
        </span>
      ))}
    </div>
  );
};

export default StarRating;
