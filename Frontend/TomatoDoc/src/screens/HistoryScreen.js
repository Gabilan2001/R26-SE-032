import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import {
  Animated,
  FlatList,
  Pressable,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  Dimensions,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import { AuthContext } from '../context/AuthContext';
import { UIThemeContext } from '../context/UIThemeContext';
import { getHistory } from '../api/historyApi';
import { getFruitHistory } from '../api/fruitHistoryApi';
import { formatDateTime } from '../utils/formatters';

const { width } = Dimensions.get('window');

// ── Tokens ────────────────────────────────────────────────────────────────────
const C = {
  bg:           '#0f0f0f',
  surface:      '#1a1a1a',
  surface2:     '#222222',
  accent:       '#c8f135',
  accentDim:    'rgba(200,241,53,0.10)',
  accentBorder: 'rgba(200,241,53,0.22)',
  text:         '#f0f0f0',
  muted:        '#555555',
  border:       'rgba(255,255,255,0.07)',
  danger:       '#ff5c5c',
  dangerDim:    'rgba(255,92,92,0.10)',
  dangerBorder: 'rgba(255,92,92,0.18)',
  warn:         '#f5a623',
  warnDim:      'rgba(245,166,35,0.10)',
  warnBorder:   'rgba(245,166,35,0.20)',
  success:      '#4adf6f',
  successDim:   'rgba(74,223,111,0.10)',
  successBorder:'rgba(74,223,111,0.20)',
  glass:        'rgba(255,255,255,0.04)',
  glassBorder:  'rgba(255,255,255,0.06)',
};

// ── Status helpers ────────────────────────────────────────────────────────────
const getStatus = (className, mode) => {
  if (mode === 'fruit') {
    return className === 'Healthy_Tomato' || className === 'Healthy' ? 'healthy' : 'disease';
  }
  return className === 'Healthy' ? 'healthy' : 'deficiency';
};

const STATUS_META = {
  healthy:    { label: 'Healthy',     color: C.success, dim: C.successDim, border: C.successBorder, emoji: '✅', accentColor: C.success },
  disease:    { label: 'Disease',     color: C.danger,  dim: C.dangerDim,  border: C.dangerBorder,  emoji: '🍅', accentColor: C.danger },
  deficiency: { label: 'Deficiency',  color: C.warn,    dim: C.warnDim,    border: C.warnBorder,    emoji: '🍃', accentColor: C.warn },
};

// ── Components ──

function GlassCard({ children, style }) {
  return (
    <View style={[styles.glassCard, style]}>
      <LinearGradient
        colors={['rgba(255,255,255,0.04)', 'rgba(255,255,255,0.01)']}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />
      {children}
    </View>
  );
}

function SummaryCard({ num, label, numColor, delay = 0 }) {
  const op = useRef(new Animated.Value(0)).current;
  const y  = useRef(new Animated.Value(15)).current;
  const scale = useRef(new Animated.Value(0.9)).current;
  
  useEffect(() => {
    Animated.parallel([
      Animated.timing(op, { toValue: 1, duration: 400, delay, useNativeDriver: true }),
      Animated.spring(y,  { toValue: 0, delay, useNativeDriver: true }),
      Animated.spring(scale, { toValue: 1, delay, useNativeDriver: true }),
    ]).start();
  }, [num]);
  
  return (
    <Animated.View style={[
      styles.sumCard,
      { 
        opacity: op, 
        transform: [{ translateY: y }, { scale }] 
      }
    ]}>
      <LinearGradient
        colors={['rgba(255,255,255,0.03)', 'rgba(255,255,255,0.01)']}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />
      <Text style={[styles.sumNum, { color: numColor }]}>{num}</Text>
      <Text style={styles.sumLabel}>{label}</Text>
    </Animated.View>
  );
}

function HistoryItem({ item, mode, onPress, index }) {
  const status = getStatus(item.class_name, mode);
  const meta   = STATUS_META[status];

  const op    = useRef(new Animated.Value(0)).current;
  const slideX= useRef(new Animated.Value(-20)).current;
  const scale = useRef(new Animated.Value(0.95)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(op,     { toValue: 1, duration: 400, delay: index * 40, useNativeDriver: true }),
      Animated.spring(slideX, { toValue: 0, delay: index * 40, useNativeDriver: true }),
      Animated.spring(scale,  { toValue: 1, delay: index * 40, useNativeDriver: true }),
    ]).start();
  }, []);

  const onPressIn  = () => Animated.spring(scale, { toValue: 0.97, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(scale, { toValue: 1,    useNativeDriver: true }).start();

  return (
    <Animated.View style={[
      { opacity: op, transform: [{ translateX: slideX }] }
    ]}>
      <Pressable
        style={[styles.histCard, { transform: [{ scale }] }]}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        onPress={onPress}
      >
        <LinearGradient
          colors={['rgba(255,255,255,0.03)', 'rgba(255,255,255,0.01)']}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        />
        
        <View style={[styles.histAccentBar, { backgroundColor: meta.accentColor }]} />

        <View style={[styles.histThumb, { backgroundColor: meta.dim, borderColor: meta.border }]}>
          <Text style={{ fontSize: 24 }}>{meta.emoji}</Text>
        </View>

        <View style={styles.histBody}>
          <Text style={styles.histName} numberOfLines={1}>{item.class_name}</Text>
          <View style={styles.histMetaRow}>
            <View style={styles.histConfidence}>
              <View style={[styles.histConfDot, { backgroundColor: meta.color }]} />
              <Text style={styles.histConf}>{item.confidence}%</Text>
            </View>
            <Text style={styles.histDate}>{formatDateTime(item.created_at)}</Text>
          </View>
        </View>

        <View style={styles.histBadge}>
          <Text style={[styles.histBadgeTxt, { color: meta.color }]}>{meta.label}</Text>
        </View>
      </Pressable>
    </Animated.View>
  );
}

function EmptyState({ query }) {
  return (
    <View style={styles.empty}>
      <View style={styles.emptyIconWrap}>
        <Text style={styles.emptyIcon}>{query ? '🔍' : '📊'}</Text>
      </View>
      <Text style={styles.emptyTxt}>
        {query
          ? `No results found for "${query}"`
          : 'No scan history yet'}
      </Text>
      <Text style={styles.emptySub}>
        {query
          ? 'Try a different search term'
          : 'Start your first scan to track your plants'}
      </Text>
    </View>
  );
}

// ── Main Screen ──

export default function HistoryScreen({ navigation, route }) {
  const { token }            = useContext(AuthContext);
  const { presentationMode } = useContext(UIThemeContext);

  const [history, setHistory] = useState([]);
  const [mode,    setMode]    = useState(route?.params?.initialMode === 'fruit' ? 'fruit' : 'nutrient');
  const [query,   setQuery]   = useState('');
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const modeRef = useRef(mode);

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  const nutrientScale = useRef(new Animated.Value(1)).current;
  const fruitScale    = useRef(new Animated.Value(1)).current;
  const headerOp = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(headerOp, {
      toValue: 1,
      duration: 500,
      useNativeDriver: true,
    }).start();
  }, []);

  const switchMode = (m) => {
    if (m === mode) return;
    const anim = m === 'nutrient' ? nutrientScale : fruitScale;
    Animated.sequence([
      Animated.timing(anim, { toValue: 0.92, duration: 80, useNativeDriver: true }),
      Animated.spring(anim, { toValue: 1, useNativeDriver: true }),
    ]).start();
    setMode(m);
    setQuery('');
  };

  const fetchData = useCallback(async (showRefreshing = false) => {
    if (!token) {
      setHistory([]);
      setError('Log in to view your scan history.');
      return;
    }

    const currentMode = modeRef.current;

    if (showRefreshing) setRefreshing(true);
    else setLoading(true);
    setError('');
    
    try {
      const res = currentMode === 'fruit'
        ? await getFruitHistory(token)
        : await getHistory(token);
      setHistory(res.data.history || []);
    } catch (e) {
      setHistory([]);
      setError(
        e?.response?.data?.message ||
        e?.response?.data?.msg ||
        e?.message ||
        'Could not load history.'
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useFocusEffect(
    useCallback(() => {
      fetchData();
    }, [fetchData])
  );

  useEffect(() => {
    fetchData();
  }, [mode, fetchData]);

  const onPressItem = useCallback((item) => {
    if (mode === 'fruit') {
      navigation.navigate('FruitResult', {
        result: {
          class:       item.class_name,
          confidence:  item.confidence,
          warning:     item.warning,
          description: item.description,
          symptoms:    item.symptoms,
          solution:    item.solution,
          treatment:   item.treatment,
        },
        imageUri: item.image_uri || null,
      });
    } else {
      navigation.navigate('Result', {
        result: {
          class:       item.class_name,
          confidence:  item.confidence,
          description: item.description,
          symptoms:    item.symptoms,
          solution:    item.solution,
          fertilizer:  item.fertilizer,
        },
        imageUri: item.image_uri || null,
      });
    }
  }, [mode, navigation]);

  const filtered = history.filter(h =>
    h.class_name?.toLowerCase().includes(query.toLowerCase())
  );

  const totalHealthy = filtered.filter(h => getStatus(h.class_name, mode) === 'healthy').length;
  const totalIssues  = filtered.filter(h => getStatus(h.class_name, mode) !== 'healthy').length;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />

      <Animated.View style={[styles.header, { opacity: headerOp }]}>
        <Text style={[styles.title, presentationMode && { fontSize: 28 }]}>History</Text>
        <Text style={styles.headerSub}>{filtered.length} records</Text>
      </Animated.View>

      <View style={styles.searchWrap}>
        <Text style={styles.searchIcon}>🔍</Text>
        <TextInput
          style={styles.searchInput}
          placeholder="Search records..."
          placeholderTextColor={C.muted}
          value={query}
          onChangeText={setQuery}
          selectionColor={C.accent}
        />
        {!!query && (
          <TouchableOpacity onPress={() => setQuery('')} style={styles.clearBtn}>
            <Text style={styles.clearBtnTxt}>✕</Text>
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.modeRow}>
        {['nutrient', 'fruit'].map((m) => (
          <Animated.View
            key={m}
            style={[
              styles.modeWrap,
              { transform: [{ scale: m === 'nutrient' ? nutrientScale : fruitScale }] }
            ]}
          >
            <TouchableOpacity
              style={[styles.modeChip, mode === m && styles.modeChipActive]}
              onPress={() => switchMode(m)}
              activeOpacity={0.85}
            >
              {mode === m && (
                <LinearGradient
                  colors={['rgba(200,241,53,0.08)', 'rgba(200,241,53,0.02)']}
                  style={StyleSheet.absoluteFill}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                />
              )}
              <Text style={[styles.modeChipTxt, mode === m && styles.modeChipTxtActive]}>
                {m === 'nutrient' ? 'Nutrient' : 'Fruit Disease'}
              </Text>
            </TouchableOpacity>
          </Animated.View>
        ))}
      </View>

      <View style={styles.summaryRow}>
        <SummaryCard 
          num={filtered.length} 
          label="Total" 
          numColor={C.accent}  
          delay={0}  
        />
        <SummaryCard 
          num={totalHealthy}    
          label="Healthy" 
          numColor={C.success} 
          delay={80} 
        />
        <SummaryCard 
          num={totalIssues}     
          label="Issues"  
          numColor={C.danger}  
          delay={160}
        />
      </View>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionLabel}>
          Recent {mode === 'nutrient' ? 'Nutrient' : 'Fruit Disease'} Scans
        </Text>
        <Text style={styles.sectionCount}>{filtered.length}</Text>
      </View>

      {!!error && !loading && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <FlatList
        data={filtered}
        key={mode}
        keyExtractor={item => String(item._id)}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshing={refreshing}
        onRefresh={() => fetchData(true)}
        renderItem={({ item, index }) => (
          <HistoryItem
            item={item}
            mode={mode}
            index={index}
            onPress={() => onPressItem(item)}
          />
        )}
        ListEmptyComponent={<EmptyState query={query} />}
      />
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: { 
    flex: 1, 
    backgroundColor: C.bg,
  },

  // ── Header ──
  header: {
    paddingHorizontal: 18,
    paddingTop: 58,
    paddingBottom: 14,
    gap: 2,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: C.text,
  },
  headerSub: {
    fontSize: 12,
    color: C.muted,
    fontWeight: '500',
  },

  // ── Search ──
  searchWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 18,
    marginBottom: 14,
    backgroundColor: C.surface,
    borderWidth: 1.5,
    borderColor: C.border,
    borderRadius: 14,
    overflow: 'hidden',
  },
  searchIcon: {
    paddingLeft: 14,
    fontSize: 14,
    opacity: 0.5,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 13,
    paddingHorizontal: 10,
    color: C.text,
    fontSize: 14,
    fontWeight: '500',
  },
  clearBtn: {
    paddingRight: 14,
    paddingLeft: 6,
  },
  clearBtnTxt: {
    fontSize: 14,
    color: C.muted,
    fontWeight: '600',
  },

  // ── Mode Toggle ──
  modeRow: {
    flexDirection: 'row',
    gap: 10,
    marginHorizontal: 18,
    marginBottom: 16,
  },
  modeWrap: {
    flex: 1,
  },
  modeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: C.border,
    backgroundColor: C.surface,
    overflow: 'hidden',
  },
  modeChipActive: {
    borderColor: C.accentBorder,
  },
  modeIcon: {
    fontSize: 16,
  },
  modeChipTxt: {
    fontSize: 13,
    fontWeight: '700',
    color: C.muted,
  },
  modeChipTxtActive: {
    color: C.accent,
  },

  // ── Glass Card ──
  glassCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 16,
    overflow: 'hidden',
  },

  // ── Summary ──
  summaryRow: {
    flexDirection: 'row',
    gap: 10,
    marginHorizontal: 18,
    marginBottom: 18,
  },
  sumCard: {
    flex: 1,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 16,
    padding: 14,
    alignItems: 'center',
    overflow: 'hidden',
    position: 'relative',
  },
  sumNum: {
    fontSize: 22,
    fontWeight: '800',
    lineHeight: 28,
  },
  sumLabel: {
    fontSize: 10,
    color: C.muted,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginTop: 2,
  },

  // ── Section ──
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginHorizontal: 18,
    marginBottom: 12,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: C.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  sectionCount: {
    fontSize: 12,
    color: C.accent,
    fontWeight: '600',
    backgroundColor: C.accentDim,
    paddingHorizontal: 10,
    paddingVertical: 2,
    borderRadius: 100,
  },

  // ── Error ──
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginHorizontal: 18,
    marginBottom: 12,
    padding: 12,
    backgroundColor: C.dangerDim,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.dangerBorder,
  },
  errorIcon: {
    fontSize: 16,
  },
  errorText: {
    flex: 1,
    fontSize: 12,
    color: C.danger,
    lineHeight: 18,
  },

  // ── List ──
  listContent: {
    paddingHorizontal: 18,
    paddingBottom: 40,
    paddingTop: 2,
  },

  // ── History Item ──
  histCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 18,
    padding: 14,
    marginBottom: 10,
    overflow: 'hidden',
    position: 'relative',
  },
  histAccentBar: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    borderTopLeftRadius: 18,
    borderBottomLeftRadius: 18,
  },
  histThumb: {
    width: 50,
    height: 50,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  histBody: {
    flex: 1,
    minWidth: 0,
    gap: 4,
  },
  histName: {
    fontSize: 14,
    fontWeight: '700',
    color: C.text,
  },
  histMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  histConfidence: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  histConfDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
  },
  histConf: {
    fontSize: 11,
    color: C.muted,
    fontWeight: '600',
  },
  histDate: {
    fontSize: 10,
    color: C.muted,
    opacity: 0.7,
  },
  histBadge: {
    borderRadius: 100,
    paddingHorizontal: 10,
    paddingVertical: 4,
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  histBadgeTxt: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.3,
  },

  // ── Empty ──
  empty: {
    alignItems: 'center',
    paddingVertical: 60,
    gap: 12,
  },
  emptyIconWrap: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderWidth: 1,
    borderColor: C.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  emptyIcon: {
    fontSize: 36,
    opacity: 0.5,
  },
  emptyTxt: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
    textAlign: 'center',
  },
  emptySub: {
    fontSize: 13,
    color: C.muted,
    textAlign: 'center',
    lineHeight: 20,
  },
});