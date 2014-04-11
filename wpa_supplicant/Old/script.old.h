static int open_connection(void);
static void close_connection(void);
static void boot_process(void);
static void printTimeDifference(void);
static void sendLog(void);
static int commands(char *cmd);
static void configNetwork(int network, char *ssid, char *key_mgmt, char *eap, char *pairwise, char *identity, char *password, char *ca_cert, char *phase1, char *phase2,  char *psk);
static void createNetworks(void);
static void loop(void);
