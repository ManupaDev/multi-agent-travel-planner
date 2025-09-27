import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { FlightSearchBar } from "@/components/SearchBar";
import { FlightCard } from "@/components/FlightCard";
import { useToast } from "@/components/ui/use-toast";
import { flightsApi } from "./flightsApi";
import type { Flight } from "@/lib/types";

export function FlightsPage() {
  const [flights, setFlights] = useState<Flight[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();

  // Initial load or search from URL params
  useEffect(() => {
    const origin = searchParams.get("origin");
    const destination = searchParams.get("destination");
    const date = searchParams.get("date");

    if (origin && destination) {
      handleSearch({ origin, destination, date: date || undefined });
    } else {
      loadAllFlights();
    }
  }, []);

  const loadAllFlights = async () => {
    setLoading(true);
    try {
      const response = await flightsApi.getFlights();
      setFlights(response.flights);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load flights. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (params: {
    origin: string;
    destination: string;
    date?: string;
  }) => {
    setLoading(true);
    try {
      const response = await flightsApi.searchFlights(params);
      setFlights(response.flights);

      // Update URL params
      const newSearchParams = new URLSearchParams({
        origin: params.origin,
        destination: params.destination,
        ...(params.date && { date: params.date }),
      });
      setSearchParams(newSearchParams);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to search flights. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleBookFlight = async (bookingData: any) => {
    try {
      const response = await flightsApi.bookFlight(bookingData);
      if (response.success) {
        toast({
          title: "Booking Successful!",
          description: `Your flight has been booked. Reference: ${response.booking.bookingReference}`,
        });
        // Refresh flights to update available seats
        const origin = searchParams.get("origin");
        const destination = searchParams.get("destination");
        const date = searchParams.get("date");
        if (origin && destination) {
          handleSearch({ origin, destination, date: date || undefined });
        } else {
          loadAllFlights();
        }
      }
    } catch (error) {
      toast({
        title: "Booking Failed",
        description: "Failed to book flight. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4">Find Flights</h1>
        <FlightSearchBar onSearch={handleSearch} loading={loading} />
      </div>

      <div className="space-y-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="text-lg">Searching flights...</div>
            <div className="text-muted-foreground">
              Please wait while we find the best options for you.
            </div>
          </div>
        ) : flights.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-lg mb-2">No flights found</div>
            <div className="text-muted-foreground">
              Try adjusting your search criteria.
            </div>
          </div>
        ) : (
          <>
            <div className="text-sm text-muted-foreground">
              Found {flights.length} flight{flights.length !== 1 ? "s" : ""}
            </div>
            <div className="grid gap-6">
              {flights.map((flight) => (
                <FlightCard
                  key={flight._id}
                  flight={flight}
                  onBook={handleBookFlight}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
