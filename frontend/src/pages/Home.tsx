import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FlightSearchBar, HotelSearchBar } from "@/components/SearchBar";
import { Plane, Hotel, Users } from "lucide-react";

export function Home() {
  const navigate = useNavigate();
  const [flightLoading, setFlightLoading] = useState(false);
  const [hotelLoading, setHotelLoading] = useState(false);

  const handleFlightSearch = async (params: {
    origin: string;
    destination: string;
    date?: string;
  }) => {
    setFlightLoading(true);
    // Navigate to flights page with search params
    const searchParams = new URLSearchParams({
      origin: params.origin,
      destination: params.destination,
      ...(params.date && { date: params.date }),
    });
    navigate(`/flights?${searchParams.toString()}`);
    setFlightLoading(false);
  };

  const handleHotelSearch = async (params: {
    city: string;
    checkIn?: string;
    checkOut?: string;
  }) => {
    setHotelLoading(true);
    // Navigate to hotels page with search params
    const searchParams = new URLSearchParams({
      city: params.city,
      ...(params.checkIn && { checkIn: params.checkIn }),
      ...(params.checkOut && { checkOut: params.checkOut }),
    });
    navigate(`/hotels?${searchParams.toString()}`);
    setHotelLoading(false);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold tracking-tight mb-4">
          Plan Your Perfect Trip
        </h1>
        <p className="text-xl text-muted-foreground mb-8">
          Search and book flights and hotels with our AI-powered travel
          assistant
        </p>
      </div>

      <div className="max-w-4xl mx-auto mb-12">
        <Tabs defaultValue="flights" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="flights" className="flex items-center gap-2">
              <Plane className="h-4 w-4" />
              Flights
            </TabsTrigger>
            <TabsTrigger value="hotels" className="flex items-center gap-2">
              <Hotel className="h-4 w-4" />
              Hotels
            </TabsTrigger>
          </TabsList>

          <TabsContent value="flights" className="mt-6">
            <FlightSearchBar
              onSearch={handleFlightSearch}
              loading={flightLoading}
            />
          </TabsContent>

          <TabsContent value="hotels" className="mt-6">
            <HotelSearchBar
              onSearch={handleHotelSearch}
              loading={hotelLoading}
            />
          </TabsContent>
        </Tabs>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plane className="h-5 w-5" />
              Flight Booking
            </CardTitle>
            <CardDescription>
              Search and book flights from hundreds of airlines worldwide
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="text-sm space-y-2">
              <li>• Real-time flight availability</li>
              <li>• Competitive pricing</li>
              <li>• Multiple airline options</li>
              <li>• Instant booking confirmation</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Hotel className="h-5 w-5" />
              Hotel Reservations
            </CardTitle>
            <CardDescription>
              Find and book the perfect accommodation for your stay
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="text-sm space-y-2">
              <li>• Wide selection of hotels</li>
              <li>• Detailed amenity information</li>
              <li>• Flexible room options</li>
              <li>• Best rate guarantee</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              AI Travel Assistant
            </CardTitle>
            <CardDescription>
              Get personalized travel recommendations and support
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="text-sm space-y-2">
              <li>• Multi-agent assistance</li>
              <li>• Real-time chat support</li>
              <li>• Personalized recommendations</li>
              <li>• Trip planning help</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
