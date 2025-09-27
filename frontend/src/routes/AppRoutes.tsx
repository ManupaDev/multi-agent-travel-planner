import { Routes, Route } from "react-router-dom";
import { Home } from "@/pages/Home";
import { BookingLayout } from "@/pages/BookingLayout";
import { NotFound } from "@/pages/NotFound";
import { FlightsPage } from "@/features/flights/FlightsPage";
import { HotelsPage } from "@/features/hotels/HotelsPage";
import { MyBookingsPage } from "@/features/bookings/MyBookingsPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />

      {/* Booking routes with chat assistant */}
      <Route element={<BookingLayout />}>
        <Route path="/flights" element={<FlightsPage />} />
        <Route path="/hotels" element={<HotelsPage />} />
      </Route>

      <Route path="/bookings" element={<MyBookingsPage />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
