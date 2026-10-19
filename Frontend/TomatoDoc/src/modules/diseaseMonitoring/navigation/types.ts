import type { CropPart, CaseStatus, MonitoringCase, Observation } from "../api/observations";
import type { ObservationLocationSelection } from "../utils/locationCapture";

export type AppStep =
  | "home"
  | "create"
  | "upload"
  | "result"
  | "overview";

export type MonitoringSession = {
  step: AppStep;
  cropPart: CropPart | null;
  caseData: MonitoringCase | null;
  status: CaseStatus | null;
  observations: Observation[];
  /** Local device URIs keyed by observation_id (session preview only). */
  imageUris: Record<string, string>;
  /** Which observation number the user is uploading (1–3). */
  uploadTarget: number;
  /** Location chosen on Observation 1 — reused for Obs 2/3 weather. */
  caseLocation: ObservationLocationSelection | null;
  lastMessage: string | null;
};

export const initialSession: MonitoringSession = {
  step: "home",
  cropPart: null,
  caseData: null,
  status: null,
  observations: [],
  imageUris: {},
  uploadTarget: 1,
  caseLocation: null,
  lastMessage: null,
};
