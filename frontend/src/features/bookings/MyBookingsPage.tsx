import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import { Plane, Hotel, Search, Mail } from "lucide-react";
import { bookingsApi } from "./bookingsApi";
import type { UserBookings, FlightBooking, HotelBooking } from "@/lib/types";

export function MyBookingsPage() {
  const [email, setEmail] = useState("");
  const [userBookings, setUserBookings] = useState<UserBookings | null>(null);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSearch = async () => {
    if (!email.trim()) {
      toast({
        title: "Email Required",
        description: "Please enter your email address to view bookings.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const response = await bookingsApi.getUserBookings(email.trim());
      setUserBookings(response);

      if (
        response.flightBookings.length === 0 &&
        response.hotelBookings.length === 0
      ) {
        toast({
          title: "No Bookings Found",
          description: "No bookings found for this email address.",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description:
          "Failed to load bookings. Please check your email and try again.",
        variant: "destructive",
      });
      setUserBookings(null);
    } finally {
      setLoading(false);
    }
  };

  // Helper functions
  const formatCurrency = (amount: number, currency: string) => {
    return `${currency} ${amount}`;
  };

  const getStatusBadge = (status: string) => {
    const variant = status === "confirmed" ? "default" : "secondary";
    return <Badge variant={variant}>{status}</Badge>;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4">My Bookings</h1>
        <p className="text-muted-foreground mb-6">
          Enter your email address to view all your flight and hotel bookings.
        </p>

        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Find Your Bookings
            </CardTitle>
            <CardDescription>
              Enter your email address to retrieve your booking history
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
              />
            </div>
            <Button
              onClick={handleSearch}
              disabled={loading}
              className="w-full"
            >
              <Search className="mr-2 h-4 w-4" />
              {loading ? "Searching..." : "Search Bookings"}
            </Button>
          </CardContent>
        </Card>
      </div>

      {userBookings && (
        <div className="space-y-8">
          <div className="text-sm text-muted-foreground">
            Showing bookings for:{" "}
            <strong>{userBookings.user?.email || email}</strong>
          </div>

          {/* Flight Bookings */}
          {userBookings.flightBookings.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plane className="h-5 w-5" />
                  Flight Bookings ({userBookings.flightBookings.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Flight</TableHead>
                      <TableHead>Route</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Seat</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Total</TableHead>
                      <TableHead>Reference</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {userBookings.flightBookings.map(
                      (booking: FlightBooking) => (
                        <TableRow key={booking._id}>
                          <TableCell>
                            <div>
                              <div className="font-medium">
                                {booking.flight.airline}{" "}
                                {booking.flight.flightNumber}
                              </div>
                              <div className="text-sm text-muted-foreground">
                                {booking.flight.aircraft}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">
                              {typeof booking.flight.origin === "string"
                                ? booking.flight.origin
                                : booking.flight.origin.city}{" "}
                              →{" "}
                              {typeof booking.flight.destination === "string"
                                ? booking.flight.destination
                                : booking.flight.destination.city}
                            </div>
                          </TableCell>
                          <TableCell>{booking.flight.flightDate}</TableCell>
                          <TableCell>{booking.seatNumber}</TableCell>
                          <TableCell>
                            {getStatusBadge(booking.status)}
                          </TableCell>
                          <TableCell>
                            {formatCurrency(
                              booking.totalPrice,
                              booking.currency
                            )}
                          </TableCell>
                          <TableCell>
                            <code className="text-sm">
                              {booking.bookingReference}
                            </code>
                          </TableCell>
                        </TableRow>
                      )
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* Hotel Bookings */}
          {userBookings.hotelBookings.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Hotel className="h-5 w-5" />
                  Hotel Bookings ({userBookings.hotelBookings.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Hotel</TableHead>
                      <TableHead>Location</TableHead>
                      <TableHead>Check-in</TableHead>
                      <TableHead>Check-out</TableHead>
                      <TableHead>Room</TableHead>
                      <TableHead>Nights</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Total</TableHead>
                      <TableHead>Reference</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {userBookings.hotelBookings.map((booking: HotelBooking) => (
                      <TableRow key={booking._id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">
                              {booking.hotel.name}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {booking.hotel.starRating} star
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            {booking.hotel.city}, {booking.hotel.country}
                          </div>
                        </TableCell>
                        <TableCell>{booking.checkInDate}</TableCell>
                        <TableCell>{booking.checkOutDate}</TableCell>
                        <TableCell>{booking.roomType}</TableCell>
                        <TableCell>{booking.numberOfNights}</TableCell>
                        <TableCell>{getStatusBadge(booking.status)}</TableCell>
                        <TableCell>
                          {formatCurrency(booking.totalPrice, booking.currency)}
                        </TableCell>
                        <TableCell>
                          <code className="text-sm">
                            {booking.bookingReference}
                          </code>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {userBookings.flightBookings.length === 0 &&
            userBookings.hotelBookings.length === 0 && (
              <Card>
                <CardContent className="text-center py-12">
                  <div className="text-lg mb-2">No bookings found</div>
                  <div className="text-muted-foreground">
                    You don't have any bookings yet. Start planning your trip!
                  </div>
                </CardContent>
              </Card>
            )}
        </div>
      )}
    </div>
  );
}
