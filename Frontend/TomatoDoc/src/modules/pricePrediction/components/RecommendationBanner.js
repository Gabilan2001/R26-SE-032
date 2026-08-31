import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { C } from '../constants/priceTheme';

export function getAdviceContent(data) {
  if (!data) {
    return {
      title: 'Market Analysis in Progress',
      textEn: 'Analyzing historical prices and regional weather signals...',
      textSi: 'වෙළඳපොළ තොරතුරු විශ්ලේෂණය කෙරෙමින් පවතී...',
      bannerStyle: styles.bannerStable,
      iconName: 'chart-line',
      iconColor: C.blue,
    };
  }

  const code = String(data.action_code || '').toUpperCase();
  const peakDay = data.peak_day || data.optimal_sell_day || 1;
  const peakPrice = data.peak_price_lkr || data.optimal_sell_price_lkr || data.day1_forecast_lkr;
  const termPrice = data.day14_forecast_lkr;
  const trend = String(data.trend || '').toUpperCase();

  // RULE 1: Anomaly
  if (
    code === 'MONITOR' ||
    (!code && String(data.recommendation || '').toUpperCase().includes('MONITOR'))
  ) {
    return {
      title: '⚠️ MONITOR — Market Anomaly Detected',
      textEn:
        'Current market prices are behaving unpredictably right now. Keep a close eye on daily physical market offers before committing to a large sale.',
      textSi:
        'වෙළඳපොළ මිල ගණන් දැනට අවිනිශ්චිත තත්ත්වයක පවතී. විශාල වශයෙන් අලෙවි කිරීමට පෙර දිනපතා වෙළඳපොළ තොරතුරු පරීක්ෂා කරන්න.',
      bannerStyle: styles.bannerMonitor,
      iconName: 'alert-circle-outline',
      iconColor: C.amber,
    };
  }

  // RULE 2 & 3: SELL NOW
  if (
    code === 'SELL_NOW' ||
    (!code &&
      String(data.recommendation || '').toUpperCase().startsWith('SELL NOW') &&
      !String(data.recommendation || '').toUpperCase().includes('HOLD'))
  ) {
    if (
      peakDay <= 2 &&
      (trend === 'DECLINING' || (data.terminal_change_pct != null && data.terminal_change_pct < 0))
    ) {
      return {
        title: `⚡ SELL NOW — Peak in Next ${peakDay === 1 ? '1–2 Days' : 'Day ' + peakDay}`,
        textEn: `Prices are projected to peak near ${Math.round(
          peakPrice
        )} LKR/kg around Day ${peakDay} and soften thereafter (reaching ~${Math.round(
          termPrice
        )} LKR/kg by Day 14). Selling immediately or near this early peak is recommended.`,
        textSi: `ඉදිරි දින 1–2 තුළ තක්කාලි මිල උපරිම මට්ටමට (~රු. ${Math.round(
          peakPrice
        )}) ළඟා වී ඉන්පසු පහත වැටෙනු ඇතැයි අපේක්ෂා කෙරේ. වැඩි ලාභයක් ලබා ගැනීමට වහාම අලෙවි කිරීම සුදුසුය.`,
        bannerStyle: styles.bannerSell,
        iconName: 'lightning-bolt',
        iconColor: C.red,
      };
    }
    return {
      title: '🚨 SELL NOW — Prices Softening',
      textEn: `Prices are projected to decline across the coming days (down to ~${Math.round(
        termPrice
      )} LKR/kg). Selling immediately is recommended to protect your earnings before prices drop further.`,
      textSi:
        'ඉදිරි දින කිහිපය තුළ තක්කාලි මිල පහළ යාමට ඉඩ ඇත. මිල තවත් අඩුවීමට පෙර වහාම අලෙවි කිරීම සුදුසුය.',
      bannerStyle: styles.bannerSell,
      iconName: 'trending-down',
      iconColor: C.red,
    };
  }

  // RULE 4 & 5: HOLD
  if (code === 'HOLD' || (!code && String(data.recommendation || '').toUpperCase() === 'HOLD')) {
    if (peakDay <= 5) {
      return {
        title: `📈 HOLD — Optimal Selling Window Near Day ${peakDay}`,
        textEn: `Prices are projected to rise toward a peak of ~${Math.round(
          peakPrice
        )} LKR/kg around Day ${peakDay}. Timing sales near this window is recommended if harvested tomatoes can be safely managed without spoilage (3–5 day shelf life).`,
        textSi: `ඉදිරි දින ${peakDay} තුළ තක්කාලි මිල ඉහළ ගොස් උපරිම මට්ටමට (~රු. ${Math.round(
          peakPrice
        )}) ළඟා වනු ඇතැයි අපේක්ෂා කෙරේ. වැඩි ලාභයක් ලබා ගැනීම සඳහා අලෙවිය දින කිහිපයක් ප්‍රමාද කිරීම සුදුසුය.`,
        bannerStyle: styles.bannerHold,
        iconName: 'trending-up',
        iconColor: C.emerald,
      };
    }
    return {
      title: `📈 HOLD — Higher Prices Projected Near Day ${peakDay}`,
      textEn: `Higher market prices (up to ~${Math.round(
        peakPrice
      )} LKR/kg) are projected later around Day ${peakDay}. Plan staggered field harvesting rather than holding already-harvested crop in ambient storage for extended periods.`,
      textSi: `ඉදිරි දින ${peakDay} පමණ වන විට ඉහළ මිලක් (~රු. ${Math.round(
        peakPrice
      )}) අපේක්ෂා කෙරේ. තක්කාලි කල්තබා ගත නොහැකි බැවින් අස්වනු නෙළීම සැලසුම් සහගතව සිදු කරන්න.`,
      bannerStyle: styles.bannerHold,
      iconName: 'arrow-top-right',
      iconColor: C.emerald,
    };
  }

  // RULE 6: STABLE
  return {
    title: '➡️ STABLE — Sell at Convenience',
    textEn:
      'Prices are projected to remain relatively steady within normal daily market fluctuations. You can sell at your convenience according to harvest readiness.',
    textSi:
      'තක්කාලි මිල සාමාන්‍ය මට්ටමේ ස්ථාවරව පවතිනු ඇතැයි අපේක්ෂා කෙරේ. අස්වැන්නේ තත්ත්වය අනුව ඔබට පහසු පරිදි අලෙවි කළ හැක.',
    bannerStyle: styles.bannerStable,
    iconName: 'swap-horizontal',
    iconColor: C.blue,
  };
}

export default function RecommendationBanner({ data }) {
  const content = getAdviceContent(data);

  return (
    <View style={[styles.container, content.bannerStyle]}>
      <View style={styles.headerRow}>
        <MaterialCommunityIcons name={content.iconName} size={22} color={content.iconColor} />
        <Text style={styles.title}>{content.title}</Text>
      </View>
      <Text style={styles.textEn}>{content.textEn}</Text>
      <View style={styles.divider} />
      <Text style={styles.textSi}>{content.textSi}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginBottom: 14,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1.5,
  },
  bannerSell: {
    backgroundColor: C.redDim,
    borderColor: C.redBorder,
  },
  bannerHold: {
    backgroundColor: C.emeraldDim,
    borderColor: C.emeraldBorder,
  },
  bannerStable: {
    backgroundColor: C.blueDim,
    borderColor: C.blueBorder,
  },
  bannerMonitor: {
    backgroundColor: C.amberDim,
    borderColor: C.amberBorder,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  title: {
    fontSize: 14,
    fontWeight: '800',
    color: C.text,
    flex: 1,
    letterSpacing: 0.2,
  },
  textEn: {
    fontSize: 12,
    color: C.text,
    lineHeight: 18,
    fontWeight: '500',
  },
  divider: {
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    marginVertical: 8,
  },
  textSi: {
    fontSize: 11.5,
    color: C.textSecondary,
    lineHeight: 17,
  },
});
