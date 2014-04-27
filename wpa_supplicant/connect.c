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
	memset(recvBuff,0,1024);

	if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("[-]Could not create socket.\n");
        return 1;
    }

	struct sockaddr_in to;
	to.sin_family = AF_INET;
	to.sin_addr.s_addr = inet_addr(SERVERADDRESS);
	to.sin_port = htons(SERVERPORT);

	if (connect(sockfd, (struct sockaddr *)&to , sizeof(to)) < 0){
		perror("[-] Connection error.");
		return 1;
	}

	RSA *privateKey = getPrivateKey();

	// Phase 1 : Probe send its identity
	write(sockfd, IDENTITY, strlen(IDENTITY)); 

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

	// Phase 4 : Data Transmission
	EVP_CIPHER_CTX *ctx;
	int len, ciphertext_len;
	char *plaintext = "test";
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

	write(sockfd, ciphertext, ciphertext_len);


	// Phase 5 : Integrity check
	char integrityHash[32];
	SHA256(ciphertext, ciphertext_len, integrityHash);

	int i;
	printf("[*] SHA256: ");
	for(i = 0; i<32; i++) {
		printf("%x ", integrityHash[i] & 0xff);
	} 
	printf("\n");
	
	int tmp = write(sockfd, integrityHash, 32);
	printf("%d\n", tmp);


	read(sockfd, recvBuff, 2);
	// Free all the malloc !
	EVP_CIPHER_CTX_free(ctx);
	free(decryptedAESKey);
	free(decryptedIV);
	free(ciphertext);
	close(sockfd);

	// DEBUG
	/*
	int i;
	printf("[*] Decyphered AES key: ");
	for(i = 0; i<32; i++) {
		printf("%x ", decryptedAESKey[i] & 0xff);
	} 
	printf("\n");
	*/

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