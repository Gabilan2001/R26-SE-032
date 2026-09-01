import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { C } from '../constants/priceTheme';

export function formatPriceRange(val, halfBandPct = 0.04) {
  if (val == null || isNaN(val)) return '—';
  const num = parseFloat(val);
  const delta = Math.max(5, Math.round(num * halfBandPct));
  const low = Math.round(num - delta);
  const high = Math.round(num + delta);
  return `${low} – ${high}`;
}

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

  const peakRange = formatPriceRange(peakPrice, 0.035);
  const termRange = formatPriceRange(termPrice, 0.05);

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

  // RULE 2 & 3: SELLING SUGGESTED
  if (
    code === 'SELL_NOW' ||
    (!code &&
      (String(data.recommendation || '').toUpperCase().includes('SELL') || String(data.recommendation || '').toUpperCase().includes('SELLING')) &&
      !String(data.recommendation || '').toUpperCase().includes('HOLD'))
  ) {
    if (
      peakDay <= 2 &&
      (trend === 'DECLINING' || (data.terminal_change_pct != null && data.terminal_change_pct < 0))
    ) {
      return {
        title: `⚡ Selling Suggested — Peak in Next ${peakDay === 1 ? '1–2 Days' : 'Day ' + peakDay}`,
        textEn: `Prices are projected to peak in the range of ${peakRange} LKR/kg around Day ${peakDay} and soften thereafter (reaching ${termRange} LKR/kg by Day 14). Selling during this early peak is suggested.`,
        textSi: `ඉදිරි දින 1–2 තුළ තක්කාලි මිල උපරිම මට්ටමට (~රු. ${peakRange}) ළඟා වී ඉන්පසු පහත වැටෙනු ඇතැයි අපේක්ෂා කෙරේ. වැඩි ලාභයක් ලබා ගැනීමට අස්වැන්න අලෙවි කිරීම සුදුසු වේ.`,
        bannerStyle: styles.bannerSell,
        iconName: 'lightning-bolt',
        iconColor: C.red,
      };
    }
    return {
      title: '🚨 Selling Suggested — Prices Softening',
      textEn: `Prices are projected to decline across the coming days (down to ${termRange} LKR/kg). Selling is suggested to protect your earnings before prices drop further.`,
      textSi:
        'ඉදිරි දින කිහිපය තුළ තක්කාලි මිල පහළ යාමට ඉඩ ඇත. මිල තවත් අඩුවීමට පෙර අස්වැන්න අලෙවි කිරීම සුදුසු වේ.',
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
        textEn: `Prices are projected to rise toward an expected range of ${peakRange} LKR/kg around Day ${peakDay}. Timing sales near this window is recommended if harvested tomatoes can be safely managed without spoilage (3–5 day shelf life).`,
        textSi: `ඉදිරි දින ${peakDay} තුළ තක්කාලි මිල ඉහළ ගොස් උපරිම මට්ටමට (~රු. ${peakRange}) ළඟා වනු ඇතැයි අපේක්ෂා කෙරේ. වැඩි ලාභයක් ලබා ගැනීම සඳහා අලෙවිය දින කිහිපයක් ප්‍රමාද කිරීම සුදුසුය.`,
        bannerStyle: styles.bannerHold,
        iconName: 'trending-up',
        iconColor: C.emerald,
      };
    }
    return {
      title: `📈 HOLD — Higher Prices Projected Near Day ${peakDay}`,
      textEn: `Higher market prices (${peakRange} LKR/kg) are projected later around Day ${peakDay}. Plan staggered field harvesting rather than holding already-harvested crop in ambient storage for extended periods.`,
      textSi: `ඉදිරි දින ${peakDay} පමණ වන විට ඉහළ මිලක් (~රු. ${peakRange}) අපේක්ෂා කෙරේ. තක්කාලි කල්තබා ගත නොහැකි බැවින් අස්වනු නෙළීම සැලසුම් සහගතව සිදු කරන්න.`,
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
    <View style={styles.wrapper}>
      {/* Main Recommendation Card */}
      <View style={[styles.container, content.bannerStyle]}>
        <View style={styles.headerRow}>
          <MaterialCommunityIcons name={content.iconName} size={22} color={content.iconColor} />
          <Text style={styles.title}>{content.title}</Text>
        </View>
        <Text style={styles.textEn}>{content.textEn}</Text>
        <View style={styles.divider} />
        <Text style={styles.textSi}>{content.textSi}</Text>
      </View>

      {/* Advisory Disclaimer Badge */}
      <View style={styles.disclaimerCard}>
        <Text style={styles.disclaimerEn}>
          ⚠️ AI Market Advisory: Forecasts indicate general price direction. Always verify local spot offers at your Dedicated Economic Centre before harvesting large quantities.
        </Text>
        <View style={styles.disclaimerDivider} />
        <Text style={styles.disclaimerSi}>
          ⚠️ වෙළඳපල උපදෙස: මෙම මිල ගණන් වෙළඳපල ප්රවණතා මත පදනම් වේ. අස්වනු නෙලීමට පෙර ප්රාදේශීය වෙළෙඳුන්ගෙන් තහවුරු කරගන්න.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    marginHorizontal: 16,
    marginBottom: 14,
  },
  container: {
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
  disclaimerCard: {
    marginTop: 8,
    backgroundColor: 'rgba(245, 158, 11, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(245, 158, 11, 0.20)',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  disclaimerEn: {
    fontSize: 10.5,
    color: C.amber,
    fontWeight: '600',
    lineHeight: 15,
  },
  disclaimerDivider: {
    height: 1,
    backgroundColor: 'rgba(245, 158, 11, 0.12)',
    marginVertical: 6,
  },
  disclaimerSi: {
    fontSize: 10,
    color: C.textSecondary,
    lineHeight: 15,
  },
});
