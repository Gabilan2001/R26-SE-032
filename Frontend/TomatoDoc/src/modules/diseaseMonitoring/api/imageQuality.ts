import { Platform } from "react-native";
import type { CropPart } from "./observations";
import { apiUrl } from "./client";

export type QualityCheckStatus = "pass" | "warn" | "fail";

export type QualityCheckItem = {
  status: QualityCheckStatus;
  score: number;
  message: string;
  min_side_px?: number;
};

export type ImageQualityResult = {
  ok: boolean;
  checks: {
    blur: QualityCheckItem;
    brightness: QualityCheckItem;
    distance: QualityCheckItem;
  };
  overall: "good" | "fair" | "poor";
  farmer_summary: string;
  can_upload: boolean;
};

async function appendImageFile(form: FormData, uri: string): Promise<void> {
  const filename = "quality-check.jpg";
  const mimeType = "image/jpeg";

  if (Platform.OS === "web") {
    const response = await fetch(uri);
    const blob = await response.blob();
    const type = blob.type || mimeType;
    const file =
      typeof File !== "undefined"
        ? new File([blob], filename, { type })
        : blob;
    form.append("file", file, filename);
    return;
  }

  form.append("file", {
    uri,
    name: filename,
    type: mimeType,
  } as unknown as Blob);
}

export async function checkImageQuality(
  uri: string,
  cropPart: CropPart
): Promise<ImageQualityResult> {
  const form = new FormData();
  form.append("crop_part", cropPart);
  await appendImageFile(form, uri);

  const res = await fetch(apiUrl("/observations/quality-check"), {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
