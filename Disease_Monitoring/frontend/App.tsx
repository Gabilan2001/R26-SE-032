import React, { useState } from "react";
import {
  deleteCase,
  type CropPart,
  type MonitoringCase,
  type Observation,
} from "./src/api/observations";
import { TARGET_OBSERVATIONS } from "./src/config/modality";
import { initialSession, type MonitoringSession } from "./src/navigation/types";
import { CreateCaseScreen } from "./src/screens/monitoring/CreateCaseScreen";
import { HomeScreen } from "./src/screens/monitoring/HomeScreen";
import { ObservationResultScreen } from "./src/screens/monitoring/ObservationResultScreen";
import { ObservationUploadScreen } from "./src/screens/monitoring/ObservationUploadScreen";
import { OverallMonitoringScreen } from "./src/screens/monitoring/OverallMonitoringScreen";

/**
 * 7-screen observation monitoring flow (state machine, no extra nav library):
 * 1 Home → 2 Create Case → 3–6 Upload/Result × Obs 1–3 → 7 Overall
 */
export default function App() {
  const [session, setSession] = useState<MonitoringSession>(initialSession);
  const [attachWeather, setAttachWeather] = useState(true);
  const [latestObservation, setLatestObservation] = useState<Observation | null>(null);
  const [latestImageUri, setLatestImageUri] = useState<string | null>(null);

  const discardIncompleteCase = async (caseId: string | null | undefined) => {
    if (!caseId) return;
    try {
      await deleteCase(caseId);
    } catch {
      // ignore
    }
  };

  const reset = () => {
    setSession(initialSession);
    setLatestObservation(null);
    setLatestImageUri(null);
  };

  const abandonCurrentCaseAndGoCreate = async () => {
    await discardIncompleteCase(session.caseData?.case_id);
    setLatestObservation(null);
    setLatestImageUri(null);
    setSession((s) => ({
      ...initialSession,
      cropPart: s.cropPart,
      step: "create",
    }));
  };

  if (session.step === "home") {
    return (
      <HomeScreen
        onSelect={(cropPart: CropPart) =>
          setSession((s) => ({ ...s, cropPart, step: "create" }))
        }
      />
    );
  }

  if (session.step === "create" && session.cropPart) {
    return (
      <CreateCaseScreen
        cropPart={session.cropPart}
        attachWeather={attachWeather}
        onToggleWeather={setAttachWeather}
        onBack={() => setSession((s) => ({ ...s, step: "home", cropPart: null }))}
        onCreated={(created: MonitoringCase) => {
          setSession((s) => ({
            ...s,
            caseData: created,
            observations: [],
            status: null,
            imageUris: {},
            caseLocation: null,
            uploadTarget: 1,
            step: "upload",
          }));
        }}
      />
    );
  }

  if (
    session.step === "upload" &&
    session.cropPart &&
    session.caseData
  ) {
    return (
      <ObservationUploadScreen
        caseData={session.caseData}
        cropPart={session.cropPart}
        observationNumber={session.uploadTarget}
        attachWeather={attachWeather}
        savedLocation={session.caseLocation}
        onLocationCommitted={(loc) =>
          setSession((s) => ({ ...s, caseLocation: loc }))
        }
        onBack={() => void abandonCurrentCaseAndGoCreate()}
        onSuccess={({ observation, status, observations, imageUri, location }) => {
          setLatestObservation(observation);
          setLatestImageUri(imageUri);
          setSession((s) => ({
            ...s,
            status,
            observations,
            caseLocation: location ?? s.caseLocation,
            imageUris: {
              ...s.imageUris,
              [observation.observation_id]: imageUri,
            },
            step: "result",
          }));
        }}
      />
    );
  }

  if (
    session.step === "result" &&
    session.caseData &&
    latestObservation
  ) {
    const observationNumber = session.observations.length;
    const previousObservation =
      observationNumber > 1 ? session.observations[observationNumber - 2] : null;
    return (
      <ObservationResultScreen
        caseId={session.caseData.case_id}
        observationNumber={observationNumber}
        observation={latestObservation}
        previousObservation={previousObservation}
        cropPart={session.cropPart ?? undefined}
        imageUri={
          latestImageUri ?? session.imageUris[latestObservation.observation_id]
        }
        onBack={() => void abandonCurrentCaseAndGoCreate()}
        onNextObservation={() =>
          setSession((s) => ({
            ...s,
            uploadTarget: Math.min(observationNumber + 1, TARGET_OBSERVATIONS),
            step: "upload",
          }))
        }
        onViewOverall={() => setSession((s) => ({ ...s, step: "overview" }))}
      />
    );
  }

  if (
    session.step === "overview" &&
    session.cropPart &&
    session.caseData
  ) {
    return (
      <OverallMonitoringScreen
        cropPart={session.cropPart}
        caseId={session.caseData.case_id}
        status={session.status}
        observations={session.observations}
        imageUris={session.imageUris}
        onRestart={reset}
      />
    );
  }

  // Fallback
  return (
    <HomeScreen
      onSelect={(cropPart: CropPart) =>
        setSession((s) => ({ ...s, cropPart, step: "create" }))
      }
    />
  );
}
