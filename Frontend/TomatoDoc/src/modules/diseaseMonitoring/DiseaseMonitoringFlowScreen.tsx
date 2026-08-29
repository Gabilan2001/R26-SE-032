import React, { useEffect, useRef, useState } from "react";
import type {
  CropPart,
  MonitoringCase,
  Observation,
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

  const exitToTomatoDoc = () => {
    appliedInitial.current = false;
    setSession(initialSession);
    setLatestObservation(null);
    setLatestImageUri(null);
    if (navigation.canGoBack()) {
      navigation.goBack();
    } else {
      navigation.navigate("MainTabs");
    }
  };

  const resetFlow = () => {
    setSession(initialSession);
    setLatestObservation(null);
    setLatestImageUri(null);
  };

  let body: React.ReactNode;

  if (session.step === "home") {
    body = (
      <HomeScreen
        onSelect={(cropPart: CropPart) =>
          setSession((s) => ({ ...s, cropPart, step: "create" }))
        }
        onExit={exitToTomatoDoc}
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
            exitToTomatoDoc();
            return;
          }
          setSession((s) => ({ ...s, step: "home", cropPart: null }));
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
        onBack={() =>
          setSession((s) => ({
            ...s,
            step: s.observations.length > 0 ? "result" : "create",
          }))
        }
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
        onBack={() => setSession((s) => ({ ...s, step: "upload" }))}
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
        onExit={exitToTomatoDoc}
      />
    );
  } else {
    body = (
      <HomeScreen
        onSelect={(cropPart: CropPart) =>
          setSession((s) => ({ ...s, cropPart, step: "create" }))
        }
        onExit={exitToTomatoDoc}
      />
    );
  }

  return (
    <MonitoringThemeProvider cropPart={session.cropPart}>
      {body}
    </MonitoringThemeProvider>
  );
}
