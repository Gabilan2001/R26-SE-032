import React, { useContext, useState } from 'react';
import { Alert, Image, Platform, ScrollView, StyleSheet, View } from 'react-native';
import { Button, Text } from 'react-native-paper';
import * as ImagePicker from 'expo-image-picker';
import { predictNutrient } from '../api/scanApi';
import { AuthContext } from '../context/AuthContext';
import { colors } from '../constants/colors';
import LoadingOverlay from '../components/LoadingOverlay';

export default function ScanScreen({ navigation }) {
  const { token } = useContext(AuthContext);
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);

  const pickImage = async (fromCamera = false) => {
    const launcher = fromCamera ? ImagePicker.launchCameraAsync : ImagePicker.launchImageLibraryAsync;
    const res = await launcher({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 0.8 });
    if (!res.canceled) setImage(res.assets[0]);
  };

  const analyze = async () => {
    if (!image) return;
    setLoading(true);
    try {
      const formData = new FormData();
      if (Platform.OS === 'web') {
        const response = await fetch(image.uri);
        const blob = await response.blob();
        const file = new File([blob], 'leaf.jpg', { type: blob.type || 'image/jpeg' });
        formData.append('image', file);
      } else {
        const filename = image.fileName || `leaf-${Date.now()}.jpg`;
        const mimeType = image.mimeType || 'image/jpeg';
        formData.append('image', {
          uri: image.uri,
          name: filename,
          type: mimeType,
        });
      }

      const res = await predictNutrient(formData, token);
      navigation.navigate('Result', { result: res.data, imageUri: image.uri });
    } catch (error) {
      const serverError = error?.response?.data?.error;
      const networkError = error?.message;
      Alert.alert('Analyze failed', serverError || networkError || 'Could not analyze this image.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {loading ? <LoadingOverlay text="Analyzing leaf..." /> : null}
      <Text style={styles.title}>Nutrient Deficiency Scan</Text>
      <Text style={styles.helper}>Take a clear photo of a single tomato leaf.</Text>
      <Button mode="contained" onPress={() => pickImage(false)}>Upload From Gallery</Button>
      <Button mode="outlined" style={styles.mt} onPress={() => pickImage(true)}>Take Photo</Button>
      {image ? <Image source={{ uri: image.uri }} style={styles.preview} /> : null}
      <Button mode="contained" style={styles.mt} onPress={analyze} disabled={!image}>Analyze</Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 16 },
  title: { fontSize: 24, fontWeight: '700', color: colors.primary, marginBottom: 8 },
  helper: { marginBottom: 16, color: colors.text },
  mt: { marginTop: 12 },
  preview: { width: '100%', height: 260, marginTop: 16, borderRadius: 12 },
});
