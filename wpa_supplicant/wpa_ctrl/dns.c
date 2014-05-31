/*
 * Author: kay ~ irc.nullnetwork.net
 * Date: 2006-08-31
 * Source: http://neverfear.org/files/download/67
 */

#include "includes.h"

#define PORT           53
#define BUFLEN         511
#define QTYPE_A        1
#define QCLASS_IN      1


struct dns_header {
    short int id;
    short int flags;
    short int qdcount;
    short int ancount;
    short int nscount;
    short int arcount;
};

struct dns_question {
    char * qname;
    short int qtype;
    short int qclass;
};

typedef struct dns_header dns_header;
typedef struct dns_question dns_question;
typedef struct dns_resource dns_answer;
typedef struct dns_resource dns_authority;
typedef struct dns_resource dns_additional;

int sendallto(int fd, char * data, int datalen, struct sockaddr_in * dest) {
    int sendlen = datalen, num_of_bytes;    
    while (sendlen > 0) {

        if ((num_of_bytes = sendto(fd, data + (datalen - sendlen), sendlen, 0, (struct sockaddr *)dest, sizeof(struct sockaddr))) == -1) {
            return -1;
        }
        sendlen -= num_of_bytes;
    }
    return 0;
}

int make_query(int fd, short int flags, struct sockaddr_in dest_addr, dns_question query) {
    dns_header qhead;
    char buf[BUFLEN];
    int buflen     = 0;
    int octetlen   = 0;
    char * dotptr  = NULL;
    char * hostptr = query.qname; //Service address
        
    memset(buf, 0, BUFLEN);
    
    qhead.id      = (unsigned short) htons(getpid());
    qhead.flags   = htons(flags); 
    qhead.qdcount = htons(0x0001);
    qhead.ancount = 0;
    qhead.nscount = 0;
    qhead.arcount = 0;
    
    buflen = sizeof(qhead);
    memcpy(buf, (void*)&qhead, buflen);
    
    do {
        dotptr = strchr(hostptr, '.');
        
        if (!dotptr)
            octetlen = strchr(hostptr,'\0') - hostptr;
        else 
            octetlen = dotptr - hostptr;
        
        buf[buflen++] = octetlen;
        strncpy(buf + buflen, hostptr, octetlen);
        buflen += octetlen;
        hostptr = dotptr + 1;
    } while(dotptr);
    
    memset(buf + buflen, 0, 2);
    buflen += 2;
    //qtype
    query.qtype = query.qtype;
    query.qclass = query.qclass;
    memcpy((void*)buf + buflen, (void*)&(query.qtype), sizeof(short));
    buflen += 2;
    //qclass
    memcpy((void*)buf + buflen, (void*)&(query.qclass), sizeof(short));
    buflen += 2;
    
    sendallto(fd, buf, buflen, &dest_addr);
    
    return 0;
}


int read_responce(int fd, struct sockaddr_in dest_addr) {
    int               num_of_bytes = 0;
    char              buf[BUFLEN];
    unsigned int      buflen = 0;
    dns_header        dns_head;
    dns_question      dns_quest;
    dns_authority *   dns_auth;
    dns_answer *      dns_ans;
    dns_additional *  dns_add;
    int               offset = 0;
    char *            name;
    int               i;
    unsigned short int qr, opcode, aa, tc, rd, ra, z, rcode;

    if ((num_of_bytes = recvfrom(fd, buf, BUFLEN, 0, (struct sockaddr *)&dest_addr, &buflen)) == -1) {
        //Timeout or error
        return -1;
    }
    //Response received
    return 0;
}


int check_dns_response(char *host) {
    
    int                sockfd, ret;
    struct sockaddr_in dest_addr;
    dns_question       q;
    char *             service;
    short int          qclass = QCLASS_IN;
    short int          qtype  = QTYPE_A;
    short int          flags  = 0x0100;
    struct timeval     tv;

    tv.tv_sec = 3; //3sec timeout for DNS response
    tv.tv_usec = 0;

    service = "google.be";
        
    sockfd = socket( AF_INET, SOCK_DGRAM, 0 );
    if (sockfd <= 0) {
        return -1;
    }

    setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, (char *)&tv, sizeof(struct timeval));;

    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port   = htons(53);
    dest_addr.sin_addr.s_addr = inet_addr(host);
    memset(&(dest_addr.sin_zero), '\0', 8);
    q.qtype = qtype;
    q.qclass = qclass;
    q.qname = service;
    make_query(sockfd, flags, dest_addr, q);
    ret = read_responce(sockfd, dest_addr);
    close(sockfd);
    
    return ret;
}