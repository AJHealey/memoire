CC = mips-openwrt-linux-uclibc-gcc
LD = mips-openwrt-linux-uclibc-ld
OBJS = wpa_ctrl.o os_unix.o log_sender.o utils.o dns.o
CTRLFLAGS = -DCONFIG_CTRL_IFACE -DCONFIG_CTRL_IFACE_UNIX

all: $(OBJS)

clean:
	rm -f $(OBJS) $(TARGET)

wpa_ctrl.o: common.h os.h wpa_debug.h wpabuf.h includes.h build_config.h wpa_ctrl.h wpa_ctrl.c
os_unix.o: os.h includes.h build_config.h os_unix.c
log_sender.o: includes.h log_sender.c
utils.o: includes.h utils.c
dns.o: includes.h

%.o: %.c
	$(CC) -c $(CFLAGS) $(LDFLAGS) $(CTRLFLAGS) $< -o $@

