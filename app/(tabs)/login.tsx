import { Button } from '@react-navigation/elements'
import { Stack, useRouter } from 'expo-router'
import React from 'react'
import { Dimensions, StyleSheet, Text, View } from 'react-native'
import { TextInput } from 'react-native-gesture-handler'

const screenHeight = Dimensions.get('window').height;
const router = useRouter();

export default function login() {
  return (
    <View style={style.container}>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <View style={[style.boxForground, { backgroundColor:  '#ffffff' }]}>
        <Text 
        style={style.welcomeText}>
          Welcome back 👋
        </Text>
        
        <Text 
        style={style.underText}>
          Login with you traveltime account 
        </Text>

        <TextInput 
        style={style.email}
        value='E-Mail'
        />

        <TextInput 
        style={style.password}
        value='Password'
        />

        <Button style={style.loginButton} onPress={() => router.push('/(tabs)/dashboard')}>
        Login
        </Button>
        <Text style={style.registerTextButton} onPress={() => router.push('/(tabs)/register')}> 
        Register now!
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
  email: {
    height: 40,
    margin: 48,
    marginTop: screenHeight / 12.7,
    borderWidth: 1, 
    borderColor: 'dimgray',
    color: 'black',
    padding: 12,
    borderRadius: 12
  },
  password: {
    height: 40,
    margin: 48,
    marginTop: -32,
    borderWidth: 1, 
    borderColor: 'dimgray',
    color: 'black',
    padding: 12,
    borderRadius: 12
  },
  loginButton: {
    alignSelf: 'center'
  },
  registerTextButton: {
    color: 'black',
    alignSelf: 'center',
    marginTop: 18,
    fontWeight: '900'
  }
})