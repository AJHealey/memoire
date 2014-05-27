#include "wpa_ctrl/wpa_ctrl.h"
#include "script.h"
#include <pthread.h>

/* TODO 
 * - RAJOUTER DNS ET TCP DANS LES SCANS (nouvelles structures pour chaque service ?)
 */


#define DEBUG 1

/* Change the number of networks the router has to configure here
 * 1: eduroam
 * 2: UCLouvain
 * 3: visiteurs.UCLouvain
 * 4: UCLouvain-prive
 * 5: student.UCLouvain
 */
#define NUM_OF_NETWORKS 5

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
				fprintf(f, "\"frequency\": \"%s\",\n", ptr->freq);
				fprintf(f, "\"signal\": \"%s\",\n", ptr->signal);
				fprintf(f, "\"ssid\": \"%s\"\n", ptr->ssid);
				
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

		case LOG_PRINT_STRUCT: {
				struct ap_tried *try = first;
				struct ap_connect *connect = first_connect;
				log_struct->tried = try;
				log_struct->connected = connect;

				fprintf(f, "\"date\": \"%s\",\n", log_struct->date);

				fprintf(f, "\"ssid\": \"%s\",\n", log_struct->ssid);

				fprintf(f, "\"tried\": [ ");
				/* Display all the BSSID tried */
				while(try != NULL) {
					fprintf(f, "\"%s\"", try->bssid);
					/* JSON syntax */
					if(first->num != 1) {
						fprintf(f, ", ");
						first->num -= 1;
					}
					else
						fprintf(f, " ");
					try = try->next;
				}	
				fprintf(f, "],\n");
		
				fprintf(f, "\"connected\": [ ");
				/* Display the connection list */
				while(connect != NULL) {
					fprintf(f, "\"%s\"", log_struct->connected->bssid);
					/* JSON syntax */
					if(first_connect->num != 1) {
						fprintf(f, ", ");
						first_connect->num -= 1;
					}
					else
						fprintf(f, " ");
					connect = connect->next;
				}
				fprintf(f, "],\n");
		
				fprintf(f, "\"time\": {\n");
				fprintf(f, "\"wpa_supplicant\": \"%ldsec %.3ums\",\n", log_struct->time->wpa_time.time, log_struct->time->wpa_time.millitm);
				fprintf(f, "\"dhcp\": \"%ldsec %.3ums\"\n", log_struct->time->dhcp_time.time, log_struct->time->dhcp_time.millitm);
				fprintf(f, "},\n");

				fprintf(f, "\"services\": {\n");
				fprintf(f, "\"DNS_1\": \"%s\",\n", log_struct->services->DNS_1);
				fprintf(f, "\"DNS_2\": \"%s\",\n", log_struct->services->DNS_2);
				fprintf(f, "\"google.be\": \"%s\",\n", log_struct->services->google);
				fprintf(f, "\"gmail.be\": \"%s\",\n", log_struct->services->gmail);
				fprintf(f, "\"github.be\": \"%s\",\n", log_struct->services->github);
				fprintf(f, "\"ssl.github.be\": \"%s\",\n", log_struct->services->ssl_github);
				fprintf(f, "\"uclouvain.be\": \"%s\",\n", log_struct->services->uclouvain);
				fprintf(f, "\"icampus.uclouvain.be\": \"%s\"\n", log_struct->services->icampus);
				fprintf(f, "}\n");
				
			}
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

		case LOG_INFO_DATE:
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "\"date\": \"%d/%d/%d %d:%d:%d\",\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
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

	/* Connected to the network */
	if(match(event, WPA_EVENT_CONNECTED)) {
		char wpa_time[20];
		char dhcp_time[20];

		ftime(&wpa_end);
		
		/*Get network BSSID */
		char bssid[18];
		memset(bssid, 0, 18);
		memcpy(bssid, &event[37], 17);
		
		struct ap_connect *ptr = (struct ap_connect*) malloc (sizeof(struct ap_connect));
		struct ap_time *time = (struct ap_time*) malloc (sizeof(struct ap_time));
		log_struct->connected = ptr;
		log_struct->time = time;
		ptr->bssid = malloc(strlen(bssid)+1);

		/* First connection */
		if(first_connect == NULL) {
			strcpy(ptr->bssid, bssid);
			ptr->next = NULL;
			first_connect = curr_connect = ptr;
			first_connect->num = 1;
		}
		/* Reconnections */
		else {
			strcpy(ptr->bssid, bssid);
			first_connect->num += 1;
			ptr->next = NULL;
			curr_connect->next = ptr;
			curr_connect = ptr;
		}
		
		/* Start udhcpc to get an IP address */
		ftime(&dhcp_start);
		system("udhcpc -t 0 -i wlan0 -C");
		ftime(&dhcp_end);
		
		timeDiff(wpa_start, wpa_end, &time->wpa_time);
		timeDiff(dhcp_start, dhcp_end, &time->dhcp_time);

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
		log_struct->tried = ptr;
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

		log_struct->ssid = malloc(strlen(ssid_log)+1);
		strcpy(log_struct->ssid, ssid_log);
	}
}

/*
 * Execute the function w.r.t the special action received
 */
static void execute_action(enum wpa_action action, int network) {
	switch(action) {
		case ACTION_CONNECT:
			connect_network(network);
			break;

		case ACTION_DISCONNECT: {
				char cmd[17];
				int i;
				commands("DISCONNECT");
				system("killall udhcpc"); /* Stop DHCP */
				dhcp = 0;
			}
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
	for(i = 0; i < NUM_OF_NETWORKS; i++) {
		commands("ADD_NETWORK"); /* Create a network with no config for wpa_supplicant */
	}

	/* Add configuration to the created networks */
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

static void connect_network(int network) {
	char date[19];
	char command[16];
	now = time(NULL);
	tm = *localtime(&now);
	sprintf(date, "%d/%d/%d %d:%d:%d", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
	log_struct->date = malloc(strlen(date)+1);
	strcpy(log_struct->date, date);	

	ftime(&wpa_start);
	sprintf(command, "SELECT_NETWORK %d", network);
	commands(command);
	while(dhcp != 1) {
		sleep(1);
	}
}

/*
 * DNS TEST
 */
static int checkDNS(char *ip_addr) {
	int res, sockfd;
	struct sockaddr_in dns;

	if((sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP))<0) {
		return 0;
	}	

	
	memset((char *) &dns, 0, sizeof(dns));
	dns.sin_family = AF_INET;
	dns.sin_port = htons(53);
	dns.sin_addr.s_addr = inet_addr(ip_addr);

	res = connect(sockfd, (struct sockaddr *) &dns, sizeof(dns));
	if(res < 0) {
		debug_print("DNS: NOK\n");
		return 0;
	}
	else {
		debug_print("DNS: OK\n");
		return 1;
	}
}


/* 
 * Check if services are available or not
 */
static int checkService(char *host, char *ip_addr, const char *port) {
	int res, valopt, sockfd;
	long arg;
	fd_set set;
	struct timeval tv;
	struct sockaddr_in serv_addr;
	char *host_name;
	struct hostent *hostptr;
	struct in_addr *ptr;
	unsigned short port_number;
	socklen_t len;

	port_number = atoi(port);

	if(host != NULL) {  
		if((hostptr = (struct hostent *) gethostbyname(host)) == NULL) { 
			return 0;
		}
		host_name = host;
		ptr = (struct in_addr *)*(hostptr->h_addr_list);
	}


	memset((char *) &serv_addr, 0, sizeof(serv_addr));
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(port_number);
	if(host != NULL) 
		serv_addr.sin_addr.s_addr = ptr->s_addr;
	else {
		serv_addr.sin_addr.s_addr = inet_addr(ip_addr);
	}


	//Non blocking socket
	arg = fcntl(sockfd, F_GETFL, NULL);
	arg |= O_NONBLOCK;
	fcntl(sockfd, F_SETFL, arg);

	//Trying to connect with timeout
	res = connect(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr));

	//Create communication endpoint
	if(host != NULL) { //Websites
		if((sockfd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP))<0) { //TCP for websites
			close(sockfd);
			return 0;
		}
	}
	else { //DNS
		if((sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP))<0) { //UDP for DNS
			close(sockfd);
			return 0;
		}
	}
	

	if(res < 0) {
		if(errno == EINPROGRESS) {
			tv.tv_sec = 10; // 5sec timeout
			tv.tv_usec = 0;
			FD_ZERO(&set);
			FD_SET(sockfd, &set);
			if(select(sockfd+1, NULL, &set, NULL, &tv) > 0) {
				len = sizeof(int);
				getsockopt(sockfd, SOL_SOCKET, SO_ERROR, (void *)(&valopt), &len);
				if(valopt) {
					//Error connection
					close(sockfd);
					return 0;
				}
			}
			else {
				//Time out 
				debug_print("NOK\n");
				close(sockfd);
				return 0;
			}
		}
		//connected
		printf("OK %s\n", port);
		close(sockfd);
		return 1;
	}
	else {
		//Error connection
		close(sockfd);
		return 0;
	}

	//Set to blocking again
	arg = fcntl(sockfd, F_GETFL, NULL);
	arg &= (~O_NONBLOCK);
	fcntl(sockfd, F_SETFL, arg);
	close(sockfd);
}

/*
 * Loop to check availability
 */
static void services_loop() {
	struct check_serv *ptr = (struct check_serv*) malloc (sizeof(struct check_serv));
	log_struct->services = ptr;
	ptr->DNS_1 = malloc(1);
	ptr->DNS_2 = malloc(1);
	ptr->google = malloc(1);
	ptr->gmail = malloc(1);
	ptr->github = malloc(1);
	ptr->ssl_github = malloc(1);
	ptr->uclouvain = malloc(1);
	ptr->icampus = malloc(1);

	if(checkService(NULL, "130.104.1.1", "53") == 1)
		strcpy(ptr->DNS_1, "1");
	else 
		strcpy(ptr->DNS_1, "0");

	if(checkService(NULL, "130.104.1.2", "53") == 1)
		strcpy(ptr->DNS_2, "1");
	else
		strcpy(ptr->DNS_2, "0");

	if(checkService("google.be", NULL, "443") == 1)
		strcpy(ptr->google, "1");
	else
		strcpy(ptr->google, "0");

	if(checkService("smtp.gmail.com", NULL, "587") == 1)
		strcpy(ptr->gmail, "1");
	else
		strcpy(ptr->gmail, "0");

	if(checkService("github.com", NULL, "22") == 1)
		strcpy(ptr->github, "1");
	else
		strcpy(ptr->github, "0");

	if(checkService("ssl.github.com", NULL, "443") == 1)
		strcpy(ptr->ssl_github, "1");
	else
		strcpy(ptr->ssl_github, "0");

	if(checkService("uclouvain.be", NULL, "443") == 1)
		strcpy(ptr->uclouvain, "1");
	else
		strcpy(ptr->uclouvain, "0");

	if(checkService("icampus.uclouvain.be", NULL, "443") == 1)
		strcpy(ptr->icampus, "1");
	else
		strcpy(ptr->icampus, "0");
}

/*
 * Scan for networks and get results
 */
static void scan() {
	char *line, *saved_line, *object, *saved_object;
	char reply[BUF*12];
	size_t len = (BUF*12)-1;
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
	if(sendLogs("/var/log/logs.txt", router_mac) < 0)
		debug_print("Error sending log file\n");
}

/*
 * Free the log structure after a connection and malloc a new one for another connection
 */
static void clear_struct() {
	struct ap_tried *tmp_try;
	struct ap_connect *tmp_connect;

	while (first != NULL) {
		tmp_try = first;
		first = tmp_try->next;
		free(tmp_try);
	}

	while (first_connect != NULL) {
		tmp_connect  = first_connect;
		first_connect = tmp_connect->next;
		free(tmp_connect);
	}

	free(log_struct->time);
	free(log_struct->services);
	free(log_struct);

	log_struct = (struct log *) malloc (sizeof(struct log));
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
	execute_action(ACTION_CREATE_NETWORKS, 0);
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
	log_struct = (struct log*) malloc (sizeof(struct log));
	int close = 0;
	int i;
	log_event(LOG_START_FILE, NULL);
	log_event(LOG_INFO_DATE, NULL);
	log_event(LOG_MAC_ADDR, router_mac);
	log_event(LOG_START_LOG, NULL);
	

	while(1) {
		log_event(LOG_START_LOOP, NULL);
		scan();
		log_event(LOG_START_CONNECTION, NULL);

		for(i = 0; i<NUM_OF_NETWORKS; i++) {
			log_event(LOG_START_CONNECTION_LOOP, NULL);
			execute_action(ACTION_CONNECT, i);
			services_loop();
			log_event(LOG_PRINT_STRUCT, NULL);
			sleep(DELAY);
			clear_struct();

			if(i != NUM_OF_NETWORKS-1) { /* Last network tested needs special final closure in log syntax */
				log_event(LOG_STOP_CONNECTION_LOOP, NULL);
				execute_action(ACTION_DISCONNECT, 0);
			}
			else
				log_event(LOG_FINAL_STOP_CONNECTION_LOOP, NULL); /* Final closure */
			sleep(DELAY);
		}
		log_event(LOG_STOP_CONNECTION, NULL);

		if(close == 0) {
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
			execute_action(ACTION_DISCONNECT, 0);
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
