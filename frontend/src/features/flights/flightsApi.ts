import { apiGet, apiPost, buildQueryParams } from "@/lib/api";
import type {
  FlightsResponse,
  FlightSearchForm,
  FlightBookingForm,
  BookingResponse,
} from "@/lib/types";

export const flightsApi = {
  // Get all flights
  getFlights: (): Promise<FlightsResponse> => {
    return apiGet<FlightsResponse>("/flights");
  },

  // Search flights
  searchFlights: (params: FlightSearchForm): Promise<FlightsResponse> => {
    const queryParams = buildQueryParams({
      origin: params.origin,
      destination: params.destination,
      date: params.date,
    });
    return apiGet<FlightsResponse>(`/flights/search${queryParams}`);
  },

  // Book a flight
  bookFlight: (booking: FlightBookingForm): Promise<BookingResponse> => {
    return apiPost<BookingResponse, FlightBookingForm>(
      "/flights/book",
      booking
    );
  },
};
