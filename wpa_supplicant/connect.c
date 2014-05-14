#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include </usr/include/openssl/rsa.h>
#include <openssl/evp.h>
#include <openssl/sha.h>
#include <string.h>
#include <stdio.h>
#include <sys/stat.h> 
#include <fcntl.h>

RSA * getPrivateKey();
int sendLogs(char *);

#define KEYFILE "probe1Key.pem"
#define IDENTITY 1
#define SERVERADDRESS "130.104.78.201"
#define SERVERPORT 3874

int main(int argc, char *argv[]) {
	if(sendLogs("logs.txt") < 0)  {
		printf("Error\n");
	}
}

int sendLogs(char *filepath) {
	int sockfd = 0, identity = IDENTITY;
	char recvBuff[1024];
	memset(recvBuff,'\0',1024);

	// Create the socket
	if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("[-]Could not create socket.\n");
        return 1;
    }

    // Generate the socket information
	struct sockaddr_in to;
	to.sin_family = AF_INET;
	to.sin_addr.s_addr = inet_addr(SERVERADDRESS);
	to.sin_port = htons(SERVERPORT);

	if (connect(sockfd, (struct sockaddr *)&to , sizeof(to)) < 0){
		perror("[-]Could not connect to the server.\n");
        return 1;
	}

	// Get our private key
	RSA *privateKey = getPrivateKey();

	// #Phase 1 : Probe send our identity to the server
	write(sockfd, &identity, 4); 

	// #Phase 2 : Reception of the encrypted AES key
	read(sockfd, recvBuff, 256);
	// Decryption of the AES key
	char *decryptedAESKey = (char *)malloc(256);
	memset(decryptedAESKey,0,256);
	int result;
	if( (result=RSA_private_decrypt(256,recvBuff,decryptedAESKey,privateKey,RSA_NO_PADDING)) < 0) {
		// Fail to decrypt
		return -1;
	}

	// #Phase 3 : Reception of the encrypted IV 
	read(sockfd, recvBuff, 256);
	// Decryption of the IV
	char *decryptedIV = (char *)malloc(256);
	memset(decryptedIV,0,256);
	
	if( (result=RSA_private_decrypt(256,recvBuff,decryptedIV,privateKey,RSA_NO_PADDING)) < 0) {
		return -1;
	}
	// Send Ack to the server
	write(sockfd, "1", 1);
	
	// #Phase 4 : Data Transmission
	EVP_CIPHER_CTX *ctx;
	int len, ciphertext_len = 0;


	if( !(ctx = EVP_CIPHER_CTX_new()) ) {
		// Unable to initialize the cipher
		return -1;
	}

	if(1 != EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, decryptedAESKey+224, decryptedIV+240)) {
		// Erreur while first dtep encryption
		return -1;
	}

	int *fd = open(filepath, O_RDONLY);
	int logsize = lseek(fd,0,SEEK_END);
	lseek(fd,0,SEEK_SET);
	char *ciphertext = (char *)malloc(logsize + 16);

	int logread = 0;
	while( (logread=read(fd, recvBuff, 56)) > 0 ) {
		if(1 != EVP_EncryptUpdate(ctx, ciphertext + ciphertext_len, &len, recvBuff, logread)) {
	    	// Error while encryption
	    	return -1;
		}
		ciphertext_len += len;
	}
  	
	if(1 != EVP_EncryptFinal_ex(ctx, ciphertext + ciphertext_len , &len)) {
		// Error while finalizing the encryption
		return -1;
	} 
  	ciphertext_len += len;

	// Send ciphered data size
	write(sockfd, &ciphertext_len, 4); 
	// Wait ack from the server
	read(sockfd, recvBuff, 1);

	// Send encrypted data
	write(sockfd, ciphertext, ciphertext_len);

	// Free all the malloc !
	EVP_CIPHER_CTX_free(ctx);
	free(decryptedAESKey);
	free(decryptedIV);
	free(ciphertext);
	close(sockfd);

}

RSA * getPrivateKey() {
    FILE * fp = fopen(KEYFILE,"rb");
 
    if(fp == NULL) {
        printf("[-]Unable to open file %s \n", KEYFILE);
        return NULL;    
    }

    RSA *rsa = RSA_new();
    PEM_read_RSAPrivateKey(fp, &rsa,NULL, NULL);
 
    return rsa;
}
