import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { HotelSearchBar } from "@/components/SearchBar";
import { HotelCard } from "@/components/HotelCard";
import { useToast } from "@/components/ui/use-toast";
import { hotelsApi } from "./hotelsApi";
import type { Hotel } from "@/lib/types";

export function HotelsPage() {
  const [hotels, setHotels] = useState<Hotel[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();

  // Initial load or search from URL params
  useEffect(() => {
    const city = searchParams.get("city");
    const checkIn = searchParams.get("checkIn");
    const checkOut = searchParams.get("checkOut");

    if (city) {
      handleSearch({
        city,
        checkIn: checkIn || undefined,
        checkOut: checkOut || undefined,
      });
    } else {
      loadAllHotels();
    }
  }, []);

  const loadAllHotels = async () => {
    setLoading(true);
    try {
      const response = await hotelsApi.getHotels();
      setHotels(response.hotels);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load hotels. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (params: {
    city: string;
    checkIn?: string;
    checkOut?: string;
  }) => {
    setLoading(true);
    try {
      const response = await hotelsApi.searchHotels(params);
      setHotels(response.hotels);

      // Update URL params
      const newSearchParams = new URLSearchParams({
        city: params.city,
        ...(params.checkIn && { checkIn: params.checkIn }),
        ...(params.checkOut && { checkOut: params.checkOut }),
      });
      setSearchParams(newSearchParams);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to search hotels. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleBookHotel = async (bookingData: any) => {
    try {
      const response = await hotelsApi.bookHotel(bookingData);
      if (response.success) {
        toast({
          title: "Booking Successful!",
          description: `Your hotel has been booked. Reference: ${response.booking.bookingReference}`,
        });
        // Refresh hotels to update available rooms
        const city = searchParams.get("city");
        const checkIn = searchParams.get("checkIn");
        const checkOut = searchParams.get("checkOut");
        if (city) {
          handleSearch({
            city,
            checkIn: checkIn || undefined,
            checkOut: checkOut || undefined,
          });
        } else {
          loadAllHotels();
        }
      }
    } catch (error) {
      toast({
        title: "Booking Failed",
        description: "Failed to book hotel. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4">Find Hotels</h1>
        <HotelSearchBar onSearch={handleSearch} loading={loading} />
      </div>

      <div className="space-y-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="text-lg">Searching hotels...</div>
            <div className="text-muted-foreground">
              Please wait while we find the best options for you.
            </div>
          </div>
        ) : hotels.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-lg mb-2">No hotels found</div>
            <div className="text-muted-foreground">
              Try adjusting your search criteria.
            </div>
          </div>
        ) : (
          <>
            <div className="text-sm text-muted-foreground">
              Found {hotels.length} hotel{hotels.length !== 1 ? "s" : ""}
            </div>
            <div className="grid gap-6">
              {hotels.map((hotel) => (
                <HotelCard
                  key={hotel._id}
                  hotel={hotel}
                  onBook={handleBookHotel}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
