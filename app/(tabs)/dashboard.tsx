import { Stack } from 'expo-router'
import React from 'react'
import { StyleSheet, View } from 'react-native'
import Icon from '@react-native-vector-icons/fontawesome';

export default function dashboard() {
  return (
    <View>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Icon name="rocket" size={30} color="#900" />;

    </View>
  )
}

const style = StyleSheet.create({})