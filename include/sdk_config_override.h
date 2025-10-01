#pragma once

// Arquivo para resolver conflitos de definições entre platformio.ini e sdkconfig.h
// Este arquivo deve ser incluído ANTES de qualquer header do ESP32/Arduino
//
// Os warnings são causados por redefinições de macros entre:
// 1. Definições da linha de comando (-D flags do platformio.ini)
// 2. Definições do sdkconfig.h do framework ESP32
//
// Estratégia: Definir as macros com os valores desejados do platformio.ini
// e suprimir warnings de redefinição

#ifndef SDK_CONFIG_OVERRIDE_H
#define SDK_CONFIG_OVERRIDE_H

// Suprimir warnings específicos de redefinição de macros para GCC
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wundef"

// Definições WiFi - usar valores otimizados do platformio.ini
#ifdef CONFIG_ESP32_WIFI_STATIC_RX_BUFFER_NUM
#undef CONFIG_ESP32_WIFI_STATIC_RX_BUFFER_NUM
#endif
#ifdef CONFIG_ESP32_WIFI_DYNAMIC_RX_BUFFER_NUM
#undef CONFIG_ESP32_WIFI_DYNAMIC_RX_BUFFER_NUM
#endif
#ifdef CONFIG_ESP32_WIFI_TX_BUFFER_TYPE
#undef CONFIG_ESP32_WIFI_TX_BUFFER_TYPE
#endif
#ifdef CONFIG_ESP32_WIFI_ENABLE_WPA3_SAE
#undef CONFIG_ESP32_WIFI_ENABLE_WPA3_SAE
#endif
#ifdef CONFIG_ESP32_PHY_MAX_WIFI_TX_POWER
#undef CONFIG_ESP32_PHY_MAX_WIFI_TX_POWER
#endif
#ifdef CONFIG_ARDUINO_LOOP_STACK_SIZE
#undef CONFIG_ARDUINO_LOOP_STACK_SIZE
#endif

// Redefinir com valores do ambiente ESP32 (padrão para esp32dev)
#if defined(ESP32_32U_EXTERNAL_ANTENNA)
  // Configurações para ESP32-32U com antena externa (produção)
  #define CONFIG_ESP32_WIFI_STATIC_RX_BUFFER_NUM 16
  #define CONFIG_ESP32_WIFI_DYNAMIC_RX_BUFFER_NUM 32
  #define CONFIG_ESP32_WIFI_TX_BUFFER_TYPE 1
  #define CONFIG_ESP32_WIFI_ENABLE_WPA3_SAE 1
  #define CONFIG_ESP32_PHY_MAX_WIFI_TX_POWER 20
  #define CONFIG_ARDUINO_LOOP_STACK_SIZE 16384
#elif defined(ESP32_WROOM_32_INTERNAL_ANTENNA)
  // Configurações para ESP32-WROOM-32 com antena interna
  #define CONFIG_ESP32_WIFI_STATIC_RX_BUFFER_NUM 10
  #define CONFIG_ESP32_WIFI_DYNAMIC_RX_BUFFER_NUM 16
  #define CONFIG_ESP32_WIFI_TX_BUFFER_TYPE 1
  #define CONFIG_ESP32_WIFI_ENABLE_WPA3_SAE 1
  #define CONFIG_ESP32_PHY_MAX_WIFI_TX_POWER 18
  #define CONFIG_ARDUINO_LOOP_STACK_SIZE 12288
#else
  // Configurações padrão (fallback)
  #define CONFIG_ESP32_WIFI_STATIC_RX_BUFFER_NUM 10
  #define CONFIG_ESP32_WIFI_DYNAMIC_RX_BUFFER_NUM 16
  #define CONFIG_ESP32_WIFI_TX_BUFFER_TYPE 1
  #define CONFIG_ESP32_WIFI_ENABLE_WPA3_SAE 1
  #define CONFIG_ESP32_PHY_MAX_WIFI_TX_POWER 18
  #define CONFIG_ARDUINO_LOOP_STACK_SIZE 12288
#endif

// Restaurar warnings
#pragma GCC diagnostic pop

#endif // SDK_CONFIG_OVERRIDE_H