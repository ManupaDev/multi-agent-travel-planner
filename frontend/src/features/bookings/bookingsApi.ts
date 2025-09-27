import { apiGet, buildQueryParams } from "@/lib/api";
import type {
  FlightBookingsResponse,
  HotelBookingsResponse,
  UserBookings,
} from "@/lib/types";

export const bookingsApi = {
  // Get all flight bookings
  getFlightBookings: (): Promise<FlightBookingsResponse> => {
    return apiGet<FlightBookingsResponse>("/bookings/flights");
  },

  // Get all hotel bookings
  getHotelBookings: (): Promise<HotelBookingsResponse> => {
    return apiGet<HotelBookingsResponse>("/bookings/hotels");
  },

  // Get bookings for a specific user
  getUserBookings: (email: string): Promise<UserBookings> => {
    const queryParams = buildQueryParams({ email });
    return apiGet<UserBookings>(`/bookings/user${queryParams}`);
  },
};
