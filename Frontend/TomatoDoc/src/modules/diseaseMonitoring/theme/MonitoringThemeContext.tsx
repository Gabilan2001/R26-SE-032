import React, { createContext, useContext, useMemo } from "react";
import type { CropPart } from "../api/observations";
import {
  hubPalette,
  leafPalette,
  fruitPalette,
  type MonitoringPalette,
} from "./colors";

type Mode = "hub" | "LEAF" | "FRUIT";

const MonitoringThemeContext = createContext<MonitoringPalette>(hubPalette);

export function MonitoringThemeProvider({
  cropPart,
  children,
}: {
  cropPart?: CropPart | null;
  children: React.ReactNode;
}) {
  const value = useMemo(() => {
    if (cropPart === "LEAF") return leafPalette;
    if (cropPart === "FRUIT") return fruitPalette;
    return hubPalette;
  }, [cropPart]);

  return (
    <MonitoringThemeContext.Provider value={value}>
      {children}
    </MonitoringThemeContext.Provider>
  );
}

/** Active monitoring palette (hub / leaf lime / fruit red). */
export function useMonitoringPalette(): MonitoringPalette {
  return useContext(MonitoringThemeContext);
}

export type { Mode };
