
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <netdb.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <sys/socket.h>

#define PORT 45678
#define MAXDATASIZE 100
#define LENGTH 512

int main(int argc, char *argv []) {
	int sockfd, numbytes;
	char buf[MAXDATASIZE];
	struct sockaddr_in remote;

	if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
		printf("Error socket\n");
		exit(1);
	}

	remote.sin_family = AF_INET;
	remote.sin_port = htons(PORT);
	inet_pton(AF_INET, "192.168.1.8", &remote.sin_addr);
	bzero(&(remote.sin_zero), 8);

	if(connect(sockfd, (struct sockaddr *)&remote, sizeof(struct sockaddr)) == -1) {
		printf("Error connect\n");
		exit(1);
	}
	else
		printf("Connected to server at port %d\n", PORT);

	/* SEND FILE TO NETWORK */
	char *file_name = "log";
	char sendBuffer[LENGTH];
	printf("Sending...\n");
	FILE *file = fopen(file_name, "r");
	if(file_name == NULL) {
		printf("Error: file not found\n");
		exit(1);
	}
	bzero(sendBuffer, LENGTH);
	int file_size;
	while((file_size = fread(sendBuffer, sizeof(char), LENGTH, file)) > 0){
		if(send(sockfd, sendBuffer, file_size, 0) < 0) {
			fprintf(stderr, "Error: Failed to send file: %d\n", errno);
			break;
		}
		bzero(sendBuffer, LENGTH);
	}
	printf("File sent\n");
	close(sockfd);
	return 0;





	/*if((numbytes = recv(sockfd, buf, MAXDATASIZE, 0)) == -1) {
		printf("Error recv\n");
	}

	buf[numbytes] = '\0';
	printf("Recevied: %s\n", buf);
	close(sockfd);
	return 0;*/

}
