int open_connection(void);
void close_connection(void);
void boot_process(void);
void printTimeDifference(void);
void sendLog(void);
int commands(char *cmd);
void configNetwork(int network, char *ssid, char *key_mgmt, char *eap, char *pairwise, char *identity, char *password, char *ca_cert, char *phase1, char *phase2,  char *psk);
void createNetworks(void);
void loop(void);
