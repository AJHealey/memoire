#include "includes.h"

#define SERVERADDRESS "130.104.78.201"
#define SERVERPORT 3874


int sendLogs(char *filepath, char *mac) {
	int sockfd;
	char identity[18];
	char recvBuff[1024];
	memset(recvBuff,'\0',1024);

	struct timeval timeout;
	long arg;
	int res, valopt;
	fd_set set;
	socklen_t len;

	strcpy(identity, mac);
	timeout.tv_sec = 3;
	timeout.tv_usec = 0;

	// Create the socket
	if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("[-]Could not create socket.\n");
        return -1;
    }

    arg = fcntl(sockfd, F_GETFL, NULL);
    arg |= O_NONBLOCK;
    fcntl(sockfd, F_SETFL, arg);

    // Generate the socket information
	struct sockaddr_in to;
	memset((char *) &to, 0, sizeof(to));
	to.sin_family = AF_INET;
	to.sin_addr.s_addr = inet_addr(SERVERADDRESS);
	to.sin_port = htons(SERVERPORT);



	res = connect(sockfd, (struct sockaddr *)&to , sizeof(to));


	if(res < 0) {
		if(errno == EINPROGRESS) {
			timeout.tv_sec = 3;
			timeout.tv_usec = 0;
			FD_ZERO(&set);
			FD_SET(sockfd, &set);
			if(select(sockfd+1, NULL, &set, NULL, &timeout) > 0) {
				len = sizeof(int);
				getsockopt(sockfd, SOL_SOCKET, SO_ERROR, (void*)(&valopt), &len);
				if(valopt) {
					fprintf(stderr, "Error in connection() %d - %s\n", valopt, strerror(valopt));
					sleep(5);
					close(sockfd);
					return -1;
				}
			}
			else {

				fprintf(stderr, "Timeout or error() %d - %s\n", valopt, strerror(valopt));
				sleep(5);
				close(sockfd);
				return -1;
			}
		}
		else {
			fprintf(stderr, "Error connecting %d - %s\n", errno, strerror(errno));
			sleep(5);
			close(sockfd);
			return -1;
		}
		
 	}

 	// Set to blocking mode again... 
  	arg = fcntl(sockfd, F_GETFL, NULL); 
  	arg &= (~O_NONBLOCK); 
  	fcntl(sockfd, F_SETFL, arg); 

 	/* Send log */
	/* Phase 1: The probe sends its identity to the server */
	if(write(sockfd, identity, sizeof(identity)) < 0) {
		perror("[-] Error sending identity");
		return -1;
	}
	/* Wait for an ack from the server*/
	read(sockfd, recvBuff, 1);

	/* Phase 2: Send data size */
	int fd = open(filepath, O_RDONLY);
	int logsize = htonl(lseek(fd, 0, SEEK_END));
	lseek(fd, 0, SEEK_SET);
	printf("SIZE: %d\n", logsize);
	if(write(sockfd, &logsize, 4) < 0) {
		perror("[-] Error sending data size");
		return -1;
	}
	/* Wait for an ack from the server */
	read(sockfd, recvBuff, 1);

	/* Phase 3: Send the data */
	int logread = 0;
	while((logread = read(fd, recvBuff, 56)) > 0) {
		if(write(sockfd, recvBuff, logread) < 0) {
			perror("[-] Error sending data");
			return -1;
		}
	}
	sleep(5);
	close(fd);
	close(sockfd);
	return 0;
}
