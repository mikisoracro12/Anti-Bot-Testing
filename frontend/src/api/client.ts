import axios from "axios";
import type {
  CaptchaStatus,
  DashboardMetrics,
  DemoResponse,
  DetectionConfig,
  EventListResponse,
  RateLimitConfig,
  SimulationLimits,
  SimulationResponse,
} from "../types/api";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

export interface EventQuery {
  page?: number;
  page_size?: number;
  outcome?: string;
  classification?: string;
  detection_reason?: string;
  start_time?: string;
  end_time?: string;
  sort_by?: string;
  sort_order?: string;
}

export async function fetchDashboard(params?: {
  start_time?: string;
  end_time?: string;
  bucket_minutes?: number;
}): Promise<DashboardMetrics> {
  const { data } = await api.get<DashboardMetrics>("/analytics/dashboard", { params });
  return data;
}

export async function fetchEvents(params: EventQuery = {}): Promise<EventListResponse> {
  const { data } = await api.get<EventListResponse>("/events", { params });
  return data;
}

export async function fetchEvent(id: string) {
  const { data } = await api.get(`/events/${id}`);
  return data;
}

export async function fetchDetectionConfig(): Promise<DetectionConfig> {
  const { data } = await api.get<DetectionConfig>("/config/detection");
  return data;
}

export async function fetchRateLimitConfig(): Promise<RateLimitConfig> {
  const { data } = await api.get<RateLimitConfig>("/config/rate-limits");
  return data;
}

export async function fetchCaptchaStatus(): Promise<CaptchaStatus> {
  const { data } = await api.get<CaptchaStatus>("/config/captcha");
  return data;
}

export async function postDemo(payload: {
  message: string;
  captcha_token?: string;
}): Promise<DemoResponse> {
  const { data } = await api.post<DemoResponse>("/demo/protected", payload);
  return data;
}

export async function verifyCaptcha(token: string) {
  const { data } = await api.post("/demo/captcha/verify", { token });
  return data;
}

export async function fetchSimulationLimits(): Promise<SimulationLimits> {
  const { data } = await api.get<SimulationLimits>("/simulation/limits");
  return data;
}

export async function runSimulation(payload: {
  mode: "normal" | "burst" | "repeat";
  request_count: number;
  interval_ms: number;
  endpoint: "demo" | "health";
}): Promise<SimulationResponse> {
  const { data } = await api.post<SimulationResponse>("/simulation/run", payload);
  return data;
}

export async function cancelSimulation() {
  const { data } = await api.post("/simulation/cancel");
  return data;
}

export async function fetchHealth() {
  const { data } = await api.get("/health");
  return data;
}

export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (err.response?.data?.message) return String(err.response.data.message);
    if (err.message) return err.message;
  }
  if (err instanceof Error) return err.message;
  return "Unexpected error";
}

export default api;
