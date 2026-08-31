import React, { useState } from 'react';
import {
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { C, SUPPORTED_MARKETS } from '../constants/priceTheme';

export default function MarketSelector({ selectedMarket, selectedType, onSelect }) {
  const [modalVisible, setModalVisible] = useState(false);

  const currentSelection =
    SUPPORTED_MARKETS.find(
      (m) => m.market === selectedMarket && m.type === selectedType
    ) || SUPPORTED_MARKETS[0];

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.selectorBtn}
        onPress={() => setModalVisible(true)}
        activeOpacity={0.75}
      >
        <View style={styles.leftGroup}>
          <View style={styles.iconWrap}>
            <MaterialCommunityIcons name="storefront-outline" size={18} color={C.amber} />
          </View>
          <View>
            <Text style={styles.label}>Selected Market & Series</Text>
            <Text style={styles.selectedValue}>{currentSelection.label}</Text>
          </View>
        </View>
        <MaterialCommunityIcons name="chevron-down" size={20} color={C.amber} />
      </TouchableOpacity>

      <Modal
        visible={modalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableWithoutFeedback onPress={() => setModalVisible(false)}>
          <View style={styles.modalOverlay}>
            <TouchableWithoutFeedback>
              <View style={styles.modalContent}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>Choose Market Location</Text>
                  <TouchableOpacity
                    onPress={() => setModalVisible(false)}
                    hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                  >
                    <MaterialCommunityIcons name="close" size={22} color={C.muted} />
                  </TouchableOpacity>
                </View>

                <Text style={styles.modalSub}>
                  Select your primary trading hub and retail/wholesale pricing series:
                </Text>

                <View style={styles.optionsList}>
                  {SUPPORTED_MARKETS.map((item) => {
                    const isSelected =
                      item.market === selectedMarket && item.type === selectedType;
                    return (
                      <TouchableOpacity
                        key={item.id}
                        style={[
                          styles.optionItem,
                          isSelected && styles.optionItemSelected,
                        ]}
                        onPress={() => {
                          onSelect(item.market, item.type);
                          setModalVisible(false);
                        }}
                        activeOpacity={0.7}
                      >
                        <View style={styles.optionLeft}>
                          <View
                            style={[
                              styles.radioCircle,
                              isSelected && styles.radioCircleSelected,
                            ]}
                          >
                            {isSelected && <View style={styles.radioInner} />}
                          </View>
                          <Text
                            style={[
                              styles.optionText,
                              isSelected && styles.optionTextSelected,
                            ]}
                          >
                            {item.label}
                          </Text>
                        </View>
                        {isSelected && (
                          <MaterialCommunityIcons
                            name="check-circle"
                            size={18}
                            color={C.amber}
                          />
                        )}
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </View>
            </TouchableWithoutFeedback>
          </View>
        </TouchableWithoutFeedback>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginBottom: 12,
  },
  selectorBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.borderLight,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  leftGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: C.amberDim,
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: {
    fontSize: 11,
    color: C.muted,
    fontWeight: '500',
  },
  selectedValue: {
    fontSize: 14,
    fontWeight: '700',
    color: C.text,
    marginTop: 1,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  modalContent: {
    backgroundColor: C.surface,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: C.borderLight,
    padding: 18,
    maxHeight: 400,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  modalSub: {
    fontSize: 12,
    color: C.muted,
    marginBottom: 14,
    lineHeight: 17,
  },
  optionsList: {
    gap: 8,
  },
  optionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: C.surface2,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  optionItemSelected: {
    backgroundColor: C.amberDim,
    borderColor: C.amberBorder,
  },
  optionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  radioCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 1.5,
    borderColor: C.muted,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioCircleSelected: {
    borderColor: C.amber,
  },
  radioInner: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: C.amber,
  },
  optionText: {
    fontSize: 13,
    fontWeight: '600',
    color: C.textSecondary,
  },
  optionTextSelected: {
    color: C.text,
    fontWeight: '700',
  },
});
