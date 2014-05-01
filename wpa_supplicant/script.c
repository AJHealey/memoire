#include "wpa_ctrl/wpa_ctrl.h"
#include "script.h"
#include <pthread.h>



/* 
 * Insert the logs into the logfile
 */
static void log_event(enum log_events log, const char *arg) {

	switch(log) {
		case LOG_CUSTOM_INFO:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[%d/%d/%d %d:%d:%d] %s\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec, arg);
			break;
		case LOG_TRY_CONNECTION:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[%d/%d/%d %d:%d:%d] Trying to connect to network: %s\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec, arg);
			break;
		case LOG_CONNECTED:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[%d/%d/%d %d:%d:%d] Connected to network BSSID: %s\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec, arg);
			break;
		case LOG_WPA_TIME:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[%d/%d/%d %d:%d:%d] <WPA_SUPPLICANT> Connection to '%s' in %ldsec %.3ums\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec, arg, wpa_time.time, wpa_time.millitm);
			break;
		case LOG_DHCP_TIME:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[%d/%d/%d %d:%d:%d] <DHCP> IP address obtained in %ldsec %.3ums\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec, dhcp_time.time, dhcp_time.millitm);
			break;
		case LOG_DISCONNECTED:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[%d/%d/%d %d:%d:%d] Disconnected from network: %s\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec, arg);
			break;
		case LOG_DISCONNECTED_BSSID:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[%d/%d/%d %d:%d:%d] Disconnected from network BSSID: %s\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec, arg);
			break;
		case LOG_EAP_SUCCESS:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[%d/%d/%d %d:%d:%d] EAP authentication completed successfully\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
			break;
		case LOG_EAP_FAILED:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[%d/%d/%d %d:%d:%d] EAP authentication failure\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
			break;
		case LOG_CERT_FAILED:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[%d/%d/%d %d:%d:%d] EAP TLS certificate chain validation error\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
			break;
		case LOG_TERMINATE:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[%d/%d/%d %d:%d:%d] Script terminated by user\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
			break;
		case LOG_FAILED:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[ERROR] [%d/%d/%d %d:%d:%d] Interface connection failed\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
			break;
		case LOG_ERROR:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[ERROR] [%d/%d/%d %d:%d:%d] Error: %s\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec, arg);
			break;
	}
}

/*
 * Parse all the event received from wpa_supplicant and execute the resulting action
 */
static void parse_event(const char *reply) {
	const char *event, *addr;
	event = reply;
	/*Removing priority level < > from event*/
	if(*event == '<') {
		event = strchr(event, '>');
		if(event) {
			event++;
		}
		else {
			event = reply;
		}
	}

	if(match(event, WPA_EVENT_CONNECTED)) {
		ftime(&wpa_end);
		timeDiff(wpa_start, wpa_end, &wpa_time);
		/*Get network BSSID*/
		char bssid[18];
		memset(bssid, 0, 18);
		memcpy(bssid, &event[37], 17);
		log_event(LOG_CONNECTED, bssid);
		log_event(LOG_WPA_TIME, bssid);

		/*Start udhcpc for IP address*/
		ftime(&dhcp_start);
		system("udhcpc -t 0 -i wlan0");
		ftime(&dhcp_end);
		timeDiff(dhcp_start, dhcp_end, &dhcp_time);
		log_event(LOG_DHCP_TIME,NULL);
		dhcp = 1;
	}

	/* EAP SUCCESS */
	else if(match(event, WPA_EVENT_EAP_SUCCESS)) {
		log_event(LOG_EAP_SUCCESS, NULL);
	}

	/* EAP FAILURE s*/
	else if(match(event, WPA_EVENT_EAP_FAILURE)) {
		log_event(LOG_EAP_FAILED, NULL);
	}
	
	/* CERTIFICATE ERROR */
	else if(match(event, WPA_EVENT_EAP_TLS_CERT_ERROR)) {
		log_event(LOG_CERT_FAILED, NULL);
	}

	/* DISCONNECTED FROM NETWORK */
	else if (match(event, WPA_EVENT_DISCONNECTED)) {
		char bssid[18];
		memset(bssid, 0, 18);
		memcpy(bssid, &event[30], 17);
		log_event(LOG_DISCONNECTED_BSSID, bssid);
	}
	
	/* TRYING NETWORK CONNECTION */
	else if(match(event, "Trying")) {
		char *ssid, *event_tmp, bssid[18], arg[256];
		/*Get network BSSID*/
		memset(bssid, 0, 18);
		memcpy(bssid, &event[25], 17);

		/*Get network SSID*/
		event_tmp = strdup(event);
		ssid = strtok(event_tmp, "'");
		ssid = strtok(NULL, "'");
		sprintf(arg,"'%s' (BSSID: %s)", ssid, bssid);
		log_event(LOG_TRY_CONNECTION, arg);
	}
	
	else if(match(event, WPA_EVENT_TERMINATING)) {
		log_event(LOG_TERMINATE, NULL);
	}
}

/*
 * Execute the function w.r.t the special action received
 */
static void execute_action(enum wpa_action action, const char * ssid) {
	switch(action) {
		case ACTION_CONNECT_STUDENT:
			connect_student();
			break;
		case ACTION_CONNECT_EDUROAM:
			connect_eduroam();
			break;
		case ACTION_CONNECT_UCLOUVAIN:
			connect_uclouvain();
			break;
		case ACTION_CONNECT_VISITEURS:
			connect_visiteurs();
			break;
		case ACTION_CONNECT_PRIVE:
			connect_prive();
			break;
		case ACTION_DISCONNECT:
			commands("DISCONNECT");
			commands("DISABLE_NETWORK 0");
			commands("DISABLE_NETWORK 1");
			commands("DISABLE_NETWORK 2");
			commands("DISABLE_NETWORK 3");
			commands("DISABLE_NETWORK 4");
			log_event(LOG_DISCONNECTED, ssid);
			dhcp = 0;
			break;
		case ACTION_CREATE_NETWORKS:
			create_networks();
			break;
		case ACTION_MAKE_LOG:
			system("logread | grep wifi_script >> log");
			break;	
	}
}


/*
 * Execute and send the command requests to wpa_supplicant
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
 * ID=0: student.UCLouvain
 * ID=1: eduroam
 * ID=2: UCLouvain
 * ID=3: visiteurs.UCLouvain
 * ID=4: UCLouvain-prive
 */
static void create_networks() {
	int i;
	for(i = 0; i < 4; i++) {
		commands("ADD_NETWORK");
	}
	config_network(1, "eduroam", "WPA-EAP", "PEAP", "CCMP", "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", "peaplabel=0", "auth=MSCHAPV2", NULL);

	config_network(2, "UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP", NULL);	
	
	config_network(3, "visiteurs.UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP", NULL);

	config_network(4, "UCLouvain-prive", "NONE", NULL, NULL, NULL, NULL, NULL, NULL, NULL);
}


/*
* Configure the newly created networks
*/
 void config_network(int network, char *ssid, char *key_mgmt, char *eap, char *pairwise, char *identity, char *password, char *ca_cert, char *phase1, char *phase2) {
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
}

/*
 * Connects wpa_supplicant to the student.UCLouvain network
 */
static void connect_student() {
	commands("ENABLE_NETWORK 0");
	ftime(&wpa_start);
	commands("SELECT_NETWORK 0");
	while(dhcp != 1) {
		sleep(1);
	}
}

/*
 * Connects wpa_supplicant to the eduroam network
 */
static void connect_eduroam() {
	commands("ENABLE_NETWORK 1");
	ftime(&wpa_start);
	commands("SELECT_NETWORK 1");
	while(dhcp != 1) {
		sleep(1);
	}
}

/*
 * Connects wpa_supplicant to the UCLouvain network
 */
static void connect_uclouvain() {
	commands("ENABLE_NETWORK 2");
	ftime(&wpa_start);
	commands("SELECT_NETWORK 2");
	while(dhcp != 1) {
		sleep(1);
	}
}

/*
 * Connects wpa_supplicant to the visiteurs.UCLouvain network
 */
static void connect_visiteurs() {
	commands("ENABLE_NETWORK 3");
	ftime(&wpa_start);
	commands("SELECT_NETWORK 3");
	while(dhcp != 1) {
		sleep(1);
	}
}

/*
 * Connects wpa_supplicant to the UCLouvain-prive network
 */
static void connect_prive() {
	commands("ENABLE_NETWORK 4");
	ftime(&wpa_start);
	commands("SELECT_NETWORK 4");
	while(dhcp != 1) {
		sleep(1);
	}
}

void *wpa_loop(void *p_data) {
	char reply[BUF];
	size_t reply_len;
	//for select() method
	int ctrl_fd, r, err;
	fd_set ctrl_fds;
	struct timeval timeout;
	
	ftime(&wpa_start);
	system("wpa_supplicant -B -D nl80211 -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant_student.UCLouvain.conf");
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
	
	//Loop for incoming events from wpa_supplicant
	while(1) {
		FD_ZERO(&ctrl_fds);
		ctrl_fd = wpa_ctrl_get_fd(ctrl);
		FD_SET(ctrl_fd, &ctrl_fds);
		timeout.tv_sec = 30;
		timeout.tv_usec = 0;
		//Wait for event
		r = select(ctrl_fd+1, &ctrl_fds, NULL, &ctrl_fds, &timeout);
		switch(r) {
			case -1:
				log_event(LOG_ERROR, "Error during select()\n");
				break;
			case 0:
				if(wpa_ctrl_request(ctrl, "PING", strlen("PING"), reply, &reply_len, NULL))
					reply_len = 0;
				reply[reply_len] = '\0';
				if(!match(reply, "PONG", strlen("PONG"))) {
					log_event(LOG_ERROR, "wpa_supplicant not responding\n");
				}
				break;
			default: //event from wpa_supplicant received
				reply_len = BUF-1;
				wpa_ctrl_recv(ctrl, reply, &reply_len);
				reply[reply_len] = '\0';
				parse_event(reply);
				break;
		}
	}
	wpa_ctrl_detach(ctrl);
	wpa_ctrl_close(ctrl);
	return NULL;
}



/*******************************
 * TESTING AREA
 *******************************/


void *connection_loop(void * p_data) {
	while(1) {
		sleep(DELAY);
		printf("Disconnection from student\n");
		execute_action(ACTION_DISCONNECT, "student.UCLouvain");
		sleep(DELAY);
		printf("Connect to eduroam\n");
		execute_action(ACTION_CONNECT_EDUROAM, NULL);
		sleep(DELAY);
		printf("Disconnection from eduroam\n");
		execute_action(ACTION_DISCONNECT, "eduroam");
		sleep(DELAY);
		printf("Connect to UCLouvain\n");
		execute_action(ACTION_CONNECT_UCLOUVAIN, NULL);
		sleep(DELAY);
		printf("Disconnection from UCLouvain\n");
		execute_action(ACTION_DISCONNECT, "UCLouvain");
		sleep(DELAY);
		printf("Connect to visiteurs.UCLouvain\n");
		execute_action(ACTION_CONNECT_VISITEURS, NULL);
		sleep(DELAY);
		printf("Disconnection from visiteurs.UCLouvain\n");
		execute_action(ACTION_DISCONNECT, "visiteurs.UCLouvain");
		sleep(DELAY);
		printf("Connect to UCLouvain-prive\n");
		execute_action(ACTION_CONNECT_PRIVE, NULL);
		sleep(DELAY);
		printf("Disconnection from UCLouvain-prive\n");
		execute_action(ACTION_DISCONNECT, "UCLouvain-prive");
		sleep(DELAY);
		printf("Closing file");
		fclose(f);
		printf("Connect to student.UCLouvain\n");
		execute_action(ACTION_CONNECT_STUDENT, NULL);
		sleep(DELAY);
	}
	return NULL;
}



int main(int argc, char ** argv) {
	system("killall hostapd");
	//log_event(LOG_CUSTOM_INFO, "Starting script");
	int r = 0;

	/* FILE */
	f = fopen("logs.txt", "w");
	if(f == NULL) {
		printf("Error opening file\n");
		exit(1);
	}	

	pthread_t wpa_thread, loop_thread;
	r = pthread_create(&wpa_thread, NULL, wpa_loop, NULL);
	if(!r){
		while(1) {
			if(dhcp == 1) {
				printf("Starting loop\n");
				/* Create all the networks */
				execute_action(ACTION_CREATE_NETWORKS, NULL);
				r = pthread_create(&loop_thread, NULL, connection_loop, NULL);
				if(r)
					fprintf(stderr, "%s", strerror(r));
				break;
			}
			else
				sleep(1);
		}
	}
	else 
		fprintf(stderr, "%s", strerror(r));

	pthread_join(wpa_thread, NULL);
	pthread_join(loop_thread, NULL);
	closelog();

	return 0;
}
