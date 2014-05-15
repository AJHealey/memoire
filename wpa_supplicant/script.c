#include "wpa_ctrl/wpa_ctrl.h"
#include "script.h"
#include <pthread.h>

#define DEBUG 0

/* 
 * Insert the logs into the logfile
 */
static void log_event(enum log_events log, const char *arg) {

	switch(log) {
		case LOG_START:
			fprintf(f, "{\n");
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "\"date\": \"%d/%d/%d %d:%d:%d\",\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
			break;

		case LOG_STOP:
			fprintf(f, "}\n");
			break;

		case LOG_SSID:
			fprintf(f, "\"ssid\": \"%s\",\n", arg);
			break;

		case LOG_TRIED: {
			struct ap_tried *ptr = first;
			fprintf(f, "\"tried\": [ ");
			/* Display all the BSSID tried */
			while(ptr != NULL) {
				fprintf(f, "\"%s\"", ptr->bssid);
				/* JSON syntax */
				if(first->num != 1) {
					fprintf(f, ", ");
					first->num -= 1;
				}
				else
					fprintf(f, " ");
				ptr = ptr->next;
			}
			fprintf(f, "],\n");
			}
			break;

		case LOG_CONNECTED:
			fprintf(f, "\"connected\": \"%s\",\n", arg);
			fprintf(f, "\"time\": {\n");
			break;

		case LOG_WPA_TIME:
			fprintf(f, "\"wpa_supplicant\": \"%ldsec %.3ums\",\n", wpa_time.time, wpa_time.millitm);
			break;

		case LOG_DHCP_TIME:
			fprintf(f, "\"dhcp\": \"%ldsec %.3ums\"\n", dhcp_time.time, dhcp_time.millitm);
			fprintf(f, "},\n");
			break;

		case LOG_PING_START:
			fprintf(f, "\"services\": {\n");
			break;

		case LOG_PING_GOOGLE:
			fprintf(f, "\"google.be\": \"%s\",\n", arg);
			break;

		case LOG_PING_GMAIL:
			fprintf(f, "\"smtp.gmail.com\": \"%s\",\n", arg);
			break;

		case LOG_PING_GITHUB:
			fprintf(f, "\"github.com\": \"%s\",\n", arg);
			break;

		case LOG_PING_GITHUBSSL:
			fprintf(f, "\"ssl.github.com\": \"%s\",\n", arg);
			break;

		case LOG_PING_ADE:
			fprintf(f, "\"horaire.sgsi.ucl.ac.be\": \"%s\",\n", arg);
			break;

		case LOG_PING_UCLOUVAIN:
			fprintf(f, "\"uclouvain.be\": \"%s\",\n", arg);
			break;

		case LOG_PING_ICAMPUS:
			fprintf(f, "\"icampus.uclouvain.be\": \"%s\",\n", arg);
			break;

		case LOG_PING_STOP:
			fprintf(f, "}\n");
			break;

		case LOG_FAILED:
			/*now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "[ERROR] [%d/%d/%d %d:%d:%d] Interface connection failed\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);*/
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
		log_event(LOG_WPA_TIME, NULL);

		/*Start udhcpc for IP address*/
		ftime(&dhcp_start);
		system("udhcpc -t 0 -i wlan0 -C");
		ftime(&dhcp_end);
		timeDiff(dhcp_start, dhcp_end, &dhcp_time);
		log_event(LOG_DHCP_TIME,NULL);
		dhcp = 1;
	}
	
	/* TRYING NETWORK CONNECTION */
	else if(match(event, "Trying")) {
		char *ssid, *event_tmp, bssid[18];
		
		/* Get BSSID */
		memset(bssid, 0, 18);
		memcpy(bssid, &event[25], 17);

		/* Get SSID */
		event_tmp = strdup(event);
		ssid = strtok(event_tmp, "'");
		ssid = strtok(NULL, "'");
		ssid_log = ssid;

		struct ap_tried *ptr = (struct ap_tried*) malloc (sizeof(struct ap_tried));
		ptr->bssid = malloc(strlen(bssid)+1);

		/* First AP tried */
		if(first == NULL) {
			strcpy(ptr->bssid, bssid);
			ptr->next = NULL;
			first = curr = ptr;
			first->num = 1;
		}
		/* Other APs tried */
		else {
			strcpy(ptr->bssid, bssid);
			first->num += 1;
			ptr->next = NULL;
			curr->next = ptr;
			curr = ptr;
		}
		
	}
	/* Association accepted with AP */
	else if(match(event, "Associated")) {
		char bssid[18];
		/*Get network BSSID*/
		memset(bssid, 0, 18);
		memcpy(bssid, &event[16], 17);
		
		log_event(LOG_SSID, ssid_log);
		log_event(LOG_TRIED, NULL);
		
		/* Free AP Tried linked List */
		struct ap_tried *current = first;
		struct ap_tried *tmp;
		while(current != NULL) {
			tmp = current->next;
			free(current);
			current = tmp;
		}
		first = NULL;
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
			log_event(LOG_STOP, NULL);
			commands("DISCONNECT");
			commands("DISABLE_NETWORK 0");
			commands("DISABLE_NETWORK 1");
			commands("DISABLE_NETWORK 2");
			commands("DISABLE_NETWORK 3");
			commands("DISABLE_NETWORK 4");
			commands("DISABLE_NETWORK 5");
			dhcp = 0;
			break;
		case ACTION_CREATE_NETWORKS:
			create_networks();
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
		/* Wpa_supplicant timed out. Restart command */
		commands(cmd);
		
	}
}




/*
 * Create the configuration for all the networks
 * ID=1: eduroam
 * ID=2: UCLouvain
 * ID=3: visiteurs.UCLouvain
 * ID=4: UCLouvain-prive
 * ID=5: student.UCLouvain
 */
static void create_networks() {
	int i;
	for(i = 0; i < 5; i++) {
		commands("ADD_NETWORK");
	}
	config_network(1, "eduroam", "WPA-EAP", "PEAP", "CCMP", "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", "peaplabel=0", "auth=MSCHAPV2");

	config_network(2, "UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP");
	
	config_network(3, "visiteurs.UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP");

	config_network(4, "UCLouvain-prive", "NONE", NULL, NULL, NULL, NULL, NULL, NULL, NULL);

	config_network(5, "student.UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP");
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
	log_event(LOG_START, NULL);
	commands("ENABLE_NETWORK 5");
	ftime(&wpa_start);
	commands("SELECT_NETWORK 5");
	while(dhcp != 1) {
		sleep(1);
	}
}

/*
 * Connects wpa_supplicant to the eduroam network
 */
static void connect_eduroam() {
	log_event(LOG_START, NULL);
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
	log_event(LOG_START, NULL);
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
	log_event(LOG_START, NULL);
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
	log_event(LOG_START, NULL);
	commands("ENABLE_NETWORK 4");
	ftime(&wpa_start);
	commands("SELECT_NETWORK 4");
	while(dhcp != 1) {
		sleep(1);
	}
}

/* 
 * Check if services are available or not
 */
static int checkService(char *host, const char *port) {
	int sockfd;
	struct sockaddr_in serv_addr;
	char *host_name;
	struct hostent *hostptr;
	struct in_addr *ptr;
	unsigned short port_number;
	
	
	port_number = atoi(port);

	if((hostptr = (struct hostent *) gethostbyname(host)) == NULL) {
		return 0;
	}
	host_name = host;

	ptr = (struct in_addr *)*(hostptr->h_addr_list);

	memset((char *) &serv_addr, 0, sizeof(serv_addr));
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_addr.s_addr = ptr->s_addr;
	serv_addr.sin_port = htons(port_number);

	//Create communication endpoint
	if((sockfd = socket(AF_INET, SOCK_STREAM, 0))<0) {
		return 0;
	}
	
	//Connect to server
	if(connect(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) {
		return 0;
	}
	else {
		debug_print("OK\n");
		return 1;
	}
	close(sockfd);
}



void *wpa_loop(void *p_data) {
	char reply[BUF];
	size_t reply_len;
	//for select() method
	int ctrl_fd, r, err;
	fd_set ctrl_fds;
	struct timeval timeout;
	
	ftime(&wpa_start);
	log_event(LOG_START, NULL);
	system("wpa_supplicant -B -D nl80211 -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf");

	
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
	/* Creation of the list of networks */
	execute_action(ACTION_CREATE_NETWORKS, NULL);
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
				debug_print(reply);
				parse_event(reply);
				break;
		}
	}
	wpa_ctrl_detach(ctrl);
	wpa_ctrl_close(ctrl);
	return NULL;
}

/*
 * Loop to check availability
 */
void services_loop() {
	log_event(LOG_PING_START, NULL);
	if(checkService("google.be", "443") == 1)
		log_event(LOG_PING_GOOGLE, "1");
	else
		log_event(LOG_PING_GOOGLE, "0");

	if(checkService("smtp.gmail.com", "587") == 1)
		log_event(LOG_PING_GMAIL, "1");
	else
		log_event(LOG_PING_GMAIL, "0");

	if(checkService("github.com", "22") == 1)
		log_event(LOG_PING_GITHUB, "1");
	else
		log_event(LOG_PING_GITHUB, "0");

	if(checkService("ssl.github.com", "443") == 1)
		log_event(LOG_PING_GITHUBSSL, "1");
	else
		log_event(LOG_PING_GITHUBSSL, "0");
	
	/*if(checkService("horaire.sgsi.ucl.ac", "8080") == 1)
		log_event(LOG_PING_ADE, "available");
	else
		log_event(LOG_PING_ADE, "unavailable");*/

	if(checkService("uclouvain.be", "443") == 1)
		log_event(LOG_PING_UCLOUVAIN, "1");
	else
		log_event(LOG_PING_UCLOUVAIN, "0");

	if(checkService("icampus.uclouvain.be", "443") == 1)
		log_event(LOG_PING_ICAMPUS, "1");
	else
		log_event(LOG_PING_ICAMPUS, "0");

	log_event(LOG_PING_STOP, NULL);	
}

void send_log() {
	if(sendLogs("logs.txt") < 0)
		debug_print("ERROR\n");
}

void *connection_loop(void * p_data) {
	int close = 0;
	services_loop();
	while(1) {
		sleep(DELAY);
		debug_print("Disconnection from student\n");
		execute_action(ACTION_DISCONNECT, "student.UCLouvain");
		sleep(DELAY);

		debug_print("Connect to eduroam\n");
		execute_action(ACTION_CONNECT_EDUROAM, NULL);
		services_loop();
		sleep(DELAY);
		debug_print("Disconnection from eduroam\n");
		execute_action(ACTION_DISCONNECT, "eduroam");
		sleep(DELAY);

		debug_print("Connect to UCLouvain\n");
		execute_action(ACTION_CONNECT_UCLOUVAIN, NULL);
		services_loop();
		sleep(DELAY);
		debug_print("Disconnection from UCLouvain\n");
		execute_action(ACTION_DISCONNECT, "UCLouvain");
		sleep(DELAY);

		debug_print("Connect to visiteurs.UCLouvain\n");
		execute_action(ACTION_CONNECT_VISITEURS, NULL);
		services_loop();
		sleep(DELAY);
		debug_print("Disconnection from visiteurs.UCLouvain\n");
		execute_action(ACTION_DISCONNECT, "visiteurs.UCLouvain");
		sleep(DELAY);

		debug_print("Connect to UCLouvain-prive\n");
		execute_action(ACTION_CONNECT_PRIVE, NULL);
		sleep(DELAY);
		debug_print("Disconnection from UCLouvain-prive\n");
		execute_action(ACTION_DISCONNECT, "UCLouvain-prive");
		sleep(DELAY);

		debug_print("Connect to student.UCLouvain\n");
		execute_action(ACTION_CONNECT_STUDENT, NULL);
		services_loop();
		sleep(DELAY);
		if(close == 0) {
			debug_print("SAVE\n");
			log_event(LOG_STOP, NULL);
			fclose(f);
			send_log();
			f = fopen("logs.txt","w");
			close = 0;
		}
		close += 1;
	}
	return NULL;
}


int main(int argc, char ** argv) {
	system("killall hostapd");
	pthread_t wpa_thread, loop_thread;
	int r = 0;

	/* FILE */
	f = fopen("logs.txt", "w");
	if(f == NULL) {
		debug_print("Error opening file\n");
		exit(1);
	}	
	
	r = pthread_create(&wpa_thread, NULL, wpa_loop, NULL);
	if(!r){
		while(1) {
			if(dhcp == 1) {
				debug_print("Starting loop\n");
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

	return 0;
}
