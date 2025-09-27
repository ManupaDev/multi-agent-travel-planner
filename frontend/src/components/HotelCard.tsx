import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MapPin, Star, Wifi, Car, Utensils } from "lucide-react";
import type { Hotel } from "@/lib/types";
import { BookingForm } from "./BookingForm";

interface HotelCardProps {
  hotel: Hotel;
  onBook?: (bookingData: any) => void;
}

export function HotelCard({ hotel, onBook }: HotelCardProps) {
  const [showBookingForm, setShowBookingForm] = useState(false);

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`h-4 w-4 ${
          i < rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
        }`}
      />
    ));
  };

  const getAmenityIcon = (amenity: string) => {
    const amenityLower = amenity.toLowerCase();
    if (amenityLower.includes("wifi")) return <Wifi className="h-4 w-4" />;
    if (amenityLower.includes("parking") || amenityLower.includes("car"))
      return <Car className="h-4 w-4" />;
    if (amenityLower.includes("restaurant") || amenityLower.includes("dining"))
      return <Utensils className="h-4 w-4" />;
    return null;
  };

  return (
    <>
      <Card className="w-full">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="flex items-center gap-2">
                {hotel.name}
              </CardTitle>
              <CardDescription className="flex items-center gap-2 mt-1">
                <MapPin className="h-4 w-4" />
                {hotel.city}, {hotel.country}
              </CardDescription>
              <div className="flex items-center gap-1 mt-2">
                {renderStars(hotel.starRating)}
                <span className="text-sm text-muted-foreground ml-1">
                  ({hotel.starRating} star)
                </span>
              </div>
            </div>
            <Badge variant="secondary">{hotel.availableRooms} rooms</Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {hotel.description && (
            <p className="text-sm text-muted-foreground">{hotel.description}</p>
          )}

          <div className="space-y-2">
            <h4 className="font-medium text-sm">Amenities</h4>
            <div className="flex flex-wrap gap-2">
              {hotel.amenities.slice(0, 6).map((amenity, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  <span className="flex items-center gap-1">
                    {getAmenityIcon(amenity)}
                    {amenity}
                  </span>
                </Badge>
              ))}
              {hotel.amenities.length > 6 && (
                <Badge variant="outline" className="text-xs">
                  +{hotel.amenities.length - 6} more
                </Badge>
              )}
            </div>
          </div>

          <div className="flex justify-between items-center pt-2 border-t">
            <div>
              <span className="text-sm text-muted-foreground">
                {hotel.availableRooms} rooms available
              </span>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">
                {hotel.currency} {hotel.pricePerNight}
              </p>
              <p className="text-sm text-muted-foreground">per night</p>
            </div>
          </div>
        </CardContent>

        <CardFooter>
          <Button
            className="w-full"
            onClick={() => setShowBookingForm(true)}
            disabled={hotel.availableRooms === 0}
          >
            {hotel.availableRooms === 0 ? "No Rooms Available" : "Book Hotel"}
          </Button>
        </CardFooter>
      </Card>

      <BookingForm
        type="hotel"
        data={hotel}
        open={showBookingForm}
        onOpenChange={setShowBookingForm}
        onSubmit={onBook}
      />
    </>
  );
}
