#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <openssl/rsa.h>
#include <openssl/evp.h>
#include <openssl/sha.h>
#include <string.h>
#include <stdio.h>


RSA * getPrivateKey();

#define KEYFILE "probe1Key.pem"
#define IDENTITY "1"
#define SERVERADDRESS "127.0.0.1"
#define SERVERPORT 45678

int main(int argc, char *argv[]) {
	int sockfd = 0;
	char recvBuff[1024];
	memset(recvBuff,'\0',1024);

	if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("[-]Could not create socket.\n");
        return 1;
    }

	struct sockaddr_in to;
	to.sin_family = AF_INET;
	to.sin_addr.s_addr = inet_addr(SERVERADDRESS);
	to.sin_port = htons(SERVERPORT);

	if (connect(sockfd, (struct sockaddr *)&to , sizeof(to)) < 0){
		perror("[-]Could not connect to the server.\n");
        return 1;
	}

	RSA *privateKey = getPrivateKey();

	//printf("[*] Phase 1\n");
	// Phase 1 : Probe send its identity
	write(sockfd, IDENTITY, 1); 

	//printf("[*] Phase 2 & 3\n");
	// Phase 2 : Reception of the encrypted AES key
	read(sockfd, recvBuff, 256);
	// Decryption of the AES key
	char *decryptedAESKey = (char *)malloc(256);
	memset(decryptedAESKey,0,256);
	int result = RSA_private_decrypt(256,recvBuff,decryptedAESKey,privateKey,RSA_NO_PADDING);


	// Phase 3 : Reception of the encrypted IV 
	read(sockfd, recvBuff, 256);
	// Decryption of the IV
	char *decryptedIV = (char *)malloc(256);
	memset(decryptedIV,0,256);
	result = RSA_private_decrypt(256,recvBuff,decryptedIV,privateKey,RSA_NO_PADDING);

	//printf("[+] AES + IV received.\n");
	write(sockfd, "1", 1);
	
	
	// Phase 4 : Data Transmission
	//printf("[*] Phase 4\n");
	EVP_CIPHER_CTX *ctx;
	int len, ciphertext_len;
	char *plaintext = "{:}}";

	char *ciphertext = (char *)malloc(strlen(plaintext) + 16);

	if( !(ctx = EVP_CIPHER_CTX_new()) ) {
		// Unable to initialize
		return 1;
	}

	if(1 != EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, decryptedAESKey+224, decryptedIV+240)) {
		// Erreur while first dtep encryption
		return 1;
	}

	if(1 != EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, strlen(plaintext))) {
    	// Error while encryption
    	return 1;
	}
  	ciphertext_len = len;

	if(1 != EVP_EncryptFinal_ex(ctx, ciphertext + len, &len)) {
		// Error while finalizing the encryption
		return 1;
	} 
  	ciphertext_len += len;


	// Send data size
	write(sockfd, &ciphertext_len, 4); 
	read(sockfd, recvBuff, 1);
	//printf("[+] Size Acked.\n");

	// Send Data
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