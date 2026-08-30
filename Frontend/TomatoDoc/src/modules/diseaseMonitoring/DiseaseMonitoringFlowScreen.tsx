import React, { useEffect, useRef, useState } from "react";
import {
  deleteCase,
  type CropPart,
  type MonitoringCase,
  type Observation,
} from "./api/observations";
import { TARGET_OBSERVATIONS } from "./config/modality";
import { initialSession, type MonitoringSession } from "./navigation/types";
import { CreateCaseScreen } from "./screens/monitoring/CreateCaseScreen";
import { HomeScreen } from "./screens/monitoring/HomeScreen";
import { ObservationResultScreen } from "./screens/monitoring/ObservationResultScreen";
import { ObservationUploadScreen } from "./screens/monitoring/ObservationUploadScreen";
import { OverallMonitoringScreen } from "./screens/monitoring/OverallMonitoringScreen";
import { MonitoringThemeProvider } from "./theme/MonitoringThemeContext";

/**
 * Embeds the Disease Monitoring state-machine UI inside TomatoDoc navigation.
 * Logic matches the standalone DM App.tsx; Exit returns to TomatoDoc Home.
 */
type NavLike = {
  canGoBack: () => boolean;
  goBack: () => void;
  navigate: (...args: any[]) => void;
};

type RouteLike = {
  params?: {
    initialCropPart?: CropPart;
  };
};

type Props = {
  navigation: NavLike;
  route?: RouteLike;
};

export default function DiseaseMonitoringFlowScreen({ navigation, route }: Props) {
  const [session, setSession] = useState<MonitoringSession>(initialSession);
  const [attachWeather, setAttachWeather] = useState(true);
  const [latestObservation, setLatestObservation] = useState<Observation | null>(null);
  const [latestImageUri, setLatestImageUri] = useState<string | null>(null);
  const appliedInitial = useRef(false);

  useEffect(() => {
    if (appliedInitial.current) return;
    const part = route?.params?.initialCropPart;
    if (part === "LEAF" || part === "FRUIT") {
      appliedInitial.current = true;
      setSession((s) => ({ ...s, cropPart: part, step: "create" }));
    }
  }, [route?.params?.initialCropPart]);

  /** Incomplete cases (not finished on Overall) are removed so test uploads do not fill the DB. */
  const discardIncompleteCase = async (
    caseId: string | null | undefined,
    observationCount: number,
    completedOverall: boolean
  ) => {
    if (!caseId || completedOverall) return;
    if (observationCount >= TARGET_OBSERVATIONS && completedOverall) return;
    try {
      await deleteCase(caseId);
    } catch {
      // Ignore network errors — local UI still resets.
    }
  };

  const clearLocalSession = () => {
    appliedInitial.current = false;
    setSession(initialSession);
    setLatestObservation(null);
    setLatestImageUri(null);
  };

  const exitToTomatoDoc = async () => {
    const completed = session.step === "overview";
    await discardIncompleteCase(
      session.caseData?.case_id,
      session.observations.length,
      completed
    );
    clearLocalSession();
    if (navigation.canGoBack()) {
      navigation.goBack();
    } else {
      navigation.navigate("MainTabs");
    }
  };

  const resetFlow = () => {
    // Completed overall — keep DB rows; only reset UI for a new case.
    setSession(initialSession);
    setLatestObservation(null);
    setLatestImageUri(null);
  };

  const abandonCurrentCaseAndGoCreate = async () => {
    await discardIncompleteCase(
      session.caseData?.case_id,
      session.observations.length,
      false
    );
    setLatestObservation(null);
    setLatestImageUri(null);
    setSession((s) => ({
      ...initialSession,
      cropPart: s.cropPart,
      step: "create",
    }));
  };

  let body: React.ReactNode;

  if (session.step === "home") {
    body = (
      <HomeScreen
        onSelect={(cropPart: CropPart) =>
          setSession((s) => ({ ...s, cropPart, step: "create" }))
        }
        onExit={() => void exitToTomatoDoc()}
      />
    );
  } else if (session.step === "create" && session.cropPart) {
    body = (
      <CreateCaseScreen
        cropPart={session.cropPart}
        attachWeather={attachWeather}
        onToggleWeather={setAttachWeather}
        onBack={() => {
          if (route?.params?.initialCropPart) {
            void exitToTomatoDoc();
            return;
          }
          setSession((s) => ({ ...s, step: "home", cropPart: null, caseData: null }));
        }}
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
  } else if (session.step === "upload" && session.cropPart && session.caseData) {
    body = (
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
  } else if (session.step === "result" && session.caseData && latestObservation) {
    const observationNumber = session.observations.length;
    const previousObservation =
      observationNumber > 1 ? session.observations[observationNumber - 2] : null;
    body = (
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
  } else if (session.step === "overview" && session.cropPart && session.caseData) {
    body = (
      <OverallMonitoringScreen
        cropPart={session.cropPart}
        caseId={session.caseData.case_id}
        status={session.status}
        observations={session.observations}
        imageUris={session.imageUris}
        onRestart={resetFlow}
        onExit={() => void exitToTomatoDoc()}
      />
    );
  } else {
    body = (
      <HomeScreen
        onSelect={(cropPart: CropPart) =>
          setSession((s) => ({ ...s, cropPart, step: "create" }))
        }
        onExit={() => void exitToTomatoDoc()}
      />
    );
  }

  return (
    <MonitoringThemeProvider cropPart={session.cropPart}>
      {body}
    </MonitoringThemeProvider>
  );
}
