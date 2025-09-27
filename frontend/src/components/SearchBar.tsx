import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Search } from "lucide-react";
import {
  getCachedCities,
  getCachedRoutes,
} from "@/features/reference/referenceApi";
import type { City, Route } from "@/lib/types";

interface FlightSearchBarProps {
  onSearch: (params: {
    origin: string;
    destination: string;
    date?: string;
  }) => void;
  loading?: boolean;
}

interface HotelSearchBarProps {
  onSearch: (params: {
    city: string;
    checkIn?: string;
    checkOut?: string;
  }) => void;
  loading?: boolean;
}

export function FlightSearchBar({ onSearch, loading }: FlightSearchBarProps) {
  const [cities, setCities] = useState<City[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [date, setDate] = useState("");
  const [availableDestinations, setAvailableDestinations] = useState<string[]>(
    []
  );

  useEffect(() => {
    const loadData = async () => {
      try {
        const [citiesRes, routesRes] = await Promise.all([
          getCachedCities(),
          getCachedRoutes(),
        ]);
        setCities(citiesRes.cities);
        setRoutes(routesRes.routes);
      } catch (error) {
        console.error("Failed to load reference data:", error);
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    if (origin && routes.length > 0) {
      const destinations = routes
        .filter((route) => route.origin === origin)
        .map((route) => route.destination);
      setAvailableDestinations(destinations);

      // Reset destination if it's not available from the selected origin
      if (destination && !destinations.includes(destination)) {
        setDestination("");
      }
    } else {
      setAvailableDestinations([]);
    }
  }, [origin, routes, destination]);

  const handleSearch = () => {
    if (origin && destination) {
      onSearch({ origin, destination, date: date || undefined });
    }
  };

  const originCities = cities.filter((city) =>
    routes.some((route) => route.origin === city.airportCode)
  );

  const destinationCities = cities.filter((city) =>
    availableDestinations.includes(city.airportCode)
  );

  return (
    <div className="space-y-4 p-6 bg-card rounded-lg border">
      <h3 className="text-lg font-semibold">Search Flights</h3>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="space-y-2">
          <Label htmlFor="origin">From</Label>
          <Select value={origin} onValueChange={setOrigin}>
            <SelectTrigger>
              <SelectValue placeholder="Select origin" />
            </SelectTrigger>
            <SelectContent>
              {originCities.map((city) => (
                <SelectItem key={city._id} value={city.airportCode}>
                  {city.name} ({city.airportCode})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="destination">To</Label>
          <Select
            value={destination}
            onValueChange={setDestination}
            disabled={!origin}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select destination" />
            </SelectTrigger>
            <SelectContent>
              {destinationCities.map((city) => (
                <SelectItem key={city._id} value={city.airportCode}>
                  {city.name} ({city.airportCode})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="date">Date (Optional)</Label>
          <Input
            id="date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>

        <div className="flex items-end">
          <Button
            onClick={handleSearch}
            disabled={!origin || !destination || loading}
            className="w-full"
          >
            <Search className="mr-2 h-4 w-4" />
            {loading ? "Searching..." : "Search"}
          </Button>
        </div>
      </div>
    </div>
  );
}

export function HotelSearchBar({ onSearch, loading }: HotelSearchBarProps) {
  const [cities, setCities] = useState<City[]>([]);
  const [city, setCity] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");

  useEffect(() => {
    const loadCities = async () => {
      try {
        const citiesRes = await getCachedCities();
        setCities(citiesRes.cities);
      } catch (error) {
        console.error("Failed to load cities:", error);
      }
    };
    loadCities();
  }, []);

  const handleSearch = () => {
    if (city) {
      onSearch({
        city,
        checkIn: checkIn || undefined,
        checkOut: checkOut || undefined,
      });
    }
  };

  return (
    <div className="space-y-4 p-6 bg-card rounded-lg border">
      <h3 className="text-lg font-semibold">Search Hotels</h3>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="space-y-2">
          <Label htmlFor="city">City</Label>
          <Select value={city} onValueChange={setCity}>
            <SelectTrigger>
              <SelectValue placeholder="Select city" />
            </SelectTrigger>
            <SelectContent>
              {cities.map((cityItem) => (
                <SelectItem key={cityItem._id} value={cityItem.name}>
                  {cityItem.name}, {cityItem.country}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="checkin">Check-in (Optional)</Label>
          <Input
            id="checkin"
            type="date"
            value={checkIn}
            onChange={(e) => setCheckIn(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="checkout">Check-out (Optional)</Label>
          <Input
            id="checkout"
            type="date"
            value={checkOut}
            onChange={(e) => setCheckOut(e.target.value)}
            min={checkIn}
          />
        </div>

        <div className="flex items-end">
          <Button
            onClick={handleSearch}
            disabled={!city || loading}
            className="w-full"
          >
            <Search className="mr-2 h-4 w-4" />
            {loading ? "Searching..." : "Search"}
          </Button>
        </div>
      </div>
    </div>
  );
}
