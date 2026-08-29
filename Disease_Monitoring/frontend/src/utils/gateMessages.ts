import type { CropPart } from "../api/observations";

const DEFAULT_GATE_MESSAGE: Record<CropPart, string> = {
  LEAF: "Please upload a valid tomato leaf image.",
  FRUIT: "Please upload a valid tomato fruit image.",
};

/** Show backend farmer message; hide technical errors from the user. */
export function formatGateRejection(
  cropPart: CropPart,
  reason?: string | null
): string {
  const text = String(reason ?? "").trim();
  if (text && !text.toLowerCase().startsWith("error:")) {
    return text;
  }
  return DEFAULT_GATE_MESSAGE[cropPart];
}
