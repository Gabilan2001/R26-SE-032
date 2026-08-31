import React, { useMemo, useState } from "react";
import {
  Dimensions,
  Pressable,
  StyleSheet,
  Text,
  View,
  type LayoutChangeEvent,
} from "react-native";
import Svg, { Circle, Line, Path, Text as SvgText } from "react-native-svg";
import type { Observation } from "../../api/observations";
import { severityColors, type MonitoringPalette } from "../../theme/colors";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";
import {
  buildSeverityTrendPoints,
  type SeverityTrendPoint,
} from "../../utils/observationDisplay";

type Props = {
  observations: Observation[];
  peakObservationNumber?: number;
};

const PAD_L = 42;
const PAD_R = 14;
const PAD_T = 12;
const PAD_B = 46;
const CHART_H = 156;
const Y_MAX = 100;
const Y_TICKS = [0, 25, 50, 75, 100];

function pointColor(point: SeverityTrendPoint): string {
  return point.severityClass === "HIGH"
    ? severityColors.high.main
    : severityColors.low.main;
}

function chartGeometry(width: number, count: number) {
  const chartW = Math.max(40, width - PAD_L - PAD_R);
  const xAt = (index: number) => {
    if (count <= 1) return PAD_L + chartW / 2;
    return PAD_L + (index / (count - 1)) * chartW;
  };
  const yAt = (pct: number) =>
    PAD_T + CHART_H - (Math.min(Y_MAX, Math.max(0, pct)) / Y_MAX) * CHART_H;
  return { chartW, xAt, yAt, svgHeight: PAD_T + CHART_H + PAD_B };
}

function linePath(
  points: SeverityTrendPoint[],
  xAt: (i: number) => number,
  yAt: (pct: number) => number
): string {
  if (points.length === 0) return "";
  return points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${xAt(i)} ${yAt(p.severityPct)}`)
    .join(" ");
}

function areaPath(
  points: SeverityTrendPoint[],
  xAt: (i: number) => number,
  yAt: (pct: number) => number
): string {
  if (points.length === 0) return "";
  const baseline = PAD_T + CHART_H;
  const start = `M ${xAt(0)} ${baseline}`;
  const through = points
    .map((p, i) => `L ${xAt(i)} ${yAt(p.severityPct)}`)
    .join(" ");
  const end = `L ${xAt(points.length - 1)} ${baseline} Z`;
  return `${start} ${through} ${end}`;
}

export function SeverityTrendGraph({ observations, peakObservationNumber }: Props) {
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);
  const [width, setWidth] = useState(
    () => Dimensions.get("window").width - 36
  );
  const [selected, setSelected] = useState<number | null>(null);

  const points = useMemo(
    () => buildSeverityTrendPoints(observations, peakObservationNumber),
    [observations, peakObservationNumber]
  );

  const { xAt, yAt, svgHeight } = useMemo(
    () => chartGeometry(width, points.length),
    [width, points.length]
  );

  const onLayout = (e: LayoutChangeEvent) => {
    const next = e.nativeEvent.layout.width;
    if (next > 0 && Math.abs(next - width) > 1) setWidth(next);
  };

  if (points.length === 0) return null;

  const selectedPoint = selected != null ? points[selected] : null;
  const selectedX = selected != null ? xAt(selected) : 0;
  const selectedY = selectedPoint ? yAt(selectedPoint.severityPct) : 0;

  return (
    <View style={styles.card} onLayout={onLayout}>
      <Text style={styles.title}>Severity trend</Text>
      <Text style={styles.hint}>Tap a point for observation details</Text>

      <View style={styles.chartWrap}>
        <Svg width={width} height={svgHeight}>
          {Y_TICKS.map((tick) => {
            const y = yAt(tick);
            return (
              <React.Fragment key={tick}>
                <Line
                  x1={PAD_L}
                  y1={y}
                  x2={width - PAD_R}
                  y2={y}
                  stroke={p.trackLine}
                  strokeWidth={1}
                  strokeDasharray={tick === 0 ? undefined : "4 4"}
                />
                <SvgText
                  x={PAD_L - 8}
                  y={y + 4}
                  fill={p.textMuted}
                  fontSize={10}
                  textAnchor="end"
                >
                  {tick}%
                </SvgText>
              </React.Fragment>
            );
          })}

          {points.length > 1 ? (
            <>
              <Path d={areaPath(points, xAt, yAt)} fill={p.accentDim} opacity={0.55} />
              <Path
                d={linePath(points, xAt, yAt)}
                stroke={p.accent}
                strokeWidth={2.5}
                fill="none"
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            </>
          ) : null}

          {points.map((pt, i) => {
            const cx = xAt(i);
            const cy = yAt(pt.severityPct);
            const color = pointColor(pt);
            const r = pt.isPeak ? 7 : 5;
            return (
              <React.Fragment key={pt.observationNumber}>
                {pt.isPeak ? (
                  <Circle cx={cx} cy={cy} r={11} fill="none" stroke={p.accent} strokeWidth={2} />
                ) : null}
                <Circle cx={cx} cy={cy} r={r} fill={color} stroke={p.card} strokeWidth={2} />
                <SvgText
                  x={cx}
                  y={PAD_T + CHART_H + 18}
                  fill={pt.isPeak ? p.accent : p.textMuted}
                  fontSize={10}
                  fontWeight={pt.isPeak ? "700" : "500"}
                  textAnchor="middle"
                >
                  Obs {pt.observationNumber}
                </SvgText>
                <SvgText
                  x={cx}
                  y={PAD_T + CHART_H + 32}
                  fill={p.textMuted}
                  fontSize={9}
                  textAnchor="middle"
                >
                  {pt.dayLabel}
                </SvgText>
              </React.Fragment>
            );
          })}
        </Svg>

        {points.map((pt, i) => {
          const cx = xAt(i);
          const cy = yAt(pt.severityPct);
          return (
            <Pressable
              key={`hit-${pt.observationNumber}`}
              style={[
                styles.hitTarget,
                {
                  left: cx - 18,
                  top: cy - 18,
                },
              ]}
              onPress={() => setSelected((prev) => (prev === i ? null : i))}
              accessibilityRole="button"
              accessibilityLabel={`Observation ${pt.observationNumber}, ${pt.severityPct.toFixed(1)} percent`}
            />
          );
        })}

        {selectedPoint ? (
          <View
            style={[
              styles.tooltip,
              {
                left: Math.min(Math.max(selectedX - 72, 4), width - 148),
                top: Math.max(selectedY - 78, 4),
              },
            ]}
          >
            <Text style={styles.tooltipTitle}>
              Obs {selectedPoint.observationNumber} · {selectedPoint.dayLabel}
            </Text>
            <Text style={[styles.tooltipValue, { color: pointColor(selectedPoint) }]}>
              {selectedPoint.severityPct.toFixed(1)}% - {selectedPoint.severityClass}
            </Text>
            {selectedPoint.isPeak ? (
              <Text style={styles.tooltipPeak}>Peak severity</Text>
            ) : null}
          </View>
        ) : null}
      </View>

      {points.length < 2 ? (
        <Text style={styles.singleHint}>
          Add more observations to see the full severity trend line.
        </Text>
      ) : null}
    </View>
  );
}

function makeStyles(p: MonitoringPalette) {
  return StyleSheet.create({
    card: {
      marginTop: 12,
      backgroundColor: p.card,
      borderRadius: 14,
      borderWidth: 1,
      borderColor: p.cardBorder,
      padding: 14,
    },
    title: { color: p.textPrimary, fontWeight: "700", fontSize: 15 },
    hint: { color: p.textMuted, fontSize: 11, marginTop: 4 },
    chartWrap: { marginTop: 8, position: "relative" },
    hitTarget: {
      position: "absolute",
      width: 36,
      height: 36,
      borderRadius: 18,
    },
    tooltip: {
      position: "absolute",
      width: 144,
      backgroundColor: p.bgElevated,
      borderRadius: 10,
      borderWidth: 1,
      borderColor: p.accentBorder,
      paddingHorizontal: 10,
      paddingVertical: 8,
    },
    tooltipTitle: { color: p.textMuted, fontSize: 11, fontWeight: "600" },
    tooltipValue: { fontSize: 16, fontWeight: "800", marginTop: 4 },
    tooltipPeak: { color: p.accent, fontSize: 11, fontWeight: "700", marginTop: 4 },
    singleHint: { color: p.textMuted, fontSize: 11, marginTop: 8, lineHeight: 16 },
  });
}
