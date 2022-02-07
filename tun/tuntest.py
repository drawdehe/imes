from tuntap import TunTap

iface = 'LongGe'

# Create and configure a TUN interface
tun = TunTap(nic_type="Tun", nic_name="tun0")
tun.config(ip="192.168.1.10", mask="255.255.255.0", gateway="192.168.2.2")

# Read from TUN interface
buf = tun.read(100)

# Write to TUN interface
tun.write(buf)

# Close and destroy interface
# tun.close()