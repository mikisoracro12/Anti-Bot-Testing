export interface DetectionReason {
  rule: string;
  score: number;
  explanation: string;
}

export interface RequestEvent {
  id: string;
  timestamp: string;
  endpoint: string;
  http_method: string;
  outcome: string;
  risk_score: number;
  classification: string;
  detection_reasons: DetectionReason[];
  rate_limited: boolean;
  captcha_status: string | null;
  client_id: string;
  user_agent_hash: string | null;
  status_code: number;
  path: string;
}

export interface EventListResponse {
  items: RequestEvent[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface SummaryMetrics {
  total_requests: number;
  allowed_requests: number;
  blocked_requests: number;
  suspected_bot_requests: number;
  rate_limit_violations: number;
  captcha_failures: number;
}

export interface TimeSeriesPoint {
  timestamp: string;
  total: number;
  allowed: number;
  blocked: number;
  rate_limited: number;
  suspected: number;
}

export interface DashboardMetrics {
  summary: SummaryMetrics;
  activity: TimeSeriesPoint[];
  detection_reasons: { reason: string; count: number }[];
  recent_events: RequestEvent[];
}

export interface DetectionConfig {
  window_seconds: number;
  frequency_threshold: number;
  repeat_endpoint_threshold: number;
  suspicious_score_threshold: number;
  high_risk_score_threshold: number;
  captcha_trigger_score: number;
  rate_limit_enabled: boolean;
  rate_limit_requests: number;
  rate_limit_window_seconds: number;
  rate_limit_storage: string;
  captcha_enabled: boolean;
  captcha_provider: string;
  turnstile_site_key: string | null;
  trust_forwarded_headers: boolean;
  notes: string[];
}

export interface RateLimitConfig {
  enabled: boolean;
  requests: number;
  window_seconds: number;
  storage: string;
  redis_configured: boolean;
  limitations: string[];
}

export interface CaptchaStatus {
  enabled: boolean;
  provider: string;
  site_key_configured: boolean;
  secret_configured: boolean;
  mock_enabled: boolean;
  site_key: string | null;
  ready: boolean;
  warnings: string[];
}

export interface DemoResponse {
  status: string;
  message: string;
  risk_score: number;
  classification: string;
  detection_reasons: DetectionReason[];
  captcha_required: boolean;
  captcha_status: string | null;
  rate_limited: boolean;
  event_id: string | null;
}

export interface SimulationResultItem {
  index: number;
  status_code: number;
  outcome: string;
  risk_score: number | null;
  error: string | null;
}

export interface SimulationResponse {
  mode: string;
  total: number;
  successful: number;
  rejected: number;
  failed: number;
  cancelled: boolean;
  results: SimulationResultItem[];
  message: string;
}

export interface SimulationLimits {
  max_requests: number;
  min_interval_ms: number;
  allowed_hosts: string[];
  notes: string[];
}
