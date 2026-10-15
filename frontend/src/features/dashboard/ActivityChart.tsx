import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TimeSeriesPoint } from "../../types/api";
import { EmptyState } from "../../components/EmptyState";

interface Props {
  data: TimeSeriesPoint[];
}

export function ActivityChart({ data }: Props) {
  if (!data.length) {
    return (
      <EmptyState
        title="No activity yet"
        description="Send demo requests or run the traffic simulator to populate this chart."
      />
    );
  }

  const chartData = data.map((p) => ({
    ...p,
    label: new Date(p.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="totalFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3d9cf0" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#3d9cf0" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="blockedFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f87171" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#f87171" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} />
          <YAxis
            allowDecimals={false}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={false}
            width={32}
          />
          <Tooltip
            contentStyle={{
              background: "#151c28",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Area
            type="monotone"
            dataKey="total"
            name="Total"
            stroke="#3d9cf0"
            fill="url(#totalFill)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="blocked"
            name="Blocked"
            stroke="#f87171"
            fill="url(#blockedFill)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="suspected"
            name="Suspected"
            stroke="#fbbf24"
            fill="transparent"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
