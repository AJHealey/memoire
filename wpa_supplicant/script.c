#include "wpa_ctrl/wpa_ctrl.h"
#include "script.h"
#include <pthread.h>

#define DEBUG 1

/* 
 * Insert the logs into the logfile
 */
static void log_event(enum log_events log, const char *arg) {

	switch(log) {
		case LOG_START_FILE:
			fprintf(f, "{\n");
			break;

		case LOG_STOP_FILE:
			fprintf(f, "}");
			break;

		case LOG_START_LOG:
			fprintf(f, "\"log\":[\n");
			break;

		case LOG_STOP_LOG:
			fprintf(f, "]\n");
			break;

		case LOG_START_LOOP:
			fprintf(f, "{\n");
			break;

		case LOG_STOP_LOOP:
			fprintf(f, "},\n");
			break;

		case LOG_FINAL_STOP_LOOP:
			fprintf(f, "}\n");
			break;

		case LOG_START_SCAN: {
			fprintf(f, "\"scan\":[\n");
			
			struct scan_results *ptr = first_scan;
			
			while(ptr != NULL) {
				
				fprintf(f, "{\n"); 
				fprintf(f, "\"bssid\": \"%s\",\n", ptr->bssid);
				fprintf(f, "\"signal\": \"%s\",\n", ptr->signal);
				fprintf(f, "\"ssid\": \"%s\",\n", ptr->ssid);
				
				/* JSON syntax */
				if(first_scan -> num != 1) {
					
					fprintf(f,"},\n");
					first_scan->num -= 1;
				}
				else {
					
					fprintf(f,"}\n");
				}
				
				ptr = ptr->next;
			}
			}
			break;

		case LOG_STOP_SCAN:
			fprintf(f, "],\n");
			break;

		case LOG_START_CONNECTION:
			fprintf(f, "\"connections\":[\n");
			break;

		case LOG_STOP_CONNECTION:
			fprintf(f, "]\n");
			break;
		
		
		case LOG_START_CONNECTION_LOOP:
			fprintf(f, "{\n");
			break;
		
		case LOG_STOP_CONNECTION_LOOP:
			fprintf(f, "},\n");
			break;

		case LOG_FINAL_STOP_CONNECTION_LOOP:
			fprintf(f, "}\n");
			break;


		case LOG_MAC_ADDR:
			fprintf(f, "\"mac\": \"%s\",\n", arg);
			break;

		case LOG_SCAN_BSSID:
			fprintf(f, "\"bssid\": \"12:12:12:12:12:12\",\n");
			break;

		case LOG_SCAN_STRENGTH:
			fprintf(f, "\"strength\": 1,\n");
			break;

		case LOG_SCAN_SSID:
			//TODO comme tried
			fprintf(f, "\"ssid\": \"blabla\"\n");
			break;

		case LOG_INFO_DATE:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "\"date\": \"%d/%d/%d %d:%d:%d\",\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
			break;
			
		
		case LOG_INFO_SSID:
			fprintf(f, "\"ssid\": \"%s\",\n", arg);
			break;


		case LOG_INFO_TRIED: {
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

		case LOG_INFO_CONNECTED:
			fprintf(f, "\"connected\": \"%s\",\n", arg);
			break;
		
		case LOG_INFO_TIME_START:
			fprintf(f, "\"time\": {\n");
			break;

		case LOG_INFO_TIME_WPA:
			fprintf(f, "\"wpa_supplicant\": \"%ldsec %.3ums\",\n", wpa_time.time, wpa_time.millitm);
			break;

		case LOG_INFO_TIME_DHCP:
			fprintf(f, "\"dhcp\": \"%ldsec %.3ums\"\n", dhcp_time.time, dhcp_time.millitm);
			break;
		
		case LOG_INFO_TIME_STOP:
			fprintf(f, "},\n");
			break;

		case LOG_INFO_SERVICE_START:
			fprintf(f, "\"services\": {\n");
			break;

		case LOG_INFO_SERVICE_GOOGLE:
			fprintf(f, "\"google.be\": \"%s\",\n", arg);
			break;
		
		case LOG_INFO_SERVICE_GMAIL:
			fprintf(f, "\"smtp.gmail.com\": \"%s\",\n", arg);
			break;
	
		case LOG_INFO_SERVICE_GITHUB:
			fprintf(f, "\"github.com\": \"%s\",\n", arg);
			break;

		case LOG_INFO_SERVICE_GITHUB_SSL:
			fprintf(f, "\"ssl.github.com\": \"%s\",\n", arg);
			break;

		case LOG_INFO_SERVICE_ADE:
			fprintf(f, "\"horaire.sgsi.ucl.ac.be\": \"%s\",\n", arg);
			break;
		
		case LOG_INFO_SERVICE_UCLOUVAIN:
			fprintf(f, "\"uclouvain.be\": \"%s\",\n", arg);
			break;

		case LOG_INFO_SERVICE_ICAMPUS:
			fprintf(f, "\"icampus.uclouvain.be\": \"%s\"\n", arg);
			break;
		
		case LOG_INFO_SERVICE_STOP:
			fprintf(f, "}\n");
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
		log_event(LOG_INFO_CONNECTED, bssid);
		log_event(LOG_INFO_TIME_START, NULL);
		log_event(LOG_INFO_TIME_WPA, NULL);

		/*Start udhcpc for IP address*/
		system("killall udhcpc");
		ftime(&dhcp_start);
		system("udhcpc -t 0 -i wlan0 -C");
		ftime(&dhcp_end);
		timeDiff(dhcp_start, dhcp_end, &dhcp_time);
		log_event(LOG_INFO_TIME_DHCP,NULL);
		log_event(LOG_INFO_TIME_STOP, NULL);
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
		
		log_event(LOG_INFO_SSID, ssid_log);
		log_event(LOG_INFO_TRIED, NULL);
		
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
static void execute_action(enum wpa_action action) {
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
			dhcp = 0;
			break;
		case ACTION_CREATE_NETWORKS:
			create_networks();
			break;
		case ACTION_SCAN:
			commands("SCAN");
			commands("SCAN_RESULTS");
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
		exit(-1);
	}
	ret = wpa_ctrl_request(ctrl, cmd, os_strlen(cmd), reply, &len, NULL);
	if(ret < 0) {
		/* Wpa_supplicant timed out. Restart command */
		ftime(&wpa_start);
		commands(cmd);
		
	}
}




/*
 * Create the configuration for all the networks
 * ID=0: eduroam
 * ID=1: UCLouvain
 * ID=2: visiteurs.UCLouvain
 * ID=3: UCLouvain-prive
 * ID=4: student.UCLouvain
 */
static void create_networks() {
	int i;
	for(i = 0; i <= 4; i++) {
		commands("ADD_NETWORK");
	}
	config_network(0, "eduroam", "WPA-EAP", "PEAP", "CCMP", "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", "peaplabel=0", "auth=MSCHAPV2");

	config_network(1, "UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP");
	
	config_network(2, "visiteurs.UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP");

	config_network(3, "UCLouvain-prive", "NONE", NULL, NULL, NULL, NULL, NULL, NULL, NULL);

	config_network(4, "student.UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP");

}


/*
 * Configure the newly created networks
 */
 void config_network(int network, char *ssid, char *key_mgmt, char *eap, char *pairwise, char *identity, char *password, char *ca_cert, char *phase1, char *phase2) {
	char cmd[512];

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
 * Connects wpa_supplicant to the eduroam network
 */
static void connect_eduroam() {
	log_event(LOG_INFO_DATE, NULL);
	ftime(&wpa_start);
	commands("SELECT_NETWORK 0");
	while(dhcp != 1) {
		sleep(1);
	}
}

/*
 * Connects wpa_supplicant to the UCLouvain network
 */
static void connect_uclouvain() {
	log_event(LOG_INFO_DATE, NULL);
	ftime(&wpa_start);
	commands("SELECT_NETWORK 1");
	while(dhcp != 1) {
		sleep(1);
	}
}

/*
 * Connects wpa_supplicant to the visiteurs.UCLouvain network
 */
static void connect_visiteurs() {
	log_event(LOG_INFO_DATE, NULL);
	ftime(&wpa_start);
	commands("SELECT_NETWORK 2");
	while(dhcp != 1) {
		sleep(1);
	}
}

/*
 * Connects wpa_supplicant to the UCLouvain-prive network
 */
static void connect_prive() {
	log_event(LOG_INFO_DATE, NULL);
	ftime(&wpa_start);
	commands("SELECT_NETWORK 3");
	while(dhcp != 1) {
		sleep(1);
	}
}

/*
 * Connects wpa_supplicant to the student.UCLouvain network
 */
static void connect_student() {
	log_event(LOG_INFO_DATE, NULL);
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

/*
 * Loop to check availability
 */
static void services_loop() {
	log_event(LOG_INFO_SERVICE_START, NULL);
	if(checkService("google.be", "443") == 1)
		log_event(LOG_INFO_SERVICE_GOOGLE, "1");
	else
		log_event(LOG_INFO_SERVICE_GOOGLE, "0");

	if(checkService("smtp.gmail.com", "587") == 1)
		log_event(LOG_INFO_SERVICE_GMAIL, "1");
	else
		log_event(LOG_INFO_SERVICE_GMAIL, "0");

	if(checkService("github.com", "22") == 1)
		log_event(LOG_INFO_SERVICE_GITHUB, "1");
	else
		log_event(LOG_INFO_SERVICE_GITHUB, "0");

	if(checkService("ssl.github.com", "443") == 1)
		log_event(LOG_INFO_SERVICE_GITHUB_SSL, "1");
	else
		log_event(LOG_INFO_SERVICE_GITHUB_SSL, "0");
	
	/*if(checkService("horaire.sgsi.ucl.ac", "8080") == 1)
		log_event(LOG_INFO_SERVICE_ADE, "available");
	else
		log_event(LOG_INFO_SERVICE_ADE, "unavailable");*/

	if(checkService("uclouvain.be", "443") == 1)
		log_event(LOG_INFO_SERVICE_UCLOUVAIN, "1");
	else
		log_event(LOG_INFO_SERVICE_UCLOUVAIN, "0");

	if(checkService("icampus.uclouvain.be", "443") == 1)
		log_event(LOG_INFO_SERVICE_ICAMPUS, "1");
	else
		log_event(LOG_INFO_SERVICE_ICAMPUS, "0");

	log_event(LOG_INFO_SERVICE_STOP, NULL);	
}

/*
 * Scan for networks and get results
 */
static void scan() {
	char *line, *saved_line, *object, *saved_object;
	char reply[BUF*3];
	size_t len = (BUF*3)-1;
	int i,ret;
	
	commands("SCAN"); //Scan	
	ret = wpa_ctrl_request(ctrl, "SCAN_RESULTS", os_strlen("SCAN_RESULTS"), reply, &len, NULL);
	if(ret < 0) {
		/* Wpa_supplicant timed out. Restart scan method */
		scan();
	}
	reply[len] = '\0';
	i = 0; 
	/* Tokenize results and extract information */
	for(line = strtok_r(reply, "\n", &saved_line); line; line = strtok_r(NULL, "\n", &saved_line)) {
		printf("%s\n", line);		
		if(i > 0) {
			char *bssid, *freq, *signal, *flags,*ssid;
			struct scan_results *ptr = (struct scan_results*) malloc (sizeof(struct scan_results));
			bssid = strtok(line, "\t");
			freq = strtok(NULL,"\t");
			signal = strtok(NULL, "\t");
			flags = strtok(NULL, "\t");
			ssid = strtok(NULL, "\t");

			ptr->bssid = malloc(strlen(bssid)+1);
			ptr->freq = malloc(strlen(freq)+1);
			ptr->signal = malloc(strlen(signal)+1);
			ptr->flags = malloc(strlen(flags)+1);
			ptr->ssid = malloc(strlen(ssid)+1);

			/* First result */
			if(first_scan == NULL) {
				strcpy(ptr->bssid, bssid);
				strcpy(ptr->freq, freq);
				strcpy(ptr->signal, signal);
				strcpy(ptr->flags, flags);
				strcpy(ptr->ssid, ssid);
				ptr->next = NULL;
				first_scan = curr_scan = ptr;
				first_scan->num = 1;
			}
			/* Other scan results */
			else {
				strcpy(ptr->bssid, bssid);
				strcpy(ptr->freq, freq);
				strcpy(ptr->signal, signal);
				strcpy(ptr->flags, flags);
				strcpy(ptr->ssid, ssid);
				first_scan->num += 1;
				ptr->next = NULL;
				curr_scan -> next = ptr;
				curr_scan = ptr;
			}
		}
		i+=1;
	}
	log_event(LOG_START_SCAN, NULL);
	log_event(LOG_STOP_SCAN, NULL);
	
	/* Free scan results */
	struct scan_results *current = first_scan;
	struct scan_results *tmp;
	while(current != NULL) {
		tmp = current->next;
		free(current);
		current = tmp;
	}
	first_scan = NULL;
	memset(&reply[0], 0, sizeof(reply));
}

/* 
 * Send logs to server
 */
static void send_log() {
	if(sendLogs("var/log/logs.txt") < 0)
		debug_print("Error sending log file\n");
}


void *wpa_loop(void *p_data) {
	char reply[BUF];
	size_t reply_len;
	int ctrl_fd, r, err;
	fd_set ctrl_fds;
	struct timeval timeout;

	system("wpa_supplicant -B -D nl80211 -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf");

	
	ctrl = wpa_ctrl_open(DEFAULT_CTRL_IFACE);
	if(ctrl == NULL) {
		debug_print("Unable to open wpa_supplicant control interface\n");
		exit(-1);
	}
	err = wpa_ctrl_attach(ctrl);
	if(err == -1) {
		wpa_ctrl_close(ctrl);
		debug_print("wpa_ctrl_attach error\n");
		exit(-1);
	}
	if(err == -2) {
		wpa_ctrl_close(ctrl);
		debug_print("wpa_ctrl_attach timeout\n");
		exit(-1);
	}
	/* Creation of the list of networks */
	execute_action(ACTION_CREATE_NETWORKS);
	start_loop = 1;

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
				debug_print("Error during select()\n");
				break;
			case 0:
				if(wpa_ctrl_request(ctrl, "PING", strlen("PING"), reply, &reply_len, NULL))
					reply_len = 0;
				reply[reply_len] = '\0';
				if(!match(reply, "PONG", strlen("PONG"))) {
					debug_print("wpa_supplicant not responding\n");
				}
				break;
			default: //event from wpa_supplicant received
				reply_len = BUF-1;
				wpa_ctrl_recv(ctrl, reply, &reply_len);
				reply[reply_len] = '\0';
				printf("[-] %s\n",reply);
				parse_event(reply);
				break;
		}
	}
	wpa_ctrl_detach(ctrl);
	wpa_ctrl_close(ctrl);
	return NULL;
}



void *connection_loop(void * p_data) {
	int close = 0;

	log_event(LOG_START_FILE, NULL);
	log_event(LOG_INFO_DATE, NULL);
	log_event(LOG_MAC_ADDR, router_mac);
	log_event(LOG_START_LOG, NULL);
	

	while(1) {
		
		log_event(LOG_START_LOOP, NULL);
		scan();
		log_event(LOG_START_CONNECTION, NULL);

		//eduroam
		debug_print("Connect to eduroam\n");
		log_event(LOG_START_CONNECTION_LOOP, NULL);
		execute_action(ACTION_CONNECT_EDUROAM);
		services_loop();
		sleep(DELAY);
		debug_print("Disconnection from eduroam\n");
		execute_action(ACTION_DISCONNECT);
		log_event(LOG_STOP_CONNECTION_LOOP, NULL);
		sleep(DELAY);

		//UCLouvain
		debug_print("Connect to UCLouvain\n");
		log_event(LOG_START_CONNECTION_LOOP, NULL);
		execute_action(ACTION_CONNECT_UCLOUVAIN);
		services_loop();
		sleep(DELAY);
		debug_print("Disconnection from UCLouvain\n");
		execute_action(ACTION_DISCONNECT);
		log_event(LOG_STOP_CONNECTION_LOOP, NULL);
		sleep(DELAY);

		//visiteurs.UCLouvain
		debug_print("Connect to visiteurs.UCLouvain\n");
		log_event(LOG_START_CONNECTION_LOOP, NULL);
		execute_action(ACTION_CONNECT_VISITEURS);
		services_loop();
		sleep(DELAY);
		debug_print("Disconnection from visiteurs.UCLouvain\n");
		execute_action(ACTION_DISCONNECT);
		log_event(LOG_STOP_CONNECTION_LOOP, NULL);
		sleep(DELAY);

		//UCLouvain-prive
		debug_print("Connect to UCLouvain-prive\n");
		log_event(LOG_START_CONNECTION_LOOP, NULL);
		execute_action(ACTION_CONNECT_PRIVE);
		sleep(DELAY);
		debug_print("Disconnection from UCLouvain-prive\n");
		execute_action(ACTION_DISCONNECT);
		log_event(LOG_STOP_CONNECTION_LOOP, NULL);
		sleep(DELAY);
		
		
		//student.UCLouvain
		debug_print("Connect to student.UCLouvain\n");
		log_event(LOG_START_CONNECTION_LOOP, NULL);
		execute_action(ACTION_CONNECT_STUDENT);
		services_loop();
		sleep(DELAY);
		log_event(LOG_FINAL_STOP_CONNECTION_LOOP, NULL);
		log_event(LOG_STOP_CONNECTION, NULL);

		if(close == 1) {
			debug_print("SAVE\n");
			log_event(LOG_FINAL_STOP_LOOP, NULL);
			log_event(LOG_STOP_LOG, NULL);
			log_event(LOG_STOP_FILE, NULL);
			fclose(f);
			send_log();
			f = fopen("/var/log/logs2.txt","w");
			log_event(LOG_START_FILE, NULL);
			log_event(LOG_MAC_ADDR, NULL);
			log_event(LOG_START_LOG, NULL);
			close = 0;
		}
		else {
			log_event(LOG_STOP_LOOP, NULL);
			debug_print("Disconnection from student\n");
			execute_action(ACTION_DISCONNECT);
			sleep(DELAY);
			
		}
		
		
		close += 1;
	}
	return NULL;
}


int main(int argc, char ** argv) {
	system("killall hostapd"); //Kill hostapd in order to launch wpa_supplicant

	/* Get router mac address */
	FILE *tmp = popen("cat /sys/class/net/wlan0/address", "r");
	fgets(router_mac, 18, tmp);
	pclose(tmp);
	
	pthread_t wpa_thread, loop_thread;
	int r = 0;

	/* FILE */
	f = fopen("/var/log/logs.txt", "w");
	if(f == NULL) {
		debug_print("Error opening file\n");
		exit(1);
	}	
	r = pthread_create(&wpa_thread, NULL, wpa_loop, NULL);
	if(!r){
		while(1) {
			if(start_loop == 1) {
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
