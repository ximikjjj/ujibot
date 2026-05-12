import { useEffect } from "react";
import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import BottomNav from "@/components/BottomNav";
import Dashboard from "@/pages/Dashboard";
import Connect from "@/pages/Connect";
import Scales from "@/pages/Scales";
import Goals from "@/pages/Goals";
import Digest from "@/pages/Digest";

const queryClient = new QueryClient();

function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center text-muted-foreground text-sm">
      Страница не найдена
    </div>
  );
}

function AppContent() {
  useEffect(() => {
    window.Telegram?.WebApp?.ready();
    window.Telegram?.WebApp?.expand();
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/connect" component={Connect} />
        <Route path="/scales" component={Scales} />
        <Route path="/goals" component={Goals} />
        <Route path="/digest" component={Digest} />
        <Route component={NotFound} />
      </Switch>
      <BottomNav />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
        <AppContent />
      </WouterRouter>
    </QueryClientProvider>
  );
}
