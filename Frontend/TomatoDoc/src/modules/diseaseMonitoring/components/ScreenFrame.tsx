import React from "react";
import { View, type ViewProps } from "react-native";

/**
 * Plain full-height frame used where the monitoring screens previously used SafeAreaView.
 * The forest header (LeafScanAppHeader) now applies the top inset itself.
 */
export function ScreenFrame(props: ViewProps) {
  return <View {...props} />;
}
