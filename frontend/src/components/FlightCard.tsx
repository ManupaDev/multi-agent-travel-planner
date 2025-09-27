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
import { Plane, Clock, Users } from "lucide-react";
import type { Flight } from "@/lib/types";
import { BookingForm } from "./BookingForm";

interface FlightCardProps {
  flight: Flight;
  onBook?: (bookingData: any) => void;
}

export function FlightCard({ flight, onBook }: FlightCardProps) {
  const [showBookingForm, setShowBookingForm] = useState(false);

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const getDestinationInfo = () => {
    if (typeof flight.destination === "string") {
      return flight.destination;
    }
    return `${flight.destination.city} (${flight.destination.airport})`;
  };

  const getOriginInfo = () => {
    if (typeof flight.origin === "string") {
      return flight.origin;
    }
    return `${flight.origin.city} (${flight.origin.airport})`;
  };

  return (
    <>
      <Card className="w-full">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Plane className="h-5 w-5" />
                {flight.airline} {flight.flightNumber}
              </CardTitle>
              <CardDescription>
                {flight.aircraft} • {flight.flightDate}
              </CardDescription>
            </div>
            <Badge variant="secondary">{flight.availableSeats} seats</Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="text-center">
              <p className="font-semibold text-lg">{flight.departureTime}</p>
              <p className="text-sm text-muted-foreground">{getOriginInfo()}</p>
            </div>

            <div className="flex-1 flex flex-col items-center px-4">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span className="text-sm">
                  {formatDuration(flight.duration)}
                </span>
              </div>
              <div className="w-full h-px bg-border mt-2" />
            </div>

            <div className="text-center">
              <p className="font-semibold text-lg">{flight.arrivalTime}</p>
              <p className="text-sm text-muted-foreground">
                {getDestinationInfo()}
              </p>
            </div>
          </div>

          <div className="flex justify-between items-center pt-2 border-t">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {flight.availableSeats} available
              </span>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">
                {flight.currency} {flight.price}
              </p>
              <p className="text-sm text-muted-foreground">per person</p>
            </div>
          </div>
        </CardContent>

        <CardFooter>
          <Button
            className="w-full"
            onClick={() => setShowBookingForm(true)}
            disabled={flight.availableSeats === 0}
          >
            {flight.availableSeats === 0 ? "Sold Out" : "Book Flight"}
          </Button>
        </CardFooter>
      </Card>

      <BookingForm
        type="flight"
        data={flight}
        open={showBookingForm}
        onOpenChange={setShowBookingForm}
        onSubmit={onBook}
      />
    </>
  );
}
