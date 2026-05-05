import React, { useContext, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { Button, Text, TextInput } from 'react-native-paper';
import { AuthContext } from '../context/AuthContext';
import { colors } from '../constants/colors';

export default function RegisterScreen({ navigation }) {
  const { register } = useContext(AuthContext);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const onRegister = async () => {
    try {
      setError('');
      await register(name, email, password);
      navigation.goBack();
    } catch (e) {
      setError(e?.response?.data?.message || 'Registration failed');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Create account</Text>
      <TextInput label="Full Name" mode="outlined" value={name} onChangeText={setName} />
      <TextInput label="Email" mode="outlined" value={email} onChangeText={setEmail} autoCapitalize="none" style={styles.mt} />
      <TextInput label="Password" mode="outlined" secureTextEntry value={password} onChangeText={setPassword} style={styles.mt} />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <Button mode="contained" style={styles.mt} onPress={onRegister}>Register</Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 20, backgroundColor: colors.bg },
  title: { fontSize: 24, fontWeight: '700', marginBottom: 20, color: colors.primary },
  mt: { marginTop: 12 },
  error: { marginTop: 10, color: colors.danger },
});
