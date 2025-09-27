import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Plane, Hotel, Calendar } from "lucide-react";

export function Navbar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <Link to="/" className="flex items-center space-x-2">
            <Plane className="h-6 w-6" />
            <span className="text-xl font-bold">Travel Planner</span>
          </Link>

          <div className="flex items-center space-x-4">
            <Button variant={isActive("/") ? "default" : "ghost"} asChild>
              <Link to="/">
                <Plane className="mr-2 h-4 w-4" />
                Home
              </Link>
            </Button>

            <Button
              variant={isActive("/flights") ? "default" : "ghost"}
              asChild
            >
              <Link to="/flights">
                <Plane className="mr-2 h-4 w-4" />
                Flights
              </Link>
            </Button>

            <Button variant={isActive("/hotels") ? "default" : "ghost"} asChild>
              <Link to="/hotels">
                <Hotel className="mr-2 h-4 w-4" />
                Hotels
              </Link>
            </Button>

            <Button
              variant={isActive("/bookings") ? "default" : "ghost"}
              asChild
            >
              <Link to="/bookings">
                <Calendar className="mr-2 h-4 w-4" />
                My Bookings
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}
