
#ifndef SCRIPT_H
#define SCRIPT_H

#define DEFAULT_CTRL_IFACE "/tmp/run/wpa_supplicant/wlan0"
#define BUF 1024
#define DELAY 10
#define debug_print(args) if (DEBUG) printf(args)

/* PING */
#define DEFDATALEN 56
#define MAXIPLEN 60
#define MAXICMPLEN 76

char router_mac[18]; /* Router mac address */

struct wpa_ctrl *ctrl;
struct timeb wpa_start, wpa_end, dhcp_start, dhcp_end, wpa_time, dhcp_time;
struct tm tm;
time_t now;
int start_loop = 0;
int dhcp = 0;
FILE *f; //Log file

/* For Logs */
char *ssid_log;


/* Stores all the AP BSSID tried for association */
struct ap_tried {
	char *bssid;
	int num;
	struct ap_tried *next;
};
struct ap_tried *first = NULL;
struct ap_tried *curr = NULL;

/* Stores all the results of a scan */
struct scan_results {
	char *bssid;
	char *freq;
	char *signal;
	char *flags;
	char *ssid;
	int num;
	struct scan_results *next;
};
struct scan_results *first_scan = NULL;
struct scan_results *curr_scan = NULL;


/* All possible events used to write the logs in JSON syntax */
enum log_events {
	LOG_START_FILE,
	LOG_STOP_FILE,
	LOG_START_LOG,
	LOG_STOP_LOG,
	LOG_START_LOOP,
	LOG_STOP_LOOP,
	LOG_FINAL_STOP_LOOP,
	LOG_START_SCAN,
	LOG_STOP_SCAN,
	LOG_START_CONNECTION,
	LOG_STOP_CONNECTION,
	LOG_START_CONNECTION_LOOP,
	LOG_STOP_CONNECTION_LOOP,
	LOG_FINAL_STOP_CONNECTION_LOOP,
	LOG_MAC_ADDR,
	LOG_SCAN_BSSID,
	LOG_SCAN_STRENGTH,
	LOG_SCAN_SSID,
	LOG_INFO_DATE,
	LOG_INFO_SSID,
	LOG_INFO_TRIED,
	LOG_INFO_CONNECTED,
	LOG_INFO_TIME_START,
	LOG_INFO_TIME_WPA,
	LOG_INFO_TIME_DHCP,
	LOG_INFO_TIME_STOP,
	LOG_INFO_SERVICE_START,
	LOG_INFO_SERVICE_GOOGLE,
	LOG_INFO_SERVICE_GMAIL,
	LOG_INFO_SERVICE_GITHUB,
	LOG_INFO_SERVICE_GITHUB_SSL,
	LOG_INFO_SERVICE_UCLOUVAIN,
	LOG_INFO_SERVICE_ADE,
	LOG_INFO_SERVICE_ICAMPUS,
	LOG_INFO_SERVICE_STOP,
};

/* Actions possible */
enum wpa_action {
	ACTION_CONNECT_STUDENT,
	ACTION_CONNECT_EDUROAM,
	ACTION_CONNECT_UCLOUVAIN,
	ACTION_CONNECT_VISITEURS,
	ACTION_CONNECT_PRIVE,
	ACTION_CONNECT_MAISON,
	ACTION_DISCONNECT,
	ACTION_CREATE_NETWORKS,
	ACTION_SCAN,
};

/* Prototypes */
static void log_event(enum log_events log, const char *arg);
static void parse_event(const char *reply);
static void execute_action(enum wpa_action action);
static void commands(char *cmd);
static void create_networks();
static void config_network(int network, char *ssid, char *key_mgmt, char *eap, char *pairwise, char *identity, char *password, char *ca_cert, char *phase1, char *phase2);
static void connect_eduroam();
static void connect_uclouvain();
static void connect_visiteurs();
static void connect_prive();
static void connect_student();
static int checkService(char *host, const char *port);
static void services_loop();
static void scan();
static void send_log();
void *wpa_loop(void *p_data);
void *connection_loop(void *p_data);




#endif /* SCRIPT2_H */
