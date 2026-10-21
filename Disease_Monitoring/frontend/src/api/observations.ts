import { Platform } from "react-native";
import { apiUrl } from "./client";

export type CropPart = "LEAF" | "FRUIT";

/** Build a multipart file part that works on web (Blob/File) and native (uri object). */
async function appendImageFile(form: FormData, uri: string): Promise<void> {
  const filename = "observation.jpg";
  const mimeType = "image/jpeg";

  if (Platform.OS === "web") {
    // Browser FormData requires a real Blob/File - RN's {uri,name,type} becomes "[object Object]".
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

export type MonitoringCase = {
  case_id: string;
  crop_part: CropPart;
  label?: string | null;
  created_at: string;
};

export type ObservationLocation = {
  latitude?: number;
  longitude?: number;
  area?: string;
  district?: string;
  province?: string;
  source?: string;
};

export type Observation = {
  observation_id: string;
  case_id: string;
  crop_part: CropPart;
  created_at: string;
  disease: string;
  severity_score: number;
  severity_class: "LOW" | "HIGH";
  estimated_affected_area_percentage?: number | null;
  similarity_score?: number | null;
  consistency_status: string;
  trend?: string | null;
  status?: string | null;
  recommendation?: Record<string, unknown> | null;
  weather_context?: Record<string, unknown> | null;
  location?: ObservationLocation | null;
};

export type MonitoringSummary = {
  initial_severity_pct: number;
  peak_severity_pct: number;
  final_severity_pct: number;
  overall_change_pct: number;
  overall_trend: string;
  peak_observation_number: number;
  severity_timeline: string;
  peak_note?: string | null;
  observation_count: number;
};

export type CaseStatus = {
  case_id: string;
  crop_part: CropPart;
  observation_count: number;
  overall_status: string;
  monitoring_summary?: MonitoringSummary | null;
  latest_observation?: Observation | null;
  latest_recommendation?: Record<string, unknown> | null;
  observations_summary: Array<{
    observation_id: string;
    created_at: string;
    severity_score: number;
    severity_class: string;
    trend?: string | null;
    consistency_status: string;
  }>;
};

export async function createCase(
  cropPart: CropPart,
  label?: string
): Promise<MonitoringCase> {
  const url = apiUrl("/cases");
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ crop_part: cropPart, label }),
    });
  } catch (e) {
    throw new Error(
      `Cannot reach API at ${url}. Is the backend running on 0.0.0.0:8000? (${String(e)})`
    );
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCaseStatus(caseId: string): Promise<CaseStatus> {
  const res = await fetch(apiUrl(`/cases/${caseId}/status`));
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export type FarmerInsight = {
  case_id: string;
  available: boolean;
  title: string;
  text: string;
  disclaimer?: string | null;
};

export async function getFarmerInsight(caseId: string): Promise<FarmerInsight> {
  const res = await fetch(apiUrl(`/cases/${caseId}/insight`));
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function caseReportPdfUrl(caseId: string): string {
  return apiUrl(`/cases/${caseId}/report.pdf`);
}

export async function downloadCaseReport(caseId: string): Promise<void> {
  const url = caseReportPdfUrl(caseId);
  if (Platform.OS === "web") {
    if (typeof window !== "undefined") {
      window.open(url, "_blank", "noopener,noreferrer");
    }
    return;
  }

  const FileSystem = await import("expo-file-system");
  const target = `${FileSystem.cacheDirectory}monitoring-report-${caseId}.pdf`;
  const result = await FileSystem.downloadAsync(url, target);
  try {
    const Sharing = await import("expo-sharing");
    if (await Sharing.isAvailableAsync()) {
      await Sharing.shareAsync(result.uri, {
        mimeType: "application/pdf",
        dialogTitle: "Monitoring report",
      });
      return;
    }
  } catch {
    // optional
  }
  throw new Error(`Report saved to ${result.uri}`);
}

export async function listObservations(caseId: string): Promise<{
  case_id: string;
  crop_part: CropPart;
  observations: Observation[];
}> {
  const res = await fetch(apiUrl(`/cases/${caseId}/observations`));
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadObservation(params: {
  caseId: string;
  cropPart: CropPart;
  disease: string;
  uri: string;
  latitude?: number;
  longitude?: number;
  area?: string;
  district?: string;
  province?: string;
  locationLabel?: string;
  locationSource?: "gps" | "manual" | "none";
  confirmSameCase?: boolean;
}): Promise<Record<string, unknown>> {
  const form = new FormData();
  form.append("crop_part", params.cropPart);
  form.append("disease", params.disease);
  if (params.latitude != null) form.append("latitude", String(params.latitude));
  if (params.longitude != null) form.append("longitude", String(params.longitude));
  if (params.area) form.append("area", params.area);
  if (params.district) form.append("district", params.district);
  if (params.province) form.append("province", params.province);
  if (params.locationLabel) form.append("location_label", params.locationLabel);
  if (params.locationSource && params.locationSource !== "none") {
    form.append("location_source", params.locationSource);
  }
  if (params.confirmSameCase) form.append("confirm_same_case", "true");

  await appendImageFile(form, params.uri);

  const res = await fetch(apiUrl(`/cases/${params.caseId}/observations`), {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteCase(caseId: string): Promise<void> {
  const res = await fetch(apiUrl(`/cases/${caseId}`), { method: "DELETE" });
  if (!res.ok && res.status !== 404) {
    throw new Error(await res.text());
  }
}

export const LEAF_DISEASES = ["early_blight", "late_blight", "leaf_miner"] as const;
export const FRUIT_DISEASES = [
  "anthracnose",
  "blossom_end_rot",
  "spotted_wilt_virus",
] as const;
