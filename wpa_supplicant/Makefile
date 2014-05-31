CC = mips-openwrt-linux-uclibc-gcc
LD = mips-openwrt-linux-uclibc-ld
OBJS = wifi_monitoring.o
LINKOBJS = wpa_ctrl/wpa_ctrl.o wpa_ctrl/os_unix.o wpa_ctrl/log_sender.o wpa_ctrl/utils.o wpa_ctrl/dns.o $(OBJS)
TARGET = wifi_monitoring

LDFLAGS = -lpthread

all: $(TARGET)

wpactrl:
	make -C wpa_ctrl

$(TARGET): wpactrl $(OBJS)
	$(CC) $(LINKOBJS) $(CFLAGS) $(LDFLAGS) $(LIBS) -o $(TARGET)

clean:
	make -C wpa_ctrl clean
	rm -f $(OBJS) $(TARGET)

%.o: %.c
	$(CC) -c $(CFLAGS) $< -o $@
