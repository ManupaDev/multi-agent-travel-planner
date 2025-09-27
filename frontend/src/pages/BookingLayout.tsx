import { Outlet } from "react-router-dom";
import { ChatLauncher } from "@/components/ChatLauncher";

export function BookingLayout() {
  return (
    <div className="relative">
      <Outlet />
      <ChatLauncher />
    </div>
  );
}
