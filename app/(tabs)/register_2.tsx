import { Button } from '@react-navigation/elements'
import { Stack, useRouter } from 'expo-router'
import React, { useState } from 'react'
import { Dimensions, StyleSheet, Text, View } from 'react-native'
import { TextInput } from 'react-native-gesture-handler'

const screenHeight = Dimensions.get('window').height;
const screenWidth = Dimensions.get('window').width;

const router = useRouter();


export default function register_2() {
      const [phone, setPhone] = useState('');
  const [error, setError] = useState('');

  const handlePhoneChange = (text: string) => {
    // Allow only numbers, remove other characters
    const cleaned = text.replace(/[^0-9]/g, '');
    setPhone(cleaned);

    // Basic validation (example: 10-digit number)
    if (cleaned.length > 0 && cleaned.length < 20) {
      setError('Enter a valid phone number');
    } else {
      setError('');
    }
  };

  return (
    <View style={style.container}>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <View style={[style.boxForground, { backgroundColor:  '#ffffff' }]}>
        <Text 
        style={style.welcomeText}>
          Just a few more things 
        </Text>
        
        <Text 
        style={style.underText}>
          Please enter the following information
        </Text>

        <TextInput 
        style={style.firstName}
        value='Name'
        />

        <TextInput 
        style={style.lastName}
        value='Last name'
        />

        <TextInput
        style={[style.input, error ? style.inputError : null]}
        value={phone}
        onChangeText={handlePhoneChange}
        placeholder="+1234567890"
        keyboardType="phone-pad"
        maxLength={20}
      />

        <Button style={style.loginButton} onPress={() => router.push('/(tabs)/dashboard')}>
        Register
        </Button>
        <Text style={style.registerTextButton} onPress={() => router.push('/(tabs)/login')}> 
        Already got an account?
        </Text>
        </View>
    </View>
  )
}

const style = StyleSheet.create({
  boxForground:{
    color: 'white',
    width: '100%',
    height: screenHeight / 1.3,
    zIndex: 0,
    bottom: 0,
    position: 'absolute',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
  },
  container: {
    flex: 1, 
    flexDirection: 'column',
    color: 'white',
    backgroundColor: '#121212',
    justifyContent: 'flex-start'
  },
  welcomeText:{
    color: 'black',
    alignSelf: 'center',
    paddingTop: screenHeight / 7,
    fontSize: 24,
    fontWeight: '900'
  },
  underText:{
    color: 'black',
    alignSelf: 'center',
    fontSize: 12,
    fontWeight: '200'
  },
    firstName: {
    height: 40,
    margin: 48,
    marginLeft: screenWidth / 8,
    marginTop: screenHeight / 5,
    position: 'absolute',
    borderWidth: 1, 
    borderColor: 'dimgray',
    color: 'black',
    padding: 12,
    borderRadius: 12
  },
  lastName: {
    marginLeft: screenWidth / 2,
    marginTop: screenHeight / 5,
    position: 'absolute',
    height: 40,
    margin: 48,
    borderWidth: 1, 
    borderColor: 'dimgray',
    color: 'black',
    padding: 12,
    borderRadius: 12
  },
  loginButton: {
    marginTop: screenHeight / 2.5,
    alignSelf: 'center'
  },
  registerTextButton: {
    color: 'black',
    alignSelf: 'center',
    marginTop: 18,
    fontWeight: '900'
  },
  phoneInput: {
    marginTop: screenHeight / 4.5,
    marginLeft: screenWidth / 6,
    position: 'absolute',
    height: 40,
    borderWidth: 1, 
    borderColor: 'dimgray',
    color: 'black',
    padding: 12,
    borderRadius: 12
  },
input: {
    marginTop: screenHeight / 3.8,
    marginLeft: screenWidth / 8,
    height: 40,
    width: screenWidth / 1.35,
    borderWidth: 1,
    borderColor: 'dimgray',
    borderRadius: 12,
    padding: 12,
    position: 'absolute',
  },
  inputError: {
    borderColor: 'red',
  },
  errorText: {
    marginTop: 5,
    color: 'red',
  },
})