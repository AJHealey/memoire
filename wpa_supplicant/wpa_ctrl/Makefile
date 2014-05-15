CC = mips-openwrt-linux-uclibc-gcc
LD = mips-openwrt-linux-uclibc-ld
OBJS = wpa_ctrl.o os_unix.o log_sender.o utils.o
#OBJS = wpa_ctrl.o os_unix.o utils.o
CTRLFLAGS = -DCONFIG_CTRL_IFACE -DCONFIG_CTRL_IFACE_UNIX

CFLAGS = -I/home/cwayembergh/Documents/openwrt/openwrt/staging_dir/target-mips_r2_uClibc-0.9.33.2/usr/include 
LDFLAGS = -L/home/cwayembergh/Documents/openwrt/openwrt/staging_dir/target-mips_r2_uClibc-0.9.33.2/usr/lib -Wl,-rpath-link=/home/cwayembergh/Documents/openwrt/openwrt/staging_dir/target-mips_r2_uClibc-0.9.33.2/usr/lib -lcrypto

all: $(OBJS)

clean:
	rm -f $(OBJS) $(TARGET)

wpa_ctrl.o: common.h os.h wpa_debug.h wpabuf.h includes.h build_config.h wpa_ctrl.h wpa_ctrl.c
os_unix.o: os.h includes.h build_config.h os_unix.c
log_sender.o: includes.h log_sender.c
utils.o: includes.h utils.c

%.o: %.c
	$(CC) -c $(CFLAGS) $(LDFLAGS) $(CTRLFLAGS) $< -o $@

