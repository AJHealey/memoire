#include "includes.h"

int connect_to_server(const char *host, const char *port) {
	struct addrinfo hints;
	struct addrinfo *result;
	int s, socketfd, optval;
	
	//Get machine name in IPv4 address
	memset(&hints, 0, sizeof(hints));
	hints.ai_family = AF_INET; //IPv4
	hints.ai_family = SOCK_STREAM; 
	hints.ai_protocol = IPPROTO_TCP;
	
	s = getaddrinfo(host, port, &hints, &result);
	if(s != 0) {
		fprintf(stderr, "Error in getaddrinfo: %s\n", gai_strerror(s));
		freeaddrinfo(result);
		return -1;
	}
	//Create Socket
	if((socketfd = socket(PF_INET, SOCK_STREAM, 0)) <  0) {
		fprintf(stderr, "Socket Error: %s\n", strerror(errno));
		freeaddrinfo(result);
		return -1;
	}
	optval = 1;
	setsockopt(socketfd, SOL_SOCKET, SO_OOBINLINE, &optval, sizeof(optval));
	//Connection
	if(connect(socketfd, result->ai_addr, result->ai_addrlen) < 0) {
		fprintf(stderr, "Connection Error: %s\n", strerror(errno));
		freeaddrinfo(result);
		return -1;
	}
	return socketfd;
}
