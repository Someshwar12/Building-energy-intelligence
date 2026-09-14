"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ConsumptionPoint } from "@/lib/api";

export default function ConsumptionChart({
  points,
}: {
  points: ConsumptionPoint[];
}) {
  const chartData = points
    .filter((point) => point.energy_kwh !== null)
    .map((point) => ({
      timestamp: point.timestamp,
      energy: point.energy_kwh,
    }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer
        width="100%"
        height="100%"
      >
        <LineChart
          data={chartData}
          margin={{
            top: 8,
            right: 8,
            left: 0,
            bottom: 8,
          }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
          />

          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) =>
              new Date(value).toLocaleDateString(
                undefined,
                {
                  month: "short",
                  day: "numeric",
                },
              )
            }
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            minTickGap={32}
          />

          <YAxis
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            width={48}
            unit=" kWh"
          />

          <Tooltip
            labelFormatter={(value) =>
              new Date(
                String(value),
              ).toLocaleString()
            }
            formatter={(value) => [
              `${Number(value).toFixed(1)} kWh`,
              "Energy",
            ]}
          />

          <Line
            type="monotone"
            dataKey="energy"
            stroke="currentColor"
            strokeWidth={1.8}
            dot={false}
            className="text-slate-900"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}