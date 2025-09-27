// API Types inferred from the provided examples

export interface Country {
  _id: string;
  _creationTime: number;
  code: string;
  currency: string;
  name: string;
  region: string;
  timezone: string;
}

export interface City {
  _id: string;
  _creationTime: number;
  airportCode: string;
  country: string;
  countryCode: string;
  countryId: string;
  isCapital: boolean;
  name: string;
}

export interface Route {
  destination: string;
  origin: string;
}

export interface Flight {
  _id: string;
  _creationTime: number;
  aircraft: string;
  airline: string;
  arrivalTime: string;
  availableSeats: number;
  currency: string;
  departureTime: string;
  destination:
    | {
        airport: string;
        city: string;
        country: string;
      }
    | string;
  destinationCityId: string;
  duration: number;
  flightDate: string;
  flightNumber: string;
  origin:
    | {
        airport: string;
        city: string;
        country: string;
      }
    | string;
  originCityId: string;
  price: number;
}

export interface Hotel {
  _id: string;
  _creationTime: number;
  address: string;
  airportCode: string;
  amenities: string[];
  availableRooms: number;
  city: string;
  cityId: string;
  country: string;
  currency: string;
  description: string;
  name: string;
  pricePerNight: number;
  starRating: number;
}

export interface FlightBooking {
  _id: string;
  _creationTime: number;
  bookingDate: number;
  bookingReference: string;
  currency: string;
  flight: Flight;
  flightId: string;
  passengerEmail: string;
  passengerName: string;
  seatNumber: string;
  status: string;
  totalPrice: number;
  userId: string;
}

export interface HotelBooking {
  _id: string;
  _creationTime: number;
  bookingDate: number;
  bookingReference: string;
  checkInDate: string;
  checkOutDate: string;
  currency: string;
  guestEmail: string;
  guestName: string;
  hotel: Hotel;
  hotelId: string;
  numberOfNights: number;
  roomType: string;
  status: string;
  totalPrice: number;
  userId: string;
}

export interface User {
  _id: string;
  email: string;
  name: string;
}

export interface UserBookings {
  flightBookings: FlightBooking[];
  hotelBookings: HotelBooking[];
  user: User;
}

export interface UsageStats {
  availableCountries: Array<{
    code: string;
    name: string;
  }>;
  citiesByCountry: Record<string, number>;
  hotelsByCountry: Record<string, number>;
  totalCities: number;
  totalCountries: number;
  totalFlightBookings: number;
  totalFlights: number;
  totalHotelBookings: number;
  totalHotels: number;
}

// API Response Types
export interface ApiResponse<T> {
  success?: boolean;
  data?: T;
  error?: string;
}

export interface FlightsResponse {
  flights: Flight[];
}

export interface HotelsResponse {
  hotels: Hotel[];
}

export interface CitiesResponse {
  cities: City[];
}

export interface CountriesResponse {
  countries: Country[];
}

export interface RoutesResponse {
  routes: Route[];
}

export interface FlightBookingsResponse {
  bookings: FlightBooking[];
}

export interface HotelBookingsResponse {
  bookings: HotelBooking[];
}

export interface UsageStatsResponse {
  stats: UsageStats;
}

// Form Types
export interface FlightSearchForm {
  origin: string;
  destination: string;
  date?: string;
}

export interface HotelSearchForm {
  city: string;
  checkIn?: string;
  checkOut?: string;
}

export interface FlightBookingForm {
  flightId: string;
  passengerName: string;
  passengerEmail: string;
}

export interface HotelBookingForm {
  hotelId: string;
  guestName: string;
  guestEmail: string;
  checkInDate: string;
  checkOutDate: string;
  roomType: string;
}

export interface BookingResponse {
  success: boolean;
  booking: {
    bookingId: string;
    bookingReference: string;
    seatNumber?: string;
    numberOfNights?: number;
    status: string;
    totalPrice?: number;
  };
}
