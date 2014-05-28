
#ifndef SCRIPT_H
#define SCRIPT_H

#define DEFAULT_CTRL_IFACE "/var/run/wpa_supplicant/wlan0"
#define BUF 1024 /* Reply buffer size */
#define DELAY 10 /* Delay in seconds for the connection loop */
#define debug_print(args) if (DEBUG) printf(args) /* Debug print */


char router_mac[18]; /* Router mac address */
char *ssid_log; /* SSID of the current network */
struct wpa_ctrl *ctrl; /* Control interface of wpa_supplicant */
struct timeb wpa_start, wpa_end, dhcp_start, dhcp_end; /* Time structures */
struct log *log_struct; /* Log structure */
struct tm tm; /* For date computation */
time_t now; /* For date computation */
int start_loop = 0; /* Starts the connection thread as soon as wpa_supplicant is started and networks are created */
int dhcp = 0; /* DHCP */
FILE *f; /* Log file */

/* Structure for log file */
struct log {
	char *date;
	char *ssid;
	struct ap_tried *tried;
	struct ap_connect *connected;
	struct ap_time *time;
	struct check_serv *services;
};

/* Structure that stores all the AP BSSID tried for association */
struct ap_tried {
	char *bssid;
	int num;
	struct ap_tried *next;
};
struct ap_tried *first = NULL;
struct ap_tried *curr = NULL;


/* Structure that stores the BSSID of the AP it is connected with */
struct ap_connect {
	char *bssid;
	int num;
	struct ap_connect *next;
};
struct ap_connect *first_connect = NULL;
struct ap_connect *curr_connect = NULL;


/* Structure for time details about wpa_supplicant and udhcpc */
struct ap_time {
	struct timeb wpa_time;
	struct timeb dhcp_time;
};


/* Structure that stores the information about the services */
struct check_serv {
	char *DNS_1;
	char *DNS_2;
	char *google;
	char *facebook;
	char *youtube;
	char *yahoo;
	char *wikipedia;
	char *twitter;
	char *amazon;
	char *linkedin;
	char *gmail;
	char *github;
	char *uclouvain;
	char *icampus;
	char *moodle;
	char *libellule;
	char *ade;
	char *studssh;
};


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
	LOG_PRINT_STRUCT,
	LOG_START_CONNECTION_LOOP,
	LOG_STOP_CONNECTION_LOOP,
	LOG_FINAL_STOP_CONNECTION_LOOP,
	LOG_MAC_ADDR,
	LOG_INFO_DATE,
};

/* List of possible actions */
enum wpa_action {
	ACTION_CONNECT,
	ACTION_CONNECT_MAISON,
	ACTION_DISCONNECT,
	ACTION_CREATE_NETWORKS,
};


/* Function prototypes */
static void log_event(enum log_events, const char *);
static void parse_event(const char *);
static void execute_action(enum wpa_action, int);
static void commands(char *);
static void create_networks();
static void config_network(int, char *, char *, char *, char *, char *, char *, char *, char *, char *);
static void connect_network(int );
static int checkDNS(char *);
static int checkService(char *, const char *);
static void services_loop();
static void scan();
static void send_log();
static void clear_struct();
void *wpa_loop(void *);
void *connection_loop(void *);




#endif /* SCRIPT2_H */
