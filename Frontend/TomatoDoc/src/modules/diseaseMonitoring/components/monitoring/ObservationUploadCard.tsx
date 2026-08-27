import React, { useEffect, useMemo, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  Image,
  ActivityIndicator,
  Animated,
  Easing,
} from "react-native";
import type { CropPart } from "../../api/observations";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";
import type { MonitoringPalette } from "../../theme/colors";

type Props = {
  cropPart: CropPart;
  observationNumber: number;
  dateLabel: string;
  previewUri: string | null;
  validationMessage: string | null;
  loading: boolean;
  disabled?: boolean;
  onPick: () => void;
  onUpload: () => void;
};

function CornerBrackets({ color }: { color: string }) {
  const size = 22;
  const t = 14;
  const corner = (pos: {
    top?: number;
    bottom?: number;
    left?: number;
    right?: number;
  }) => ({
    position: "absolute" as const,
    width: size,
    height: size,
    borderColor: color,
    ...(pos.top !== undefined && { top: pos.top }),
    ...(pos.bottom !== undefined && { bottom: pos.bottom }),
    ...(pos.left !== undefined && { left: pos.left }),
    ...(pos.right !== undefined && { right: pos.right }),
    borderTopWidth: pos.top !== undefined ? 2.5 : 0,
    borderBottomWidth: pos.bottom !== undefined ? 2.5 : 0,
    borderLeftWidth: pos.left !== undefined ? 2.5 : 0,
    borderRightWidth: pos.right !== undefined ? 2.5 : 0,
  });

  return (
    <>
      <View style={corner({ top: t, left: t })} />
      <View style={corner({ top: t, right: t })} />
      <View style={corner({ bottom: t, left: t })} />
      <View style={corner({ bottom: t, right: t })} />
    </>
  );
}

function ScanLine({ color }: { color: string }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(anim, {
          toValue: 1,
          duration: 2400,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(anim, {
          toValue: 0,
          duration: 2400,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [anim]);

  const translateY = anim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 160],
  });

  return (
    <Animated.View
      pointerEvents="none"
      style={[
        {
          position: "absolute",
          left: 18,
          right: 18,
          top: 24,
          height: 1.5,
          backgroundColor: color,
          opacity: 0.75,
        },
        { transform: [{ translateY }] },
      ]}
    />
  );
}

/**
 * TomatoDoc-style upload viewfinder (leaf lime / fruit coral). Logic unchanged.
 */
export function ObservationUploadCard({
  cropPart,
  observationNumber,
  dateLabel,
  previewUri,
  validationMessage,
  loading,
  disabled,
  onPick,
  onUpload,
}: Props) {
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);
  const isFruit = cropPart === "FRUIT";
  const placeHint = isFruit
    ? "Place tomato fruit\ninside the frame"
    : "Place leaf inside the frame";
  const emoji = isFruit ? "🍅" : "🍃";

  return (
    <View style={styles.wrap}>
      <Text style={styles.kicker}>OBSERVATION {observationNumber}</Text>
      <Text style={styles.date}>{dateLabel}</Text>

      <View style={[styles.viewfinder, isFruit && styles.viewfinderFruit]}>
        <CornerBrackets color={p.accent} />
        {!previewUri ? <ScanLine color={p.accent} /> : null}

        {previewUri ? (
          <Image source={{ uri: previewUri }} style={styles.preview} resizeMode="cover" />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderEmoji}>{emoji}</Text>
            <Text style={styles.placeholderTxt}>{placeHint}</Text>
          </View>
        )}

        {loading ? (
          <View style={styles.loadingOverlay}>
            <ActivityIndicator color={p.accent} size="large" />
          </View>
        ) : null}
      </View>

      <Text style={styles.sectionLabel}>REFERENCE QUALITY SAMPLES</Text>

      {validationMessage ? (
        <Text style={styles.validation}>{validationMessage}</Text>
      ) : null}

      <View style={styles.actions}>
        <Pressable
          style={[styles.actionGallery, disabled && styles.disabled]}
          onPress={onPick}
          disabled={disabled || loading}
        >
          <Text style={styles.actionGalleryTxt}>
            {previewUri ? "Change image" : "Gallery"}
          </Text>
        </Pressable>
        <Pressable
          style={[styles.actionCamera, (!previewUri || disabled) && styles.disabled]}
          onPress={onUpload}
          disabled={!previewUri || disabled || loading}
        >
          {loading ? (
            <ActivityIndicator color={p.onAccent} />
          ) : (
            <Text style={styles.actionCameraTxt}>Upload</Text>
          )}
        </Pressable>
      </View>
    </View>
  );
}

function makeStyles(p: MonitoringPalette) {
  return StyleSheet.create({
    wrap: { marginTop: 8 },
    kicker: {
      color: p.textMuted,
      fontSize: 11,
      letterSpacing: 1.2,
      fontWeight: "700",
    },
    date: { color: p.textPrimary, fontSize: 16, fontWeight: "700", marginTop: 4 },
    viewfinder: {
      marginTop: 14,
      height: 220,
      borderRadius: 18,
      backgroundColor: "#0a1400",
      borderWidth: 1.5,
      borderColor: p.accentBorder,
      overflow: "hidden",
      alignItems: "center",
      justifyContent: "center",
    },
    viewfinderFruit: {
      backgroundColor: "#1a0a0a",
    },
    preview: {
      ...StyleSheet.absoluteFillObject,
      width: "100%",
      height: "100%",
    },
    placeholder: {
      alignItems: "center",
      justifyContent: "center",
      paddingHorizontal: 24,
      zIndex: 1,
    },
    placeholderEmoji: { fontSize: 36, marginBottom: 8 },
    placeholderTxt: {
      color: p.textMuted,
      fontSize: 12,
      textAlign: "center",
      lineHeight: 18,
    },
    loadingOverlay: {
      ...StyleSheet.absoluteFillObject,
      backgroundColor: "rgba(0,0,0,0.45)",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 2,
    },
    sectionLabel: {
      marginTop: 14,
      fontSize: 10,
      fontWeight: "700",
      color: p.textMuted,
      letterSpacing: 0.8,
    },
    validation: { color: p.infoText, marginTop: 10, lineHeight: 18 },
    actions: {
      flexDirection: "row",
      gap: 10,
      marginTop: 14,
    },
    actionGallery: {
      flex: 1,
      backgroundColor: p.accent,
      borderRadius: 14,
      paddingVertical: 14,
      alignItems: "center",
    },
    actionGalleryTxt: { color: p.onAccent, fontWeight: "800", fontSize: 13 },
    actionCamera: {
      flex: 1,
      backgroundColor: p.bgElevated,
      borderRadius: 14,
      paddingVertical: 14,
      alignItems: "center",
      borderWidth: 1,
      borderColor: p.cardBorder,
    },
    actionCameraTxt: { color: p.textPrimary, fontWeight: "700", fontSize: 13 },
    disabled: { opacity: 0.45 },
  });
}
