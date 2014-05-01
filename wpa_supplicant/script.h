
#ifndef SCRIPT2_H
#define SCRIPT2_H

#define DEFAULT_CTRL_IFACE "/tmp/run/wpa_supplicant/wlan0"
#define BUF 1024
#define DELAY 10

struct wpa_ctrl *ctrl;
struct timeb wpa_start, wpa_end, dhcp_start, dhcp_end, wpa_time, dhcp_time;
struct tm tm;
time_t now;
int dhcp = 0;
FILE *f;

enum log_events {
	LOG_CUSTOM_INFO,
	LOG_TRY_CONNECTION,
	LOG_CONNECTED,
	LOG_WPA_TIME,
	LOG_DHCP_TIME,
	LOG_DISCONNECTED,
	LOG_DISCONNECTED_BSSID,
	LOG_EAP_SUCCESS,
	LOG_EAP_FAILED,
	LOG_CERT_FAILED,
	LOG_TERMINATE,
	LOG_FAILED,
	LOG_ERROR,
};

enum wpa_action {
	ACTION_CONNECT_STUDENT,
	ACTION_CONNECT_EDUROAM,
	ACTION_CONNECT_UCLOUVAIN,
	ACTION_CONNECT_VISITEURS,
	ACTION_CONNECT_PRIVE,
	ACTION_DISCONNECT,
	ACTION_CREATE_NETWORKS,
	ACTION_MAKE_LOG
};

static void log_event();
static void parse_event();
static void execute_action();
static void commands();
static void get_status();
static void create_networks();
static void config_network();
static void connect_student();
static void connect_eduroam();
static void connect_uclouvain();
static void connect_visiteurs();
static void connect_prive();
void *connection_loop();
void *wpa_loop();



#endif /* SCRIPT2_H */
