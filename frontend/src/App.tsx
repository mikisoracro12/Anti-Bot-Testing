import { Route, Routes } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { AboutPage } from "./pages/AboutPage";
import { CaptchaPage } from "./pages/CaptchaPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DetectionPage } from "./pages/DetectionPage";
import { EventsPage } from "./pages/EventsPage";
import { RateLimitsPage } from "./pages/RateLimitsPage";
import { SimulatorPage } from "./pages/SimulatorPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="detection" element={<DetectionPage />} />
        <Route path="rate-limits" element={<RateLimitsPage />} />
        <Route path="captcha" element={<CaptchaPage />} />
        <Route path="simulator" element={<SimulatorPage />} />
        <Route path="about" element={<AboutPage />} />
      </Route>
    </Routes>
  );
}
