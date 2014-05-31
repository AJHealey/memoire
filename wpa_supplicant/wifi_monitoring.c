/*
 * wifi_monitoring.c
 */

#include "wpa_ctrl/wpa_ctrl.h"
#include "wifi_monitoring.h"
#include <pthread.h>


#define DEBUG 1 /* Print debug messages */

/* 
 * 1: eduroam
 * 2: UCLouvain
 * 3: visiteurs.UCLouvain
 * 4: UCLouvain-prive
 * 5: student.UCLouvain
 */
#define NUM_OF_NETWORKS 5 /* Number of networks */
#define NUM_OF_LOOPS 5 /* Number of loops to execute before sending the log file */

/* 
 * Insert the log information into the log file.
 * Depending on the type of events received, the correct part handling the insertion is
 * executed in order to respect the JSON syntax.
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
				
				/* Last element cannot have a comma after the closing bracket */
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

				/* Display all the BSSIDs tried during the allocation phase */
				while(try != NULL) {
					fprintf(f, "\"%s\"", try->bssid);

					/* Last element cannot have a comma after the closing bracket */
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

				/* Display the list of all the APs the supplicant had a connection with*/
				while(connect != NULL) {
					fprintf(f, "\"%s\"", log_struct->connected->bssid);

					/* Last element cannot have a comma after the closing bracket */
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
				/* Services */
				fprintf(f, "\"services\": {\n");
				fprintf(f, "\"DNS_1\": \"%s\",\n", log_struct->services->DNS_1);
				fprintf(f, "\"DNS_2\": \"%s\",\n", log_struct->services->DNS_2);
				fprintf(f, "\"google.be\": \"%s\",\n", log_struct->services->google);
				fprintf(f, "\"facebook.com\": \"%s\",\n", log_struct->services->facebook);
				fprintf(f, "\"youtube.com\": \"%s\",\n", log_struct->services->youtube);
				fprintf(f, "\"be.yahoo.com\": \"%s\",\n", log_struct->services->yahoo);
				fprintf(f, "\"en.wikipedia.com\": \"%s\",\n", log_struct->services->wikipedia);
				fprintf(f, "\"twitter.com\": \"%s\",\n", log_struct->services->twitter);
				fprintf(f, "\"amazon.fr\": \"%s\",\n", log_struct->services->amazon);
				fprintf(f, "\"live.com\": \"%s\",\n", log_struct->services->live);
				fprintf(f, "\"linkedin.com\": \"%s\",\n", log_struct->services->linkedin);
				fprintf(f, "\"blogspot.com\": \"%s\",\n", log_struct->services->blogspot);
				fprintf(f, "\"gmail.be\": \"%s\",\n", log_struct->services->gmail);
				fprintf(f, "\"github.be\": \"%s\",\n", log_struct->services->github);
				fprintf(f, "\"uclouvain.be\": \"%s\",\n", log_struct->services->uclouvain);
				fprintf(f, "\"icampus.uclouvain.be\": \"%s\", \n", log_struct->services->icampus);
				fprintf(f, "\"moodleucl.uclouvain.be\": \"%s\",\n", log_struct->services->moodle);
				fprintf(f, "\"bib.ucl.ac.be\": \"%s\",\n", log_struct->services->libellule);
				fprintf(f, "\"horaire.sgsi.ucl.ac.be\": \"%s\",\n", log_struct->services->ade);
				fprintf(f, "\"studssh.info.uc.ac.be\": \"%s\"\n", log_struct->services->studssh);
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
			time(&now);
			tm = *localtime(&now);
			printf("\"date\": \"%d/%d/%d %d:%d:%d\",\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
			fprintf(f, "\"date\": \"%d/%d/%d %d:%d:%d\",\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
			break;
	}
}

/*
 * Parse all the event received from the wpa_supplicant daemon and execute actions accordingly.
 * Four messages are handled:
 *   - WPA_EVENT_CONNECTED 
 *   - Trying an association
 *   - Associated
 *   - WPA_EVENT_DISCONNECTED
 * The data concerning each message are stored into the different structures.
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

	/* 1st event: Connected to the network */
	if(match(event, WPA_EVENT_CONNECTED)) {
		char wpa_time[20];
		char dhcp_time[20];

		ftime(&wpa_end); /* Stop the wpa_supplicant timer */
		
		/*Get network BSSID */
		char bssid[18];
		memset(bssid, 0, 18);
		memcpy(bssid, &event[37], 17);
		
		/* 
		 * Inserting the data into the ap_connect and ap_time structures and linking
		 * those structures to the main log_struct.
		 * This part keeps track of all the possible reconnection made with APs.
		 */
		struct ap_connect *ptr = (struct ap_connect*) malloc (sizeof(struct ap_connect));
		struct ap_time *time = (struct ap_time*) malloc (sizeof(struct ap_time));
		log_struct->connected = ptr;
		log_struct->time = time;
		ptr->bssid = malloc(strlen(bssid)+1);

		/* First connection to an AP */
		if(first_connect == NULL) {
			strcpy(ptr->bssid, bssid);
			ptr->next = NULL;
			first_connect = curr_connect = ptr;
			first_connect->num = 1;
		}
		/* Reconnections to other APs */
		else {
			strcpy(ptr->bssid, bssid);
			first_connect->num += 1;
			ptr->next = NULL;
			curr_connect->next = ptr;
			curr_connect = ptr;
		}
		
		/* 
		 * Start udhcpc to receive an IP address from the DHCP servers.
		 * Starting the udhcpc timer and stopping it as soon as the address is received.
		 */ 
		ftime(&dhcp_start);
		system("udhcpc -t 0 -i wlan0 -C");
		ftime(&dhcp_end);
		
		timeDiff(wpa_start, wpa_end, &time->wpa_time); /* Compute the time wpa_supplicant took to connect */
		timeDiff(dhcp_start, dhcp_end, &time->dhcp_time); /* Compute the time to get an IP address */
		dhcp = 1; 
	}
	
	/* 2nd event: Trying to associate with an AP */
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

		/* 
		 * Inserting the data into the ap_tried and linking these structure to the main log_struct.
		 * This part keeps track of all the APs the supplicant tried to associate with.
		 */
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

	/* 3rd event: Associated with an AP */
	else if(match(event, "Associated")) {
		char bssid[18];
		/*Get network BSSID*/
		memset(bssid, 0, 18);
		memcpy(bssid, &event[16], 17);

		/* Store the ssid of the network inside the main struct for the creation of the log file */
		log_struct->ssid = malloc(strlen(ssid_log)+1);
		strcpy(log_struct->ssid, ssid_log);
	}

	/* 
	 * 4th event: WPA_EVENT_DISCONNECTED
	 * Sometimes the supplicant is abruptly disconnected from the AP and is forced to reauthenticate 
	 * and establish a connection with another AP.
	 * This part is only to safely stop the connection by releasing the IP address.
	 */
	else if(match(event, WPA_EVENT_DISCONNECTED)) {
		system("killall udhcpc"); /* Stop DHCP */
		dhcp = 0;
	}
}

/*
 * Executes the correct function requested by the action received.
 */
static void execute_action(enum wpa_action action, int network) {
	switch(action) {
		/* Connect to the network with id equals to the 'network' parameter */
		case ACTION_CONNECT:
			connect_network(network);
			break;

		/* Disconnect from the current networks */
		case ACTION_DISCONNECT: {
				commands("DISCONNECT");
				system("killall udhcpc"); /* Stop DHCP */
				dhcp = 0;
			}
			break;

		/* Create all the networks needed to start the monitoring process */
		case ACTION_CREATE_NETWORKS:
			create_networks();
			break;
	}
}

/*
 * This function is used to send a command to the wpa_supplicant interface.
 */
static void commands(char *cmd)
{
	char reply[BUF];
	size_t len;
	int ret;
	
	/* No control interface has been found */
	if(ctrl == NULL) {
		exit(-1);
	}
	ret = wpa_ctrl_request(ctrl, cmd, os_strlen(cmd), reply, &len, NULL);
	if(ret < 0) {
		/* Wpa_supplicant timed out. Restart command */
		commands(cmd);
		
	}
}




/*
 * Create the networks in two steps:
 *   - First, it adds 'NUM_OF_NETWORKS' networks in the control interface with empty configuration
 *   - Second, all the added networks are configured by calling the function config_network() with a set of
 *     parameters.
 */
static void create_networks() {
	int i;

	/* 1) Add the networks */
	for(i = 0; i < NUM_OF_NETWORKS; i++) {
		commands("ADD_NETWORK");
	}

	/* 2) Configrue the networks */
	config_network(0, "eduroam", "WPA-EAP", "PEAP", "CCMP", "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", "peaplabel=0", "auth=MSCHAPV2");

	config_network(1, "UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP");
	
	config_network(2, "visiteurs.UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP");

	config_network(3, "UCLouvain-prive", "NONE", NULL, NULL, NULL, NULL, NULL, NULL, NULL);

	config_network(4, "student.UCLouvain", "WPA-EAP", "TTLS", NULL, "ingi1@wifi.uclouvain.be", "OLIelmdrad99", "/etc/wpa_supplicant/chain-radius.pem", NULL, "auth=PAP");

}


/*
 * Configure the network by sending commands to wpa_supplicant with special variables and parameters
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
 * A connection to the network with ID 'network' is started. 
 * The desired network needs to be previously added and configured.
 */
static void connect_network(int network) {
	char date[19];
	char command[16];
	/* Insert the date in the log struct */
	time(&now);
	tm = *localtime(&now);
	sprintf(date, "%d/%d/%d %d:%d:%d", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
	log_struct->date = malloc(strlen(date)+1);
	strcpy(log_struct->date, date);	

	sprintf(command, "SELECT_NETWORK %d", network);
	ftime(&wpa_start); /* Starting the wpa_supplicant timer */
	commands(command);
	/* Wait until the entire connection establishment has been executed */
	while(dhcp != 1) {
		sleep(1);
	}
}

/* 
 * Checks if the DNS server with IP address 'host' is responding and is available.
 * A DNS query is sent to the server and the response is analyzed.
 */
static int checkDNS(char *host) {
	int ret;

	/* 
	 * Some abrupt disconnection might occur during the tests. In order to counter the problem we
	 * wait until a new IP address has been received before continuing the testings. 
	 * The function returns 0 if the DNS is reachable, -1 otherwise.
	 */
	while(dhcp != 1) {
		sleep(1);
	}

	ret = check_dns_response(host);
	if(ret == 0)
		printf("OK %s\n", host);
	else
		printf("NOK %s\n", host);
	return ret;
}


/* 
 * Check if the service 'host' is reachable and available.
 * TCP Sockets connection are used in order to test the connection.
 * The function returns 0 if the service is reachable, -1 otherwise.
 */
static int checkService(char *host, const char *port) {
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

	/* 
	 * Some abrupt disconnection might occur during the tests. In order to counter the problem we
	 * wait until a new IP address has been received before continuing the testings. 
	 */
	while(dhcp != 1) {
		sleep(1);
	}

	if((hostptr = (struct hostent *) gethostbyname(host)) == NULL) { 
		return -1;
	}
	host_name = host;
	ptr = (struct in_addr *)*(hostptr->h_addr_list);

	//Create communication endpoint
	if((sockfd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP))<0) { //TCP for websites
		close(sockfd);
		return -1;
	}

	memset((char *) &serv_addr, 0, sizeof(serv_addr));
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(port_number);
	serv_addr.sin_addr.s_addr = ptr->s_addr;


	//Non blocking socket
	arg = fcntl(sockfd, F_GETFL, NULL);
	arg |= O_NONBLOCK;
	fcntl(sockfd, F_SETFL, arg);

	//Trying to connect with timeout
	res = connect(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr));

	if(res < 0) {
		if(errno == EINPROGRESS) {
			tv.tv_sec = 3; // 3sec timeout
			tv.tv_usec = 0;
			FD_ZERO(&set);
			FD_SET(sockfd, &set);
			if(select(sockfd+1, NULL, &set, NULL, &tv) > 0) {
				len = sizeof(int);
				getsockopt(sockfd, SOL_SOCKET, SO_ERROR, (void *)(&valopt), &len);
				if(valopt) {
					//Error connection
					close(sockfd);
					return -1;
				}
			}
			else {
				//Time out 
				printf("NOK %s\n", host);
				close(sockfd);
				return -1;
			}
		}
		//connected
		printf("OK %s\n", host);
		close(sockfd);
		return 0;
	}
}

/*
 * Loop that check the availability and reachibilty of the services set.
 * The results for each service are stored into the check_serv structure.
 */
static void services_loop() {
	struct check_serv *ptr = (struct check_serv*) malloc (sizeof(struct check_serv));
	log_struct->services = ptr;
	ptr->DNS_1 = malloc(1);
	ptr->DNS_2 = malloc(1);
	ptr->google = malloc(1);
	ptr->facebook = malloc(1);
	ptr->youtube = malloc(1);
	ptr->yahoo = malloc(1);
	ptr->wikipedia = malloc(1);
	ptr->twitter = malloc(1);
	ptr->amazon = malloc(1);
	ptr->live = malloc(1);
	ptr->linkedin = malloc(1);
	ptr->blogspot = malloc(1);
	ptr->gmail = malloc(1);
	ptr->github = malloc(1);
	ptr->uclouvain = malloc(1);
	ptr->icampus = malloc(1);
	ptr->moodle = malloc(1);
	ptr->libellule = malloc(1);
	ptr->ade = malloc(1);
	ptr->studssh = malloc(1);

	if(checkDNS("130.104.1.1") == 0)
		strcpy(ptr->DNS_1, "1");
	else 
		strcpy(ptr->DNS_1, "0");

	if(checkDNS("130.104.1.2") == 0)
		strcpy(ptr->DNS_2, "1");
	else
		strcpy(ptr->DNS_2, "0");

	if(checkService("google.be", "443") == 0)
		strcpy(ptr->google, "1");
	else
		strcpy(ptr->google, "0");

	if(checkService("facebook.com", "80") == 0)
		strcpy(ptr->facebook, "1");
	else
		strcpy(ptr->facebook, "0");

	if(checkService("youtube.com", "443") == 0)
		strcpy(ptr->youtube, "1");
	else
		strcpy(ptr->youtube, "0");

	if(checkService("be.yahoo.com", "80") == 0)
		strcpy(ptr->yahoo, "1");
	else
		strcpy(ptr->yahoo, "0");

	if(checkService("en.wikipedia.org", "443") == 0)
		strcpy(ptr->wikipedia, "1");
	else
		strcpy(ptr->wikipedia, "0");

	if(checkService("twitter.com", "443") == 0)
		strcpy(ptr->twitter, "1");
	else
		strcpy(ptr->twitter, "0");

	if(checkService("amazon.fr", "443") == 0)
		strcpy(ptr->amazon, "1");
	else
		strcpy(ptr->amazon, "0");

	if(checkService("login.live.com", "443") == 0)
		strcpy(ptr->live, "1");
	else
		strcpy(ptr->live, "0");

	if(checkService("linkedin.com", "443") == 0)
		strcpy(ptr->linkedin, "1");
	else
		strcpy(ptr->linkedin, "0");

	if(checkService("blogger.com", "443") == 0)
		strcpy(ptr->blogspot, "1");
	else
		strcpy(ptr->blogspot, "0");

	if(checkService("smtp.gmail.com", "587") == 0)
		strcpy(ptr->gmail, "1");
	else
		strcpy(ptr->gmail, "0");

	if(checkService("github.com", "22") == 0)
		strcpy(ptr->github, "1");
	else
		strcpy(ptr->github, "0");

	if(checkService("uclouvain.be", "443") == 0)
		strcpy(ptr->uclouvain, "1");
	else
		strcpy(ptr->uclouvain, "0");

	if(checkService("icampus.uclouvain.be", "443") == 0)
		strcpy(ptr->icampus, "1");
	else
		strcpy(ptr->icampus, "0");

	if(checkService("moodleucl.uclouvain.be", "443") == 0)
		strcpy(ptr->moodle, "1");
	else
		strcpy(ptr->moodle, "0");

	if(checkService("bib.sipr.ucl.ac.be", "80") == 0)
		strcpy(ptr->libellule, "1");
	else
		strcpy(ptr->libellule, "0");

	if(checkService("horaire.sgsi.ucl.ac.be", "8080") == 0)
		strcpy(ptr->ade, "1");
	else
		strcpy(ptr->ade, "0");

	if(checkService("studssh.info.ucl.ac.be", "22") == 0)
		strcpy(ptr->studssh, "1");
	else
		strcpy(ptr->studssh, "0");
}

/*
 * Performs a scan of the networks in the surroundings of the router and stores the results 
 * into the scan_results structure.
 */
static void scan() {
	char *line, *saved_line, *object, *saved_object;
	char reply[BUF*12];
	size_t len = (BUF*12)-1;
	int i,ret;
	
	/* Perfoms a scan */
	commands("SCAN");
	/* Get and store the scan results inside a buffer */
	ret = wpa_ctrl_request(ctrl, "SCAN_RESULTS", os_strlen("SCAN_RESULTS"), reply, &len, NULL);
	if(ret < 0) {
		scan();
	}

	reply[len] = '\0';
	i = 0; 
	/* 
	 * Tokenize results, extract the information and stored them into the structure.
	 */
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
	/* Insert the scan results in the log file */
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
 * Saves the actual log file into a tmp file due to an error while trying to send the current log file.
 */
static void save_log_tmp() {
	FILE *tmp;
	char ch;
	tmp = fopen("/var/log/logs.txt", "r");
	tmp_log = fopen("/var/log/logs.tmp.txt", "w");
	while((ch = fgetc(tmp)) != EOF)
		fputc(ch, tmp_log);
	fclose(tmp);
	fclose(tmp_log);
}

/* 
 * Function that sends the log to the server. 
 * If the sending failed, the log file is saved into tmp file that is going to be sent the next
 * time as well as the current log file.
 */
static void send_log() {
	int ret;

	if(access("/var/log/logs.tmp.txt", F_OK) != -1) {
		ret = sendLogs("/var/log/logs.tmp.txt", router_mac);

		if(ret == -1) {
			debug_print("Error sending tmp file\n");
			debug_print("Trying to send current log file\n");

			ret = sendLogs("/var/log/logs.txt", router_mac);

			if (ret == -1) {
				save_log_tmp();
				debug_print("Error sending log file\n");
				debug_print("Log saved into tmp file\n");
			}
			else {
				debug_print("Log Sent\n");
			}
		}
		else {
			debug_print("Tmp log sent.\n");
			remove("/var/log/logs.tmp.txt");

			ret = sendLogs("/var/log/logs.txt", router_mac);
			if (ret == -1) {
				save_log_tmp();
				debug_print("Error sending log file\n");
				debug_print("Log saved into tmp file\n");
			}
			else {
				debug_print("Log Sent\n");
			}
		}
	} 
	else {
		ret = sendLogs("/var/log/logs.txt", router_mac);
		if(ret == -1) {
			save_log_tmp();
			debug_print("Error sending log file\n");
			debug_print("Log saved into tmp file\n");
		}
		else {
			debug_print("Log Sent\n");
		}
	}
}

/*
 * Free the main log structure and all the others after a connection and malloc a new 
 * one for another connection data gathering.
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

/*
 * First thread main function. 
 * The function starts the wpa_supplicant daemon, open a control interface and attach to it.
 * The networks are also created during this function.
 * The thread then waits for events sent by the daemon.
 */
void *wpa_loop(void *p_data) {
	char reply[BUF];
	size_t reply_len;
	int ctrl_fd, r, err;
	fd_set ctrl_fds;
	struct timeval timeout;

	/* Start wpa_supplicant */
	system("wpa_supplicant -B -D nl80211 -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf");

	/* Open the control interface */
	ctrl = wpa_ctrl_open(DEFAULT_CTRL_IFACE);
	if(ctrl == NULL) {
		debug_print("Unable to open wpa_supplicant control interface\n");
		exit(-1);
	}
	/* Attach to the control interface */
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
		/* Wait for an event */
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
			default: 
				/* Event received */
				reply_len = BUF-1;
				wpa_ctrl_recv(ctrl, reply, &reply_len);
				reply[reply_len] = '\0';
				printf("[-] %s\n",reply);
				parse_event(reply); /* Parse the event */
				break;
		}
	}
	wpa_ctrl_detach(ctrl);
	wpa_ctrl_close(ctrl);
	return NULL;
}

/*
 * Second thread main function.
 * The function handles the loop for connection establishments and services checking.
 * The function also takes care of sending the log file to the server once a connection loop
 * is ended.
 */ 
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
		scan(); /* Performs a networks scan */
		log_event(LOG_START_CONNECTION, NULL);

		/* Connections loop */
		for(i = 0; i<NUM_OF_NETWORKS; i++) {
			log_event(LOG_START_CONNECTION_LOOP, NULL);
			execute_action(ACTION_CONNECT, i); /* Connects to the network with ID 'i' */
			services_loop(); /* Executes the service checking loop */
			log_event(LOG_PRINT_STRUCT, NULL);
			sleep(DELAY);
			clear_struct(); /* Free the structures */

			if(i != NUM_OF_NETWORKS-1) { /* Last network needs special final closure for log syntax */
				log_event(LOG_STOP_CONNECTION_LOOP, NULL);
				execute_action(ACTION_DISCONNECT, 0);
			}
			else
				log_event(LOG_FINAL_STOP_CONNECTION_LOOP, NULL); /* Final closure */
			sleep(DELAY);
		}
		log_event(LOG_STOP_CONNECTION, NULL);
		if(close == NUM_OF_LOOPS-1) {
			log_event(LOG_FINAL_STOP_LOOP, NULL);
			log_event(LOG_STOP_LOG, NULL);
			log_event(LOG_STOP_FILE, NULL);
			fclose(f); /* Close log file */
			send_log(); /* Send log file to the server */
			execute_action(ACTION_DISCONNECT, 0);
			f = fopen("/var/log/logs.txt","w+"); /* Overwrite the log file */
			log_event(LOG_START_FILE, NULL);
			log_event(LOG_INFO_DATE, NULL);
			log_event(LOG_MAC_ADDR, router_mac);
			log_event(LOG_START_LOG, NULL);
			close = 0;
		}
		else {
			log_event(LOG_STOP_LOOP, NULL);
			execute_action(ACTION_DISCONNECT, 0);
			close += 1;	
		}
	}
	return NULL;
}


int main(int argc, char ** argv) {
	system("killall hostapd"); /* Kill hostapd in order to launch wpa_supplicant */

	/* Get router mac address */
	FILE *tmp = popen("cat /sys/class/net/wlan0/address", "r");
	fgets(router_mac, 18, tmp);
	pclose(tmp);
	
	pthread_t wpa_thread, loop_thread;
	int r = 0;

	/* Log file */
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
