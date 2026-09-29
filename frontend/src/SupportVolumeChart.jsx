import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="chart-tooltip">
        <div className="tooltip-date">{label}</div>
        <div className="tooltip-value">
          <span className="tooltip-dot" />
          <strong>{payload[0].value}</strong> support tickets
        </div>
        <div className="tooltip-hint">Click to inspect activity</div>
      </div>
    )
  }
  return null
}

export default function SupportVolumeChart({ data, onSelectDate }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        data={data}
        margin={{ top: 12, right: 12, left: -20, bottom: 0 }}
        onClick={(state) => {
          if (state && state.activePayload && state.activePayload.length) {
            const pointData = state.activePayload[0].payload
            if (onSelectDate) onSelectDate(pointData.date)
          }
        }}
        style={{ cursor: 'pointer' }}
      >
        <defs>
          <linearGradient id="ticketFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#258b79" stopOpacity={0.28} />
            <stop offset="95%" stopColor="#258b79" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke="#e9eeeb" strokeDasharray="3 5" />
        <XAxis
          dataKey="date"
          tickLine={false}
          axisLine={false}
          tick={{ fill: '#7a8883', fontSize: 11, fontWeight: 500 }}
        />
        <YAxis
          allowDecimals={false}
          tickLine={false}
          axisLine={false}
          tick={{ fill: '#7a8883', fontSize: 11 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="tickets"
          stroke="#258b79"
          strokeWidth={2.5}
          fill="url(#ticketFill)"
          activeDot={{ r: 6, fill: '#258b79', stroke: '#ffffff', strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
