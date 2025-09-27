import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";
import type { Flight, Hotel } from "@/lib/types";

const flightBookingSchema = z.object({
  passengerName: z.string().min(2, "Name must be at least 2 characters"),
  passengerEmail: z.string().email("Please enter a valid email address"),
});

const hotelBookingSchema = z.object({
  guestName: z.string().min(2, "Name must be at least 2 characters"),
  guestEmail: z.string().email("Please enter a valid email address"),
  checkInDate: z.string().min(1, "Check-in date is required"),
  checkOutDate: z.string().min(1, "Check-out date is required"),
  roomType: z.string().min(1, "Room type is required"),
});

type FlightBookingData = z.infer<typeof flightBookingSchema>;
type HotelBookingData = z.infer<typeof hotelBookingSchema>;

interface BookingFormProps {
  type: "flight" | "hotel";
  data: Flight | Hotel;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit?: (bookingData: any) => void;
}

export function BookingForm({
  type,
  data,
  open,
  onOpenChange,
  onSubmit,
}: BookingFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const schema = type === "flight" ? flightBookingSchema : hotelBookingSchema;

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
  } = useForm<FlightBookingData | HotelBookingData>({
    resolver: zodResolver(schema),
  });

  const onSubmitForm = async (
    formData: FlightBookingData | HotelBookingData
  ) => {
    setIsSubmitting(true);

    try {
      const bookingData = {
        ...formData,
        [type === "flight" ? "flightId" : "hotelId"]: data._id,
      };

      if (onSubmit) {
        await onSubmit(bookingData);
      }

      toast({
        title: "Booking Successful!",
        description: `Your ${type} has been booked successfully.`,
      });

      reset();
      onOpenChange(false);
    } catch (error) {
      toast({
        title: "Booking Failed",
        description: `Failed to book ${type}. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const roomTypes = ["Standard", "Deluxe", "Suite", "Executive"];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>
            Book {type === "flight" ? "Flight" : "Hotel"}
          </DialogTitle>
          <DialogDescription>
            {type === "flight"
              ? `Flight ${(data as Flight).flightNumber} - ${
                  (data as Flight).airline
                }`
              : `${(data as Hotel).name} - ${(data as Hotel).city}`}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmitForm)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor={type === "flight" ? "passengerName" : "guestName"}>
              {type === "flight" ? "Passenger Name" : "Guest Name"}
            </Label>
            <Input
              id={type === "flight" ? "passengerName" : "guestName"}
              {...register(type === "flight" ? "passengerName" : "guestName")}
              placeholder="Enter full name"
            />
            {(type === "flight"
              ? (errors as any).passengerName
              : (errors as any).guestName) && (
              <p className="text-sm text-red-500">
                {type === "flight"
                  ? (errors as any).passengerName?.message
                  : (errors as any).guestName?.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label
              htmlFor={type === "flight" ? "passengerEmail" : "guestEmail"}
            >
              Email Address
            </Label>
            <Input
              id={type === "flight" ? "passengerEmail" : "guestEmail"}
              type="email"
              {...register(type === "flight" ? "passengerEmail" : "guestEmail")}
              placeholder="Enter email address"
            />
            {(type === "flight"
              ? (errors as any).passengerEmail
              : (errors as any).guestEmail) && (
              <p className="text-sm text-red-500">
                {type === "flight"
                  ? (errors as any).passengerEmail?.message
                  : (errors as any).guestEmail?.message}
              </p>
            )}
          </div>

          {type === "hotel" && (
            <>
              <div className="space-y-2">
                <Label htmlFor="checkInDate">Check-in Date</Label>
                <Input
                  id="checkInDate"
                  type="date"
                  {...register("checkInDate")}
                />
                {(errors as any).checkInDate && (
                  <p className="text-sm text-red-500">
                    {(errors as any).checkInDate.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="checkOutDate">Check-out Date</Label>
                <Input
                  id="checkOutDate"
                  type="date"
                  {...register("checkOutDate")}
                />
                {(errors as any).checkOutDate && (
                  <p className="text-sm text-red-500">
                    {(errors as any).checkOutDate.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="roomType">Room Type</Label>
                <Select onValueChange={(value) => setValue("roomType", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select room type" />
                  </SelectTrigger>
                  <SelectContent>
                    {roomTypes.map((roomType) => (
                      <SelectItem key={roomType} value={roomType}>
                        {roomType}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {(errors as any).roomType && (
                  <p className="text-sm text-red-500">
                    {(errors as any).roomType.message}
                  </p>
                )}
              </div>
            </>
          )}

          <div className="flex justify-end space-x-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting
                ? "Booking..."
                : `Book ${type === "flight" ? "Flight" : "Hotel"}`}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
