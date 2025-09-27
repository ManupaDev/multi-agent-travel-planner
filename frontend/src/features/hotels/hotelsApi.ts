import { apiGet, apiPost, buildQueryParams } from "@/lib/api";
import type {
  HotelsResponse,
  HotelSearchForm,
  HotelBookingForm,
  BookingResponse,
} from "@/lib/types";

export const hotelsApi = {
  // Get all hotels
  getHotels: (): Promise<HotelsResponse> => {
    return apiGet<HotelsResponse>("/hotels");
  },

  // Search hotels
  searchHotels: (params: HotelSearchForm): Promise<HotelsResponse> => {
    const queryParams = buildQueryParams({
      city: params.city,
      checkIn: params.checkIn,
      checkOut: params.checkOut,
    });
    return apiGet<HotelsResponse>(`/hotels/search${queryParams}`);
  },

  // Book a hotel
  bookHotel: (booking: HotelBookingForm): Promise<BookingResponse> => {
    return apiPost<BookingResponse, HotelBookingForm>("/hotels/book", booking);
  },
};
