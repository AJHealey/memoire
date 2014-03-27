
#include "wpa_ctrl/wpa_ctrl.h"
#include "script.h"

#define BUF 2048
#define DEFAULT_CTRL_IFACE "/tmp/run/wpa_supplicant/wlan0"

static struct wpa_ctrl *ctrl;
static const char *server_ip = "130.104.78.201";
static const char *server_port = "45678";
static struct timeb wpa_start, wpa_end, dhcp_start, dhcp_end, wpa_time, dhcp_time;

enum wpaEvent {
	SCRIPT_EVENT_UNCHANGED,
	SCRIPT_EVENT_CONNECTED,
	SCRIPT_EVENT_DISCONNECTED,
	SCRIPT_EVENT_FAILED,
	SCRIPT_EVENT_TERMINATED
};

enum wpaState {
	WPA_STATE_UNDEFINED,
	WPA_STATE_CONNECTED,
	WPA_STATE_DISCONNECTED,
	WPA_STATE_CONNECTION_LOST,
	WPA_STATE_TERMINATED
};

enum wpaAction {
	WPA_ACTION_CONNECT,
	WPA_ACTION_CONNECTION_LOST,
	WPA_ACTION_CONNECTION_REESTABLISHED,
	WPA_ACTION_FAILED,
	WPA_ACTION_DISCONNECT
};

enum logEvent {
	WPA_LOG_STARTED,
	WPA_LOG_CONNECTED,
	WPA_LOG_DISCONNECTED,
	WPA_LOG_CONNECTION_LOST,
	WPA_LOG_CONNECTION_REESTABLISHED,
	WPA_LOG_TERMINATE,
	WPA_LOG_FAILED,
	WPA_LOG_ERROR,
	WPA_LOG_CUSTOM_ERROR
};


/*
 * Open and attach a new connection to the running instance of wpa_supplicant
 */
static int open_connection() 
{
	ctrl = wpa_ctrl_open(DEFAULT_CTRL_IFACE);
	if(ctrl == NULL) {
		printf("Error in wpa_ctrl_open\n");
		return -1;
	}
	wpa_ctrl_attach(ctrl);
}

/*
 * Close and detach connection
 */
static void close_connection()
{
	wpa_ctrl_detach(ctrl);
	wpa_ctrl_close(ctrl);
	ctrl = NULL;
}

/*
 * Copy all the events in the logfile
 */
static void logEvent(enum logEvent l, const char *ssid, const char *msg) {
	switch(l) {
		case WPA_LOG_STARTED:
			syslog(LOG_NOTICE, "Starting wpa_supplicant for network: %s", ssid);
			break;
		case WPA_LOG_CONNECTED:
			syslog(LOG_NOTICE, "Connected to network '%s'", ssid);
			break;

		case WPA_LOG_DISCONNECTED:
			syslog(LOG_NOTICE, "Disconnected to network '%s'", ssid);
			break;

		case WPA_LOG_CONNECTION_LOST:
			syslog(LOG_NOTICE, "Lost connection to network '%s'", ssid);
			break;

		case WPA_LOG_CONNECTION_REESTABLISHED:
			syslog(LOG_NOTICE, "Connection to network '%s' reestabished",ssid);
			break;
	
		case WPA_LOG_TERMINATE:
			syslog(LOG_NOTICE, "Terminating wpa_supplicant session");
			break;

		case WPA_LOG_FAILED:
			syslog(LOG_NOTICE, "Connection failed");
			break;

		case WPA_LOG_ERROR:
			syslog(LOG_ERR, "Error", msg);
			break;

		case WPA_LOG_CUSTOM_ERROR:
			syslog(LOG_ERR, "Custome error");
			break;
	}
}

/*
 * Handles the wpa events
 */
static void wpa_event(const char *msg, enum wpaEvent *event) {
	const char *pos;
	pos = msg;
	if(match_str(pos, WPA_EVENT_CONNECTED)) {
		*event = SCRIPT_EVENT_CONNECTED;
	}
	else if (match_str(pos, WPA_EVENT_DISCONNECTED))
		*event = SCRIPT_EVENT_DISCONNECTED;
	else if (match_str(pos, WPA_EVENT_TERMINATING))
		*event = SCRIPT_EVENT_TERMINATED;
	else if (match_str(pos, WPA_EVENT_EAP_FAILURE))
		*event = SCRIPT_EVENT_FAILED; 
}

/*
 * Handles the wpa actions
 */


/*
 * Boot process
 * Kill hostapd and launch wpa_supplicant with 1st configuration file
 */
static void boot_process() 
{
	system("killall hostapd");
	ftime(&wpa_start);
	system("wpa_supplicant -B -D nl80211 -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant_student.UCLouvain.conf");
	//system("wpa_supplicant -B -D nl80211 -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant_montoise.conf");
	ftime(&wpa_end);

	ftime(&dhcp_start);	
	system("udhcpc -t 0 -i wlan0");
	ftime(&dhcp_end);
	
	timeDiff(wpa_start, wpa_end, &wpa_time);
	timeDiff(dhcp_start, dhcp_end, &dhcp_time);
	printTimeDifference();
	
}

static void printTimeDifference() {
	printf("wpa_supplicant connection: %ldseconds and %u ms\n", wpa_time.time, wpa_time.millitm);
	printf("DHCP: %ldseconds and %u ms\n", dhcp_time.time, dhcp_time.millitm);
	memset(&wpa_time, 0, sizeof(wpa_time));
	memset(&dhcp_time, 0, sizeof(dhcp_time));
}

/*
 * Sends the log file to the server (130.104.78.201:45678)
 */
static void sendLog() {
	int socketfd;
	socketfd = connect_to_server(server_ip, server_port);
	printf("Socket : %d\n", socketfd);
}


/*
 * Executes command requests to wpa_supplicant
 */
static int commands(char *cmd)
{
	char reply[BUF];
	size_t len;
	int ret;
	
	if(ctrl == NULL) {
		printf("Not connected to wpa_supplicant\n");
		return -1;
	}
	len = BUF-1;
	ret = wpa_ctrl_request(ctrl, cmd, os_strlen(cmd), reply, &len, NULL);
	if(ret == -2) {
		printf("'%s' command timed out.\n",cmd);
		return -2;
	} else if(ret < 0) {
		printf("'%s' command failed.\n",cmd);
		return -1;
	}
	reply[len] = '\0';
	printf("%s", reply);
	return 0;
}

/*
* TODO PSK only for Montoise SSID.
*/
static void configNetwork(int network, char *ssid, char *key_mgmt, char *eap, char *pairwise, char *identity, char *password, char *ca_cert, char *phase1, char *phase2,  char *psk) {
	char cmd[1024];

	os_snprintf(cmd, sizeof(cmd), "SET_NETWORK %d ssid \"%s\"", network,ssid);
	commands(cmd);

	if(key_mgmt != NULL) {
		os_snprintf(cmd, sizeof(cmd), "SET_NETWORK %d key_mgmt %s", network, key_mgmt);
		commands(cmd);
	}

	if(eap != NULL) {
		os_snprintf(cmd, sizeof(cmd), "SET_NETWORK %d eap %s", network, eap);
		commands(cmd);
	}

	if(pairwise != NULL) {
		os_snprintf(cmd, sizeof(cmd), "SET_NETWORK %d pairwise %s", network, pairwise);
		commands(cmd);
	}

	if(identity != NULL) {
		os_snprintf(cmd, sizeof(cmd), "SET_NETWORK %d identity \"%s\"", network, identity);
		commands(cmd);
	}

	if(password != NULL) {
		os_snprintf(cmd, sizeof(cmd), "SET_NETWORK %d password \"%s\"", network, password);
		commands(cmd);
	}

	if(ca_cert != NULL) {
		os_snprintf(cmd, sizeof(cmd), "SET_NETWORK %d ca_cert \"%s\"", network, ca_cert);
		commands(cmd);
	}

	if(phase1 != NULL) {
		os_snprintf(cmd, sizeof(cmd), "SET_NETWORK %d phase1 \"%s\"", network, phase1);
		commands(cmd);
	}

	if(phase2 != NULL) {
		os_snprintf(cmd, sizeof(cmd), "SET_NETWORK %d phase2 \"%s\"",network, phase2);
		commands(cmd);
	}

	/*
	 * TODO Only for Montoise SSID
	 */
	if(psk != NULL) {
		os_snprintf(cmd, sizeof(cmd), "SET_NETWORK %d psk \"%s\"",network, psk);
		commands(cmd);
	}
}

/*
 * Create the configuration for all the networks
 * ID=0: student.UCLOUVAIN
 * ID=1: eduroam
 * ID=2: UCLOUVAIN
 */
static void createNetworks() {
	int i;
	for(i = 0; i < 2; i++) {
		commands("ADD_NETWORK");
	}
	configNetwork(1, "eduroam", "WPA-EAP", "PEAP", "CCMP", "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", "peaplabel=0", "auth=MSCHAPV2", NULL);

	configNetwork(2, "UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP", NULL);
	
	
}


/*
 * Main loop changing networks and gathering the logs
 */
static void loop() {
	commands("DISCONNECT");
	commands("DISABLE_NETWORK 0");
	commands("DISABLE_NETWORK 1");
	commands("DISABLE_NETWORK 2");

	//Eduroam
	commands("ENABLE_NETWORK 1");
	ftime(&wpa_start);
	commands("SELECT_NETWORK 1");
	ftime(&wpa_end);
	system("killall udhcpc");
	ftime(&dhcp_start);
	system("udhcpc -i wlan0");
	ftime(&dhcp_end);
	timeDiff(wpa_start, wpa_end, &wpa_time);
	timeDiff(dhcp_start, dhcp_end, &dhcp_time);
	printTimeDifference();
	//TODO Debug
	printf("Network changed to Eduroam\n");
	sleep(15);
	commands("DISCONNECT");
	commands("DISABLE_NETWORK 1");

	//UCLOUVAIN
	commands("ENABLE_NETWORK 2");
	ftime(&wpa_start);
	commands("SELECT_NETWORK 2");
	ftime(&wpa_end);
	system("killall udhcpc");
	ftime(&dhcp_start);
	system("udhcpc -i wlan0");
	ftime(&dhcp_end);
	timeDiff(wpa_start, wpa_end, &wpa_time);
	timeDiff(dhcp_start, dhcp_end, &dhcp_time);
	printTimeDifference();
	//TODO Debug
	printf("Network changed to UCLOUVAIN\n");
	sleep(15);
	commands("DISCONNECT");
	commands("DISABLE_NETWORK 2");

	//student.UCLOUVAIN
	commands("ENABLE_NETWORK 0");
	ftime(&wpa_start);
	commands("SELECT_NETWORK 0");
	ftime(&wpa_end);
	system("killall udhcpc");
	ftime(&dhcp_start);
	system("udhcpc -i wlan0");
	ftime(&dhcp_end);
	timeDiff(wpa_start, wpa_end, &wpa_time);
	timeDiff(dhcp_start, dhcp_end, &dhcp_time);
	printTimeDifference();
	//TODO Debug
	printf("Network changed to student.UCLOUVAIN\n");
}

static void connectMontoise() {
	commands("ADD_NETWORK");
	configNetwork(1, "Montoise", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, "Bf3-aZ47");
	commands("SELECT_NETWORK 1");
}

int main(int argc, char ** argv)
{
	char buf[256];
	size_t len = sizeof(buf) - 1;
	boot_process();
	open_connection();
	sleep(10);

	createNetworks();
	loop();
	//sendLog();
	return 0;
}
