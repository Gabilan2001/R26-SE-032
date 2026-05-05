import React, { useContext, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { Button, Text, TextInput } from 'react-native-paper';
import { AuthContext } from '../context/AuthContext';
import { colors } from '../constants/colors';

export default function LoginScreen({ navigation }) {
  const { login } = useContext(AuthContext);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const onLogin = async () => {
    try {
      setError('');
      await login(email, password);
    } catch (e) {
      setError(e?.response?.data?.message || 'Login failed');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to TomatoDoc</Text>
      <TextInput label="Email" mode="outlined" value={email} onChangeText={setEmail} autoCapitalize="none" />
      <TextInput label="Password" mode="outlined" secureTextEntry value={password} onChangeText={setPassword} style={styles.mt} />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <Button mode="contained" style={styles.mt} onPress={onLogin}>Login</Button>
      <Button mode="text" onPress={() => navigation.navigate('Register')}>Create account</Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 20, backgroundColor: colors.bg },
  title: { fontSize: 24, fontWeight: '700', marginBottom: 20, color: colors.primary },
  mt: { marginTop: 12 },
  error: { marginTop: 10, color: colors.danger },
});
