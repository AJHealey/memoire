/*
 * wpa_supplicant/hostapd / Debug prints
 * Copyright (c) 2002-2007, Jouni Malinen <j@w1.fi>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Alternatively, this software may be distributed under the terms of BSD
 * license.
 *
 * See README and COPYING for more details.
 */

#ifndef WPA_DEBUG_H
#define WPA_DEBUG_H
 
#include "wpabuf.h"
 
/* Debugging function - conditional printf and hex dump. Driver wrappers can
 * use these for debugging purposes. */
 
enum { MSG_MSGDUMP, MSG_DEBUG, MSG_INFO, MSG_WARNING, MSG_ERROR };
 
#ifdef CONFIG_NO_STDOUT_DEBUG
 
#define wpa_debug_print_timestamp() do { } while (0)
#define wpa_printf(args...) do { } while (0)
#define wpa_hexdump(l,t,b,le) do { } while (0)
#define wpa_hexdump_buf(l,t,b) do { } while (0)
#define wpa_hexdump_key(l,t,b,le) do { } while (0)
#define wpa_hexdump_buf_key(l,t,b) do { } while (0)
#define wpa_hexdump_ascii(l,t,b,le) do { } while (0)
#define wpa_hexdump_ascii_key(l,t,b,le) do { } while (0)
#define wpa_debug_open_file(p) do { } while (0)
#define wpa_debug_close_file() do { } while (0)
 
#else /* CONFIG_NO_STDOUT_DEBUG */
 
int wpa_debug_open_file(const char *path);
void wpa_debug_close_file(void);

void wpa_debug_print_timestamp(void);
 
void wpa_printf(int level, const char *fmt, ...)
PRINTF_FORMAT(2, 3);
 
void wpa_hexdump(int level, const char *title, const u8 *buf, size_t len);
 
static inline void wpa_hexdump_buf(int level, const char *title,
                                   const struct wpabuf *buf)
{
        wpa_hexdump(level, title, wpabuf_head(buf), wpabuf_len(buf));
}
 
void wpa_hexdump_key(int level, const char *title, const u8 *buf, size_t len);
 
static inline void wpa_hexdump_buf_key(int level, const char *title,
                                       const struct wpabuf *buf)
{
        wpa_hexdump_key(level, title, wpabuf_head(buf), wpabuf_len(buf));
}

void wpa_hexdump_ascii(int level, const char *title, const u8 *buf,
                       size_t len);

void wpa_hexdump_ascii_key(int level, const char *title, const u8 *buf,
                           size_t len);

#endif /* CONFIG_NO_STDOUT_DEBUG */


#ifdef CONFIG_NO_WPA_MSG
#define wpa_msg(args...) do { } while (0)
#define wpa_msg_ctrl(args...) do { } while (0)
#define wpa_msg_register_cb(f) do { } while (0)
#else /* CONFIG_NO_WPA_MSG */

void wpa_msg(void *ctx, int level, const char *fmt, ...) PRINTF_FORMAT(3, 4);

void wpa_msg_ctrl(void *ctx, int level, const char *fmt, ...)
PRINTF_FORMAT(3, 4);

typedef void (*wpa_msg_cb_func)(void *ctx, int level, const char *txt,
                                size_t len);

void wpa_msg_register_cb(wpa_msg_cb_func func);
#endif /* CONFIG_NO_WPA_MSG */


#ifdef CONFIG_NO_HOSTAPD_LOGGER
#define hostapd_logger(args...) do { } while (0)
#define hostapd_logger_register_cb(f) do { } while (0)
#else /* CONFIG_NO_HOSTAPD_LOGGER */
void hostapd_logger(void *ctx, const u8 *addr, unsigned int module, int level,
                    const char *fmt, ...) PRINTF_FORMAT(5, 6);

typedef void (*hostapd_logger_cb_func)(void *ctx, const u8 *addr,
                                       unsigned int module, int level,
                                       const char *txt, size_t len);
 
void hostapd_logger_register_cb(hostapd_logger_cb_func func);
#endif /* CONFIG_NO_HOSTAPD_LOGGER */

#define HOSTAPD_MODULE_IEEE80211        0x00000001
#define HOSTAPD_MODULE_IEEE8021X        0x00000002
#define HOSTAPD_MODULE_RADIUS           0x00000004
#define HOSTAPD_MODULE_WPA              0x00000008
#define HOSTAPD_MODULE_DRIVER           0x00000010
#define HOSTAPD_MODULE_IAPP             0x00000020
#define HOSTAPD_MODULE_MLME             0x00000040

enum hostapd_logger_level {
        HOSTAPD_LEVEL_DEBUG_VERBOSE = 0,
        HOSTAPD_LEVEL_DEBUG = 1,
        HOSTAPD_LEVEL_INFO = 2,
        HOSTAPD_LEVEL_NOTICE = 3,
        HOSTAPD_LEVEL_WARNING = 4
};


#ifdef CONFIG_DEBUG_SYSLOG

void wpa_debug_open_syslog(void);
void wpa_debug_close_syslog(void);

#else /* CONFIG_DEBUG_SYSLOG */

static inline void wpa_debug_open_syslog(void)
{
}

static inline void wpa_debug_close_syslog(void)
{
}

#endif /* CONFIG_DEBUG_SYSLOG */


#ifdef EAPOL_TEST
#define WPA_ASSERT(a)                                                  \
        do {                                                           \
                if (!(a)) {                                            \
                        printf("WPA_ASSERT FAILED '" #a "' "           \
                               "%s %s:%d\n",                           \
                               __FUNCTION__, __FILE__, __LINE__);      \
                        exit(1);                                       \
                }                                                      \
        } while (0)
#else
#define WPA_ASSERT(a) do { } while (0)
#endif

#endif /* WPA_DEBUG_H */
