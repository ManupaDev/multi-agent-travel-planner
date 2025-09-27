export function Footer() {
  return (
    <footer className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 mt-auto">
      <div className="container mx-auto px-4 py-6">
        <div className="text-center text-sm text-muted-foreground">
          <p>&copy; 2025 Multi-Agent Travel Planner. All rights reserved.</p>
          <p className="mt-2">
            Powered by Convex APIs & Multi-Agent AutoGen Backend
          </p>
        </div>
      </div>
    </footer>
  );
}
