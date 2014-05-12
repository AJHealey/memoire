#include "wpa_ctrl/wpa_ctrl.h"
#include "script.h"
#include <pthread.h>


/* 
 * Insert the logs into the logfile
 */
static void log_event(enum log_events log, const char *arg) {

	switch(log) {
		case LOG_START:
			fprintf(f, "{\n");
			now = time(NULL);
			tm = *localtime(&now);
			fprintf(f, "\t\"date\": \"%d/%d/%d %d:%d:%d\",\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
			break;

		case LOG_STOP:
			fprintf(f, "}\n");
			break;

		case LOG_SSID:
			fprintf(f, "\t\"ssid\": \"%s\",\n", arg);
			break;

		case LOG_TRIED: {
			struct ap_tried *ptr = first;
			fprintf(f, "\t\"tried\": [ ");
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
			fprintf(f, "\t\"connected\": \"%s\",\n", arg);
			fprintf(f, "\t\"time\": {\n");
			break;

		case LOG_WPA_TIME:
			fprintf(f, "\t\t\"wpa_supplicant\": \"%ldsec %.3ums\",\n", wpa_time.time, wpa_time.millitm);
			break;

		case LOG_DHCP_TIME:
			fprintf(f, "\t\t\"dhcp\": \"%ldsec %.3ums\"\n", dhcp_time.time, dhcp_time.millitm);
			fprintf(f, "\t},\n");
			break;

		case LOG_PING_START:
			fprintf(f, "\t\"ping\": {\n");
			break;

		case LOG_PING_GOOGLE:
			fprintf(f, "\t\t\"google\": \"%s\",\n", arg);
			break;

		case LOG_PING_GMAIL:
			fprintf(f, "\t\t\"gmail\": \"%s\",\n", arg);
			break;

		case LOG_PING_ADE:
			fprintf(f, "\t\t\"ade expert\": \"%s\",\n", arg);
			break;

		case LOG_PING_UCLOUVAIN:
			fprintf(f, "\t\t\"uclouvain\": \"%s\",\n", arg);
			break;

		case LOG_PING_ICAMPUS:
			fprintf(f, "\t\t\"icampus\": \"%s\",\n", arg);
			break;

		case LOG_PING_STOP:
			fprintf(f, "\t}\n");
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

/* Get IP address */
static char * get_ip() {
	int fd;
	struct ifreq ifr;
	fd = socket(AF_INET, SOCK_DGRAM, 0);
	ifr.ifr_addr.sa_family = AF_INET;
	strncpy(ifr.ifr_name, "wlan0", IFNAMSIZ-1);
	ioctl(fd, SIOCGIFADDR, &ifr);
	close(fd);
	return inet_ntoa(((struct sockaddr_in *)&ifr.ifr_addr)->sin_addr);
}

/* Get Destination IP address */
static char * dest_ip(const char *addr) {
	struct hostent *h;
	h = gethostbyname(addr);
	return inet_ntoa(*(struct in_addr *)h->h_addr);
}

unsigned short in_cksum(unsigned short *addr, int len) {
	register int sum = 0;
	u_short answer = 0;
	register u_short *w = addr;
	register int nleft = len;

	while(nleft > 1) {
		sum += *w++;
		nleft -= 2;
	}
	if(nleft == 1) {
		*(u_char *)(&answer) = *(u_char *)w;
		sum += answer;
	}
	sum = (sum >> 16) + (sum & 0xffff);
	sum += (sum >> 16);
	answer = ~sum;
	return (answer);
}

/*static void noresp(int ign) {
	printf("No response from %s\n", hostname);
}

static void ping(const char *host) {
	struct hostent *h;
	struct sockaddr_in pingaddr;
	struct icmp *pkt;
	int pingsock, c;
	char packet[DEFDATALEN + MAXIPLEN + MAXICMPLEN];
	
	if((pingsock = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)) < 0) {
		perror("Ping: creating a raw socket");
		exit(1);
	}

	memset(&pingaddr, 0, sizeof(struct sockaddr_in));
	
	pingaddr.sin_family = AF_INET;
	if(!(h = gethostbyname(host))) {
		fprintf(stderr, "ping: unknown host");
		exit(1);
	}

	memcpy(&pingaddr.sin_addr, h->h_addr, sizeof(pingaddr.sin_addr));
	hostname = h->h_name;

	pkt = (struct icmp *) packet;
	memset(pkt, 0, sizeof(packet));
	pkt->icmp_type = ICMP_ECHO;
	pkt->icmp_cksum = in_cksum((unsigned short *) pkt, sizeof(packet));
	
	c = sendto(pingsock, packet, sizeof(packet), 0, (struct sockaddr *) &pingaddr, sizeof(struct sockaddr_in));
	if(c < 0 || c != sizeof(packet)) {
		if(c < 0)
			perror("ping: sendto");
		fprintf(stderr, "ping: write incomplete\n");
		exit(1);
	}

	signal(SIGALRM, noresp);
	alarm(1);
	while(1) {
		struct sockaddr_in from;
		size_t fromlen = sizeof(from);
		
		if((c = recvfrom(pingsock, packet, sizeof(packet), 0, (struct sockaddr *)&from, &fromlen)) < 0) {
			if(errno == EINTR)
				continue;
			perror("ping: recvfrom");
			continue;
		}
		if(c >= 76) {
			struct iphdr *iphdr = (struct iphdr *)packet;
			pkt = (struct icmp *)(packet + (iphdr->ihl << 2));
			if(pkt->icmp_type == ICMP_ECHOREPLY)
				break;
		}
	}
	printf("%s is alive\n", hostname);
	return;

}


*/





/*
 * Ping method
 * Inspired from www.cboard.cprogramming.com/networking-device-communication/41635-ping-program.html
 */
static int ping(const char *addr) {
	char src[20];
	char dest[20];
	int sockfd, optval, addrlen, size;
	char *buf, *packet;
	struct iphdr *ip;
	struct iphdr *reply;
	struct icmphdr *icmp;
	struct sockaddr_in sock, connection;

	strncpy(src, get_ip(), 20); //Get router IP
	printf("1\n");
	strncpy(dest, addr, 20); //Get IP addr of destination
	printf("2\n");
	buf = malloc(sizeof(struct iphdr) + sizeof(struct icmphdr));
	printf("3\n");
	packet = malloc(sizeof(struct iphdr) + sizeof(struct icmphdr));
	printf("4\n");
	ip = (struct iphdr *) packet;
	printf("5\n");	
	icmp = (struct icmphdr *) (packet + sizeof(struct iphdr));
	printf("6\n");

	ip->ihl = 5;
	ip->version = 4;
	ip->tos = 0;
	ip->tot_len = sizeof(struct iphdr) + sizeof(struct icmphdr);
	ip->id = htons(0);
	ip->frag_off = 0;
	ip->ttl = 64;
	ip->protocol = IPPROTO_ICMP;
	ip->saddr = inet_addr(src);
	ip->daddr = inet_addr(dest);
	
	printf("7\n");
	if((sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)) == -1) {
		perror("Socket");
		exit(EXIT_FAILURE);
	}
	printf("8\n");	
	
	setsockopt(sockfd, IPPROTO_IP, IP_HDRINCL, &optval, sizeof(int));
	printf("9\n");
	icmp->type = ICMP_ECHO;
	icmp->code = 0;
	icmp->un.echo.id = random();
	icmp->un.echo.sequence = 0;
	icmp->checksum = in_cksum((unsigned short *)icmp, sizeof(struct icmphdr));
	ip->check = in_cksum((unsigned short *)ip, sizeof(struct iphdr));

	connection.sin_family = AF_INET;
	connection.sin_addr.s_addr = inet_addr(dest);
	printf("10\n");
	sendto(sockfd, packet, ip->tot_len, 0, (struct sockaddr *)&connection, sizeof(struct sockaddr));
	printf("11\n");
	addrlen = sizeof(connection);
	printf("12\n");
	if((size = recvfrom(sockfd, buf, sizeof(struct iphdr) + sizeof(struct icmphdr), 0, (struct sockaddr *)&connection, &addrlen)) == -1) {
		printf("13\n");
		free(packet);
		free(buf);
		close(sockfd);
		return -1;
		
	}
	else {
		printf("Received %d byte reply from %s:\n", size, dest);
		free(packet);
		free(buf);
		close(sockfd);
		return 0;
	}
}

static void ping_loop() {
	printf("PING\n");
	log_event(LOG_PING_START, NULL);
	ping("google.be");
	ping("icampus.uclouvain.be");
	/*if(ping_routine("194.78.0.59") == 0)
		log_event(LOG_PING_GOOGLE, "OK");
	else 
		log_event(LOG_PING_GOOGLE, "DOWN");
	if(ping_routine("173.194.34.150") == 0) 
		log_event(LOG_PING_GMAIL, "OK");
	else	
		log_event(LOG_PING_GMAIL, "DOWN");
	if(ping_routine("130.10.4.5.81")) 
		log_event(LOG_PING_ADE, "OK");
	else
		log_event(LOG_PING_ADE, "DOWN");
	if(ping_routine("130.104.5.100") == 0)
		log_event(LOG_PING_UCLOUVAIN, "OK");
	else
		log_event(LOG_PING_UCLOUVAIN, "DOWN");
	if(ping_routine("130.104.5.70") == 0)
		log_event(LOG_PING_ICAMPUS, "OK");
	else
		log_event(LOG_PING_ICAMPUS, "DOWN");
	log_event(LOG_PING_STOP, NULL);*/
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
				printf("[-] %s\n", reply);
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
	while(1) {
		ping_loop();
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
		printf("Connect to student.UCLouvain\n");
		execute_action(ACTION_CONNECT_STUDENT, NULL);
		sleep(DELAY);
		if(close == 1) {
			printf("SAVE\n");
			log_event(LOG_STOP, NULL);
			fclose(f);
			//TODO send file
			//TODO f = fopen("log.txt", "w");
			f = fopen("logs2.txt","w");
			close = 0;
		}
		close += 1;
	}
	return NULL;
}

//TODO supprimer
void *maison(void *p_data) {
	int close = 0;
	ping_loop();
	sleep(DELAY);
	printf("Deconnection\n");
	commands("DISABLE_NETWORK 0");
	dhcp = 0;

	while(1) {
		sleep(DELAY);
		log_event(LOG_START, NULL);
		commands("ENABLE_NETWORK 0");
		ftime(&wpa_start);
		printf("Connection\n");
		commands("SELECT_NETWORK 0");
		while(dhcp != 1) {
			sleep(1);
		}
		ping_loop();
		sleep(DELAY);
		printf("Deconnection\n");
		commands("DISABLE_NETWORK 0");
		dhcp = 0;
		if(close == 2) {
			printf("SAVE\n");
			log_event(LOG_STOP, NULL);
			fclose(f);
			f = fopen("logs2.txt", "w");
			
			close = 0;
		}
		close += 1;
	}
}



int main(int argc, char ** argv) {
	system("killall hostapd");
	pthread_t wpa_thread, loop_thread;
	int r = 0;

	/* FILE */
	f = fopen("logs.txt", "w");
	if(f == NULL) {
		printf("Error opening file\n");
		exit(1);
	}	
	
	r = pthread_create(&wpa_thread, NULL, wpa_loop, NULL);
	if(!r){
		while(1) {
			if(dhcp == 1) {
				printf("Starting loop\n");
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
