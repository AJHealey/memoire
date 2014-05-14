
#ifndef SCRIPT_H
#define SCRIPT_H

#define DEFAULT_CTRL_IFACE "/tmp/run/wpa_supplicant/wlan0"
#define BUF 1024
#define DELAY 10

/* PING */
#define DEFDATALEN 56
#define MAXIPLEN 60
#define MAXICMPLEN 76


struct wpa_ctrl *ctrl;
struct timeb wpa_start, wpa_end, dhcp_start, dhcp_end, wpa_time, dhcp_time;
struct tm tm;
time_t now;
int dhcp = 0;
FILE *f;

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


/* All possible events used to write the logs */
enum log_events {
	LOG_START,
	LOG_STOP,
	LOG_SSID,
	LOG_TRIED,
	LOG_CONNECTED,
	LOG_WPA_TIME,
	LOG_DHCP_TIME,
	LOG_PING_START,
	LOG_PING_GOOGLE,
	LOG_PING_GMAIL,
	LOG_PING_GITHUB,
	LOG_PING_GITHUBSSL,
	LOG_PING_ADE,
	LOG_PING_UCLOUVAIN,
	LOG_PING_ICAMPUS,
	LOG_PING_STOP,
	LOG_FAILED,
	LOG_ERROR,
};

/* Actions possible */
enum wpa_action {
	ACTION_CONNECT_STUDENT,
	ACTION_CONNECT_EDUROAM,
	ACTION_CONNECT_UCLOUVAIN,
	ACTION_CONNECT_VISITEURS,
	ACTION_CONNECT_PRIVE,
	ACTION_DISCONNECT,
	ACTION_CREATE_NETWORKS,
};

/* Prototypes */
static void log_event(enum log_events log, const char *arg);
static void parse_event(const char *reply);
static void execute_action(enum wpa_action action, const char *ssid);
static void commands(char *cmd);
static void create_networks();
static void config_network(int network, char *ssid, char *key_mgmt, char *eap, char *pairwise, char *identity, char *password, char *ca_cert, char *phase1, char *phase2);
static void connect_student();
static void connect_eduroam();
static void connect_uclouvain();
static void connect_visiteurs();
static void connect_prive();
static int checkService(char *host, const char *port);
void *wpa_loop(void *p_data);
void *connection_loop(void *p_data);




#endif /* SCRIPT2_H */
