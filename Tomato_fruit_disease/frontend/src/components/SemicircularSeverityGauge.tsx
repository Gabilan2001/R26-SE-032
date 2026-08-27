import React, { useMemo } from "react";
import { View, Text, StyleSheet } from "react-native";
import Svg, { Path } from "react-native-svg";
import { severityColors, type SeverityBand } from "../theme/colors";

type Props = {
  /** Estimated affected-area % displayed as 0–100 for the gauge arc */
  score: number;
  band: SeverityBand;
  size?: number;
  strokeWidth?: number;
};

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n));
}

/** Top-opening semicircle: diameter along bottom, arc bulges upward (SVG y down). */
function describeSemicircleArc(
  cx: number,
  cy: number,
  r: number
): string {
  const x0 = cx - r;
  const y0 = cy;
  const x1 = cx + r;
  const y1 = cy;
  return `M ${x0} ${y0} A ${r} ${r} 0 0 0 ${x1} ${y1}`;
}

export function SemicircularSeverityGauge({
  score,
  band,
  size = 200,
  strokeWidth = 14,
}: Props) {
  const colors = severityColors[band];
  const pct = clamp(Math.round(score), 0, 100);

  const padding = strokeWidth / 2 + 4;
  const width = size;
  const baselineY = size * 0.62;
  const cx = width / 2;
  const r = Math.max(24, width / 2 - padding);

  const d = useMemo(
    () => describeSemicircleArc(cx, baselineY, r),
    [cx, baselineY, r]
  );

  const arcLength = Math.PI * r;
  const filled = (pct / 100) * arcLength;
  const dashArray = `${filled} ${arcLength}`;

  const svgHeight = baselineY + 4;

  return (
    <View style={[styles.wrap, { width }]}>
      <Svg width={width} height={svgHeight} viewBox={`0 0 ${width} ${svgHeight}`}>
        <Path
          d={d}
          stroke="#3a4f42"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          fill="none"
        />
        <Path
          d={d}
          stroke={colors.main}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={dashArray}
        />
      </Svg>
      <View
        style={[
          styles.labelBlock,
          { top: baselineY - r * 0.55 - 8, width },
        ]}
        pointerEvents="none"
      >
        <Text style={[styles.pct, { color: colors.main }]}>{pct}%</Text>
        <Text style={styles.sub}>est. affected area</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    alignItems: "center",
    justifyContent: "flex-end",
  },
  labelBlock: {
    position: "absolute",
    alignItems: "center",
  },
  pct: {
    fontSize: 28,
    fontWeight: "700",
    letterSpacing: -0.5,
  },
  sub: {
    marginTop: 2,
    fontSize: 13,
    color: "#8a9d91",
    fontWeight: "500",
  },
});
