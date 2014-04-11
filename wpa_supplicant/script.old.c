
#include "wpa_ctrl/wpa_ctrl.h"
#include "script.h"

/* 
 * Insert the logs into the logfile
 */
static void log_event(enum log_events log, const char *arg) {
	static int isOpen = 0;
	
	if(!isOpen) {
		openlog("wifi_script", LOG_PID, LOG_DAEMON);
		isOpen = 1;
	}
	switch(log) {
		case LOG_CUSTOM_INFO:
			syslog(LOG_NOTICE, "%s", arg);
			break;
		case LOG_STARTED:
			syslog(LOG_NOTICE, "Starting script");
			break;
		case LOG_CONNECTED:
			syslog(LOG_NOTICE, "Interface connected to network: '%s'", arg);
			break;
		case LOG_DISCONNECTED:
			syslog(LOG_NOTICE, "Interface disconnected");
			break;
		case LOG_CONNECTION_LOST:
			syslog(LOG_NOTICE, "Interface lost connection to network: '%s'", arg);
			break;
		case LOG_CONNECTION_REESTABLISHED:
			syslog(LOG_NOTICE, "Interface reestablished connection to network: '%s'", arg);
			break;
		case LOG_WPA_TIME:
			syslog(LOG_NOTICE, "wpa_supplicant connection time to network '%s' : %ldsec %ums", arg, wpa_time.time, wpa_time.millitm); 
			break;
		case LOG_DHCP_TIME:
			syslog(LOG_NOTICE, "udhcpc completion time for network '%s' : %ldsec %ums", arg, dhcp_time.time, dhcp_time.millitm); 
			break;
		case LOG_TERMINATE:
			syslog(LOG_NOTICE, "Script terminated", arg);
			break;
		case LOG_FAILED:
			syslog(LOG_NOTICE, "Interface connection failed");
			break;
		case LOG_ERROR:
			syslog(LOG_ERR, "Error: %m", arg);
			break;
		case LOG_CUSTOM_ERROR:
			syslog(LOG_NOTICE, "Error: %s", arg);
			break;
	}	
}

/*
 * Handles all the actions executed by the progam
 */
static void execute(enum wpa_action action) {
	switch(action) {
		case ACTION_OPEN_CONNECTION:
			open_connection();
		break;
		case ACTION_BOOT:
			boot_process();
			log_event(LOG_CONNECTED, "student.UCLouvain");
		break;
		case ACTION_CONNECT_STUDENT:
			connect_student();
		break;
		case ACTION_CONNECT_EDUROAM:
			connect_eduroam();
		break;
		case ACTION_CONNECT_UCLOUVAIN:
			connect_uclouvain();
		break;
		case ACTION_DISCONNECT:
			commands("DISCONNECT");
			commands("DISABLE_NETWORK 0");
			commands("DISABLE_NETWORK 1");
			commands("DISABLE_NETWORK 2");
			log_event(LOG_DISCONNECTED, NULL);
		break;
		case ACTION_CREATE_NETWORKS:
			create_networks();
			log_event(LOG_CUSTOM_INFO, "Networks created");
		break;
		case ACTION_MAKE_LOG:
			system("logread | grep wifi_script >> log");
		break;
	}
}

/*
 * Executes command requests to wpa_supplicant
 */
static void commands(char *cmd)
{
	char reply[BUF];
	size_t len;
	int ret;
	
	if(ctrl == NULL) {
		log_event(LOG_ERROR, "Interface not connected to wpa_supplicant");
		exit(-1);
	}
	ret = wpa_ctrl_request(ctrl, cmd, os_strlen(cmd), reply, &len, NULL);
	if(ret < 0) {
		log_event(LOG_ERROR, ("Command '%s' timed out or failed", cmd));
		exit(-1);
	}
}

/*
 * Create the configuration for all the networks
 * ID=0: student.UCLOUVAIN
 * ID=1: eduroam
 * ID=2: UCLOUVAIN
 */
static void create_networks() {
	int i;
	for(i = 0; i < 2; i++) {
		commands("ADD_NETWORK");
	}
	config_network(1, "eduroam", "WPA-EAP", "PEAP", "CCMP", "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", "peaplabel=0", "auth=MSCHAPV2", NULL);

	config_network(2, "UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP", NULL);	
}

/*
* TODO PSK only for Montoise SSID.
*/
 void config_network(int network, char *ssid, char *key_mgmt, char *eap, char *pairwise, char *identity, char *password, char *ca_cert, char *phase1, char *phase2,  char *psk) {
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
 * Starts wpa_supplicant with student.UCLouvain config file in
 * background and starts the DHCP
 */
static void boot_process() {
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
	log_event(LOG_WPA_TIME, "student.UCLouvain");
	log_event(LOG_DHCP_TIME, "student.UCLouvain");
}

/*
 * Connects wpa_supplicant to the eduroam network
 */
static void connect_eduroam() {
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
	log_event(LOG_WPA_TIME, "eduroam");
	log_event(LOG_DHCP_TIME, "eduroam");
	log_event(LOG_CONNECTED, "eduroam");
}

/*
 * Connects wpa_supplicant to the UCLouvain network
 */
static void connect_uclouvain() {
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
	log_event(LOG_WPA_TIME, "UCLouvain");
	log_event(LOG_DHCP_TIME, "UCLouvain");
	log_event(LOG_CONNECTED, "UCLouvain");
}

/*
 * Connects wpa_supplicant to the student.UCLouvain network
 */
static void connect_student() {
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
	log_event(LOG_WPA_TIME, "student.UCLouvain");
	log_event(LOG_DHCP_TIME, "student.UCLouvain");
	log_event(LOG_CONNECTED, "student.UCLouvain");
}


/*
 * Open the wpa_supplicant control interface and attach it to 
 * the instance of wpa_supplicant
 */
static void open_connection() {
	int err;

	ctrl = wpa_ctrl_open(DEFAULT_CTRL_IFACE);
	if(ctrl == NULL) {
		log_event(LOG_ERROR, "Unable to open wpa_supplicant control interface");
		exit(-1);
	}
	err = wpa_ctrl_attach(ctrl);
	if(err == -1) {
		wpa_ctrl_close(ctrl);
		log_event(LOG_ERROR, "wpa_ctrl_attach error");
		exit(-1);
	}
	if(err == -2) {
		wpa_ctrl_close(ctrl);
		log_event(LOG_ERROR, "wpa_ctrl_attach timeout");
		exit(-1);
	}
}

/*
 * Receive events sent by wpa_supplicant
 */
static void event_recv() {
	int err;
	char reply[BUF];
	size_t reply_len = BUF-1;
	printf("Pending : %d\n", wpa_ctrl_pending(ctrl));
	err = wpa_ctrl_recv(ctrl, reply, &reply_len);
	if(err == -1) {
		printf("wpa_ctrl_recv error\n");
		
	}
	reply[reply_len] = '\0';
	printf("Reply: %s\n", reply);
}


/*
 * Main loop
 */
static void loop() {
	int i;
	execute(ACTION_BOOT);
	execute(ACTION_OPEN_CONNECTION);
	//event_recv();
	//commands("STATUS");

	execute(ACTION_CREATE_NETWORKS);
	for(i = 0; i < 3; i++) {
		sleep(3);
		execute(ACTION_DISCONNECT);
		event_recv();
		execute(ACTION_CONNECT_EDUROAM);
		event_recv();		
		sleep(3);
		execute(ACTION_DISCONNECT);
		event_recv();
		execute(ACTION_CONNECT_UCLOUVAIN);
		event_recv();
		sleep(3);
		execute(ACTION_DISCONNECT);
		event_recv();
		execute(ACTION_CONNECT_STUDENT);
		event_recv();
		execute(ACTION_DISCONNECT);
	}
	execute(ACTION_MAKE_LOG);
}

void connectMaison() {
	system("killall hostapd");
	system("wpa_supplicant -B -D nl80211 -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant_maison.conf");
	system("udhcpc -t 0 -i wlan0");
}

void test() {
	//WPA CTRL INTERFACE
	struct wpa_ctrl *ctrl2;

	//Buffer for replies
	char reply[BUF];
	size_t reply_len;

	//SELECT()
	int ctrl_fd, r;
	fd_set ctrl_fds;

	//Select timeout
	struct timeval ping_timeout;

	//Save SSID
	char ssid[256], old_ssid[256];
	char idstr[256], old_idstr[256];
	ssid[0] = '\0';
	old_ssid[0] = '\0';
	idstr[0] = '\0';
	old_idstr[0] = '\0';

	ctrl2 = wpa_ctrl_open(DEFAULT_CTRL_IFACE);
	if(ctrl2 == NULL) {
		printf("Error ctrl_open\n");
	}
	if(wpa_ctrl_attach(ctrl2)) {
		printf("Error attach\n");
		exit(0);
	}

	while(1) {
		FD_ZERO(&ctrl_fds);
		ctrl_fd = wpa_ctrl_get_fd(ctrl2);
		FD_SET(ctrl_fd, &ctrl_fds);
		ping_timeout.tv_sec = 5;
		ping_timeout.tv_usec = 0;
		//Wait for event
		r = select(ctrl_fd+1, &ctrl_fds, NULL, &ctrl_fds, &ping_timeout);
		switch(r) {
			case -1:
				printf("Error select\n");
				break;
			case 0:
				printf("Timeout\n");
				if(wpa_ctrl_request(ctrl2, "PING", strlen("PING"), reply, &reply_len, NULL))
					reply_len = 0;
				reply[reply_len] = '\0';
				if(strncmp(reply, "PONG", strlen("PONG"))) {
					printf("STR: %d\n", strncmp(reply, "PONG", strlen("PONG")));
					printf("WPA not responding\n");
				}
				break;
			default:
				//Event received
				reply_len = BUF-1;
				wpa_ctrl_recv(ctrl2, reply, &reply_len);
				reply[reply_len] = '\0';
				printf("BUF: %s\n", reply);
				break;
		}
	}	
	
}


int main(int argc, char ** argv) {
	//log_event(LOG_STARTED, NULL);
	//loop();
	//closelog();

	connectMaison();
	test();
	return 0;
}
