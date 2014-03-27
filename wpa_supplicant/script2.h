
#ifndef SCRIPT2_H
#define SCRIPT2_H

#define DEFAULT_CTRL_IFACE "/tmp/run/wpa_supplicant/wlan0"
#define BUF 2048

struct wpa_ctrl *ctrl;
struct timeb wpa_start, wpa_end, dhcp_start, dhcp_end, wpa_time, dhcp_time;

enum log_events {
	LOG_CUSTOM_INFO,
	LOG_STARTED,
	LOG_CONNECTED,
	LOG_DISCONNECTED,
	LOG_CONNECTION_LOST,
	LOG_CONNECTION_REESTABLISHED,
	LOG_WPA_TIME,
	LOG_DHCP_TIME,
	LOG_TERMINATE,
	LOG_FAILED,
	LOG_ERROR,
	LOG_CUSTOM_ERROR
};

enum wpa_state {
	STATE_UNDEFINED,
	STATE_CONNECTED,
	STATE_DISCONNECTED,
	STATE_CONNECTION_LOST,
	STATE_TERMINATED
};

enum wpa_action {
	ACTION_OPEN_CONNECTION,
	ACTION_BOOT,
	ACTION_CONNECT_STUDENT,
	ACTION_CONNECT_EDUROAM,
	ACTION_CONNECT_UCLOUVAIN,
	ACTION_DISCONNECT,
	ACTION_CREATE_NETWORKS,
	ACTION_MAKE_LOG
};

enum wpa_event {
	EVENT_UNCHANGED,
	EVENT_CONNECTED,
	EVENT_DISCONNECTED,
	EVENT_FAILED,
	EVENT_TERMINATED
};

static void log_event();
static void execute();
static void boot_process();
static void commands();
static void create_networks();
static void config_network();
static void connect_eduroam();
static void connect_uclouvain();
static void connect_student();
static void open_connection();
static void loop();



#endif /* SCRIPT2_H */
