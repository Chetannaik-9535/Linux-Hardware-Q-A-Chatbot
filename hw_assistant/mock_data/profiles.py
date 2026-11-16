"""Realistic simulated Linux command outputs for different hardware profiles.

Profiles available:
1. thinkpad_x1: Lenovo ThinkPad X1 Carbon Gen 10
   - Intel Core i7-1260P (12 cores: 4P+8E, 16 threads)
   - 16 GB LPDDR5 Soldered RAM (Row of chips, no upgradeable slots, max 16 GB)
   - 512 GB NVMe SSD (Samsung PM9A1)
   - Intel Iris Xe Graphics
   - ThinkPad X1 Carbon Gen 10 motherboard, Phoenix BIOS

2. dell_xps: Dell XPS 15 9520
   - Intel Core i7-12700H (14 cores: 6P+8E, 20 threads)
   - 32 GB DDR5 RAM (2 of 2 slots used: 2x 16GB SODIMM, max capacity 64 GB, upgradeable by replacing modules)
   - 1 TB NVMe SSD (Micron 3400)
   - Intel Iris Xe + NVIDIA GeForce RTX 3050 Ti Laptop GPU (4 GB VRAM)
   - Dell Inc. 0HJ5R7 motherboard, Dell BIOS

3. gaming_desktop: Custom AMD Desktop Workstation
   - AMD Ryzen 9 5900X (12 cores, 24 threads)
   - 32 GB DDR4 RAM (2 of 4 slots used: 2x 16GB DIMM, 2 empty slots available, max capacity 128 GB)
   - Dual drives: 1 TB NVMe SSD (Samsung 980 PRO) + 4 TB SATA HDD (Seagate Barracuda)
   - NVIDIA GeForce RTX 4080 (16 GB VRAM)
   - ASUS ROG STRIX B550-F GAMING motherboard, AMI UEFI BIOS

4. acer_budget: Budget Laptop
   - AMD Ryzen 3 5300U (4 cores, 8 threads)
   - 8 GB DDR4 RAM (1 of 1 slot used: 1x 8GB SODIMM, 0 empty slots, max capacity 16 GB, upgradeable by replacement)
   - 256 GB SATA SSD (Kingston)
   - AMD Radeon Vega Graphics
   - Acer Aspire A515-45 motherboard, Insyde BIOS
"""

from __future__ import annotations

PROFILES: dict[str, dict[str, str]] = {
    "thinkpad_x1": {
        "lscpu": """Architecture:                         x86_64
CPU op-mode(s):                       32-bit, 64-bit
Address sizes:                        39 bits physical, 48 bits virtual
Byte Order:                           Little Endian
CPU(s):                               16
On-line CPU(s) list:                  0-15
Vendor ID:                            GenuineIntel
Model name:                           12th Gen Intel(R) Core(TM) i7-1260P
CPU family:                           6
Model:                                154
Thread(s) per core:                   2
Core(s) per socket:                   12
Socket(s):                            1
Stepping:                             3
CPU(s) scaling MHz:                   67%
CPU max MHz:                          4700.0000
CPU min MHz:                          400.0000
BogoMIPS:                             4992.00
Flags:                                fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb cat_l2 cdp_l2 ssbd ibrs ibpb stibp ibrs_enhanced tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid rdt_a rdseed adx smap clflushopt clwb intel_pt sha_ni xsaveopt xsavec xgetbv1 xsaves split_lock_detect avx_vnni dtherm ida arat pln pts hwp hwp_notify hwp_act_window hwp_epp hwp_pkg_req hreset umip pku ospke waitpkg gfni vaes vpclmulqdq tme rdpid movdiri movdir64b fsrm md_clear serialize pconfig arch_lbr flush_l1d arch_capabilities
Virtualization:                       VT-x
L1d cache:                            384 KiB (12 instances)
L1i cache:                            576 KiB (12 instances)
L2 cache:                             9 MiB (3 instances)
L3 cache:                             18 MiB (1 instance)
""",
        "free": """               total        used        free      shared  buff/cache   available
Mem:     16515858432  6124589056  4125892608   854126592  6265376768  10391269376
Swap:     8589934592           0  8589934592
""",
        "/proc/meminfo": """MemTotal:       16128768 kB
MemFree:         4029192 kB
MemAvailable:   10147724 kB
Buffers:          345672 kB
Cached:          5773120 kB
SwapCached:            0 kB
Active:          6245120 kB
Inactive:        4589120 kB
SwapTotal:       8388608 kB
SwapFree:        8388608 kB
Dirty:               128 kB
Writeback:             0 kB
AnonPages:       4715892 kB
Mapped:          1125890 kB
Shmem:            834108 kB
""",
        "lsblk": """{
   "blockdevices": [
      {
         "name": "nvme0n1",
         "size": "512G",
         "type": "disk",
         "mountpoint": null,
         "model": "SAMSUNG MZVL2512HCJQ-00BL7",
         "rota": false,
         "tran": "nvme",
         "fstype": null,
         "children": [
            {
               "name": "nvme0n1p1",
               "size": "512M",
               "type": "part",
               "mountpoint": "/boot/efi",
               "model": null,
               "rota": false,
               "tran": null,
               "fstype": "vfat"
            },
            {
               "name": "nvme0n1p2",
               "size": "480G",
               "type": "part",
               "mountpoint": "/",
               "model": null,
               "rota": false,
               "tran": null,
               "fstype": "ext4"
            },
            {
               "name": "nvme0n1p3",
               "size": "31.5G",
               "type": "part",
               "mountpoint": "[SWAP]",
               "model": null,
               "rota": false,
               "tran": null,
               "fstype": "swap"
            }
         ]
      }
   ]
}
""",
        "lspci": """Slot:	00:02.0
Class:	VGA compatible controller [0300]
Vendor:	Intel Corporation [8086]
Device:	Alder Lake-P Integrated Graphics Controller [46a6]
SVendor:	Lenovo [17aa]
SDevice:	ThinkPad X1 Carbon Gen 10 [22f4]
Rev:	0c

Slot:	00:14.0
Class:	USB controller [0c03]
Vendor:	Intel Corporation [8086]
Device:	Alder Lake PCH USB 3.2 xHCI Host Controller [51ed]
""",
        "lspci_driver": """00:02.0 VGA compatible controller: Intel Corporation Alder Lake-P Integrated Graphics Controller (rev 0c)
	Subsystem: Lenovo ThinkPad X1 Carbon Gen 10
	Kernel driver in use: i915
	Kernel modules: i915
""",
        "nvidia_smi": "",  # No NVIDIA GPU on ThinkPad X1
        "dmidecode_memory": """# dmidecode 3.4
Getting SMBIOS data from sysfs.
SMBIOS 3.4.0 present.

Handle 0x000E, DMI type 16, 23 bytes
Physical Memory Array
	Location: System Board Or Motherboard
	Use: System Memory
	Error Correction Type: None
	Maximum Capacity: 16 GB
	Error Information Handle: Not Provided
	Number Of Devices: 1

Handle 0x000F, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x000E
	Error Information Handle: Not Provided
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 16 GB
	Form Factor: Row Of Chips
	Set: None
	Locator: Motherboard
	Bank Locator: Not Specified
	Type: LPDDR5
	Type Detail: Synchronous Unbuffered (Unregistered)
	Speed: 5200 MT/s
	Manufacturer: Samsung
	Serial Number: 00000000
	Asset Tag: 9876543210
	Part Number: K3LK4K40BM-BGCP
	Rank: 2
	Configured Memory Speed: 5200 MT/s
	Minimum Voltage: 0.5 V
	Maximum Voltage: 0.5 V
	Configured Voltage: 0.5 V
""",
        "dmidecode_baseboard": """# dmidecode 3.4
Getting SMBIOS data from sysfs.
SMBIOS 3.4.0 present.

Handle 0x0002, DMI type 2, 17 bytes
Base Board Information
	Manufacturer: LENOVO
	Product Name: 21CBCTO1WW
	Version: ThinkPad X1 Carbon Gen 10
	Serial Number: L1HF1234567

Handle 0x0000, DMI type 0, 26 bytes
BIOS Information
	Vendor: LENOVO
	Version: N3AET75W (1.40 )
	Release Date: 09/18/2023
	Address: 0xE0000
	Runtime Size: 128 kB
	ROM Size: 32 MB
""",
        "/sys/class/dmi/id": {
            "sys_vendor": "LENOVO",
            "product_name": "21CBCTO1WW",
            "product_version": "ThinkPad X1 Carbon Gen 10",
            "board_vendor": "LENOVO",
            "board_name": "21CBCTO1WW",
            "bios_vendor": "LENOVO",
            "bios_version": "N3AET75W (1.40 )",
            "bios_date": "09/18/2023",
        },
    },
    "dell_xps": {
        "lscpu": """Architecture:                         x86_64
CPU op-mode(s):                       32-bit, 64-bit
Address sizes:                        39 bits physical, 48 bits virtual
Byte Order:                           Little Endian
CPU(s):                               20
On-line CPU(s) list:                  0-19
Vendor ID:                            GenuineIntel
Model name:                           12th Gen Intel(R) Core(TM) i7-12700H
CPU family:                           6
Model:                                154
Thread(s) per core:                   2
Core(s) per socket:                   14
Socket(s):                            1
Stepping:                             3
CPU max MHz:                          4700.0000
CPU min MHz:                          400.0000
Flags:                                fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand avx2 smep bmi2 erms invpcid rdseed adx smap
L1d cache:                            544 KiB (14 instances)
L1i cache:                            768 KiB (14 instances)
L2 cache:                             11.5 MiB (5 instances)
L3 cache:                             24 MiB (1 instance)
""",
        "free": """               total        used        free      shared  buff/cache   available
Mem:     33421770752 11811160064  9663676416  1073741824 11946934272 20545191936
Swap:    17179869184           0 17179869184
""",
        "/proc/meminfo": """MemTotal:       32638448 kB
MemFree:         9437184 kB
MemAvailable:   20063664 kB
Buffers:          456789 kB
Cached:         11490145 kB
SwapTotal:      16777216 kB
SwapFree:       16777216 kB
""",
        "lsblk": """{
   "blockdevices": [
      {
         "name": "nvme0n1",
         "size": "1T",
         "type": "disk",
         "mountpoint": null,
         "model": "Micron 3400 NVMe 1024GB",
         "rota": false,
         "tran": "nvme",
         "fstype": null,
         "children": [
            {
               "name": "nvme0n1p1",
               "size": "1G",
               "type": "part",
               "mountpoint": "/boot/efi",
               "model": null,
               "rota": false,
               "tran": null,
               "fstype": "vfat"
            },
            {
               "name": "nvme0n1p2",
               "size": "990G",
               "type": "part",
               "mountpoint": "/",
               "model": null,
               "rota": false,
               "tran": null,
               "fstype": "ext4"
            },
            {
               "name": "nvme0n1p3",
               "size": "32G",
               "type": "part",
               "mountpoint": "[SWAP]",
               "model": null,
               "rota": false,
               "tran": null,
               "fstype": "swap"
            }
         ]
      }
   ]
}
""",
        "lspci": """Slot:	00:02.0
Class:	VGA compatible controller [0300]
Vendor:	Intel Corporation [8086]
Device:	Alder Lake-P Integrated Graphics Controller [46a6]
SVendor:	Dell [1028]
SDevice:	XPS 15 9520 [0b19]
Rev:	0c

Slot:	01:00.0
Class:	3D controller [0302]
Vendor:	NVIDIA Corporation [10de]
Device:	GA107M [GeForce RTX 3050 Ti Mobile] [25a0]
SVendor:	Dell [1028]
SDevice:	XPS 15 9520 [0b19]
Rev:	a1
""",
        "lspci_driver": """00:02.0 VGA compatible controller: Intel Corporation Alder Lake-P Integrated Graphics Controller (rev 0c)
	Subsystem: Dell XPS 15 9520
	Kernel driver in use: i915
	Kernel modules: i915

01:00.0 3D controller: NVIDIA Corporation GA107M [GeForce RTX 3050 Ti Mobile] (rev a1)
	Subsystem: Dell XPS 15 9520
	Kernel driver in use: nvidia
	Kernel modules: nvidia_drm, nvidia
""",
        "nvidia_smi": "NVIDIA GeForce RTX 3050 Ti Laptop GPU, 550.54.14, 4096, 00000000:01:00.0\n",
        "dmidecode_memory": """# dmidecode 3.4
Getting SMBIOS data from sysfs.
SMBIOS 3.4.0 present.

Handle 0x002B, DMI type 16, 23 bytes
Physical Memory Array
	Location: System Board Or Motherboard
	Use: System Memory
	Error Correction Type: None
	Maximum Capacity: 64 GB
	Error Information Handle: Not Provided
	Number Of Devices: 2

Handle 0x002C, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x002B
	Error Information Handle: Not Provided
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 16 GB
	Form Factor: SODIMM
	Set: None
	Locator: ChannelA-DIMM0
	Bank Locator: BANK 0
	Type: DDR5
	Type Detail: Synchronous Unbuffered (Unregistered)
	Speed: 4800 MT/s
	Manufacturer: SK Hynix
	Serial Number: 4321A890
	Part Number: HMCG78MEBSA095N
	Rank: 1
	Configured Memory Speed: 4800 MT/s

Handle 0x002D, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x002B
	Error Information Handle: Not Provided
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 16 GB
	Form Factor: SODIMM
	Set: None
	Locator: ChannelB-DIMM0
	Bank Locator: BANK 1
	Type: DDR5
	Type Detail: Synchronous Unbuffered (Unregistered)
	Speed: 4800 MT/s
	Manufacturer: SK Hynix
	Serial Number: 4321A891
	Part Number: HMCG78MEBSA095N
	Rank: 1
	Configured Memory Speed: 4800 MT/s
""",
        "dmidecode_baseboard": """# dmidecode 3.4
Handle 0x0002, DMI type 2, 17 bytes
Base Board Information
	Manufacturer: Dell Inc.
	Product Name: 0HJ5R7
	Version: A00
	Serial Number: /8K2LM13/CN1296316D002B/

Handle 0x0000, DMI type 0, 26 bytes
BIOS Information
	Vendor: Dell Inc.
	Version: 1.15.0
	Release Date: 06/12/2023
""",
        "/sys/class/dmi/id": {
            "sys_vendor": "Dell Inc.",
            "product_name": "XPS 15 9520",
            "product_version": "",
            "board_vendor": "Dell Inc.",
            "board_name": "0HJ5R7",
            "bios_vendor": "Dell Inc.",
            "bios_version": "1.15.0",
            "bios_date": "06/12/2023",
        },
    },
    "gaming_desktop": {
        "lscpu": """Architecture:                         x86_64
CPU op-mode(s):                       32-bit, 64-bit
Address sizes:                        48 bits physical, 48 bits virtual
Byte Order:                           Little Endian
CPU(s):                               24
On-line CPU(s) list:                  0-23
Vendor ID:                            AuthenticAMD
Model name:                           AMD Ryzen 9 5900X 12-Core Processor
CPU family:                           25
Model:                                33
Thread(s) per core:                   2
Core(s) per socket:                   12
Socket(s):                            1
Stepping:                             0
Frequency boost:                      enabled
CPU max MHz:                          4950.0000
CPU min MHz:                          2200.0000
BogoMIPS:                             7386.42
Flags:                                fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm constant_tsc rep_good nopl nonstop_tsc cpuid extd_apicid aperfmperf rapl pni pclmulqdq monitor ssse3 fma cx16 sse4_1 sse4_2 movbe popcnt aes xsave avx f16c rdrand lahf_lm cmp_legacy svm extapic cr8_legacy abm sse4a misalignsse 3dnowprefetch osvw ibs skinit wdt tce topoext perfctr_core perfctr_nb bpext perfctr_llc mwaitx cpb cat_l3 cdp_l3 hw_pstate ssbd mba ibrs ibpb stibp vmmcall fsgsbase bmi1 avx2 smep bmi2 erms invpcid cqm rdt_a rdseed adx smap clflushopt clwb sha_ni xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local clzero irperf xsaveerptr rdpru wbnoinvd arat npt lbrv svm_lock nrip_save tsc_scale vmcb_clean flushbyasid decodeassists pausefilter pfthreshold avic v_vmsave_vmload vgif v_spec_ctrl umip pku ospke vaes vpclmulqdq rdpid overflow_recov succor smca fsrm
Virtualization:                       AMD-V
L1d cache:                            384 KiB (12 instances)
L1i cache:                            384 KiB (12 instances)
L2 cache:                             6 MiB (12 instances)
L3 cache:                             64 MiB (2 instances)
""",
        "free": """               total        used        free      shared  buff/cache   available
Mem:     33618685952  8245120000 18245120000   451200000  7128445952 24922365952
Swap:     4294967296           0  4294967296
""",
        "/proc/meminfo": """MemTotal:       32830748 kB
MemFree:        17817500 kB
MemAvailable:   24338248 kB
Buffers:          345678 kB
Cached:          6782768 kB
SwapTotal:       4194304 kB
SwapFree:        4194304 kB
""",
        "lsblk": """{
   "blockdevices": [
      {
         "name": "nvme0n1",
         "size": "931.5G",
         "type": "disk",
         "mountpoint": null,
         "model": "Samsung SSD 980 PRO 1TB",
         "rota": false,
         "tran": "nvme",
         "fstype": null,
         "children": [
            {
               "name": "nvme0n1p1",
               "size": "1G",
               "type": "part",
               "mountpoint": "/boot/efi",
               "model": null,
               "rota": false,
               "tran": null,
               "fstype": "vfat"
            },
            {
               "name": "nvme0n1p2",
               "size": "930.5G",
               "type": "part",
               "mountpoint": "/",
               "model": null,
               "rota": false,
               "tran": null,
               "fstype": "btrfs"
            }
         ]
      },
      {
         "name": "sda",
         "size": "3.6T",
         "type": "disk",
         "mountpoint": null,
         "model": "ST4000DM004-2CV104",
         "rota": true,
         "tran": "sata",
         "fstype": null,
         "children": [
            {
               "name": "sda1",
               "size": "3.6T",
               "type": "part",
               "mountpoint": "/mnt/storage",
               "model": null,
               "rota": true,
               "tran": null,
               "fstype": "ext4"
            }
         ]
      }
   ]
}
""",
        "lspci": """Slot:	01:00.0
Class:	VGA compatible controller [0300]
Vendor:	NVIDIA Corporation [10de]
Device:	AD103 [GeForce RTX 4080] [2704]
SVendor:	ASUSTeK Computer Inc. [1043]
SDevice:	GeForce RTX 4080 TUF Gaming [88a1]
Rev:	a1
""",
        "lspci_driver": """01:00.0 VGA compatible controller: NVIDIA Corporation AD103 [GeForce RTX 4080] (rev a1)
	Subsystem: ASUSTeK Computer Inc. GeForce RTX 4080 TUF Gaming
	Kernel driver in use: nvidia
	Kernel modules: nvidia_drm, nvidia
""",
        "nvidia_smi": "NVIDIA GeForce RTX 4080, 560.35.03, 16376, 00000000:01:00.0\n",
        "dmidecode_memory": """# dmidecode 3.4
Handle 0x001B, DMI type 16, 23 bytes
Physical Memory Array
	Location: System Board Or Motherboard
	Use: System Memory
	Error Correction Type: None
	Maximum Capacity: 128 GB
	Error Information Handle: Not Provided
	Number Of Devices: 4

Handle 0x001C, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x001B
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 16 GB
	Form Factor: DIMM
	Set: None
	Locator: DIMM_A1
	Bank Locator: BANK 0
	Type: DDR4
	Type Detail: Synchronous Unbuffered (Unregistered)
	Speed: 3600 MT/s
	Manufacturer: Corsair
	Part Number: CMW32GX4M2D3600C18
	Configured Memory Speed: 3600 MT/s

Handle 0x001D, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x001B
	Total Width: Unknown
	Data Width: Unknown
	Size: No Module Installed
	Form Factor: DIMM
	Set: None
	Locator: DIMM_A2
	Bank Locator: BANK 1
	Type: Unknown

Handle 0x001E, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x001B
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 16 GB
	Form Factor: DIMM
	Set: None
	Locator: DIMM_B1
	Bank Locator: BANK 2
	Type: DDR4
	Type Detail: Synchronous Unbuffered (Unregistered)
	Speed: 3600 MT/s
	Manufacturer: Corsair
	Part Number: CMW32GX4M2D3600C18
	Configured Memory Speed: 3600 MT/s

Handle 0x001F, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x001B
	Total Width: Unknown
	Data Width: Unknown
	Size: No Module Installed
	Form Factor: DIMM
	Set: None
	Locator: DIMM_B2
	Bank Locator: BANK 3
	Type: Unknown
""",
        "dmidecode_baseboard": """# dmidecode 3.4
Handle 0x0002, DMI type 2, 17 bytes
Base Board Information
	Manufacturer: ASUSTeK COMPUTER INC.
	Product Name: ROG STRIX B550-F GAMING
	Version: Rev 1.xx
	Serial Number: 210584739201948

Handle 0x0000, DMI type 0, 26 bytes
BIOS Information
	Vendor: American Megatrends Inc.
	Version: 3404
	Release Date: 12/28/2023
""",
        "/sys/class/dmi/id": {
            "sys_vendor": "ASUSTeK COMPUTER INC.",
            "product_name": "System Product Name",
            "product_version": "System Version",
            "board_vendor": "ASUSTeK COMPUTER INC.",
            "board_name": "ROG STRIX B550-F GAMING",
            "bios_vendor": "American Megatrends Inc.",
            "bios_version": "3404",
            "bios_date": "12/28/2023",
        },
    },
    "acer_budget": {
        "lscpu": """Architecture:                         x86_64
CPU op-mode(s):                       32-bit, 64-bit
Byte Order:                           Little Endian
CPU(s):                               8
On-line CPU(s) list:                  0-7
Vendor ID:                            AuthenticAMD
Model name:                           AMD Ryzen 3 5300U with Radeon Graphics
CPU family:                           23
Model:                                104
Thread(s) per core:                   2
Core(s) per socket:                   4
Socket(s):                            1
CPU max MHz:                          3800.0000
CPU min MHz:                          1400.0000
Flags:                                fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm constant_tsc rep_good nopl nonstop_tsc cpuid extd_apicid aperfmperf rapl pni pclmulqdq monitor ssse3 fma cx16 sse4_1 sse4_2 movbe popcnt aes xsave avx f16c rdrand lahf_lm cmp_legacy svm extapic cr8_legacy abm sse4a misalignsse 3dnowprefetch osvw ibs skinit wdt tce topoext perfctr_core perfctr_nb bpext perfctr_llc mwaitx cpb cat_l3 cdp_l3 hw_pstate ssbd mba ibrs ibpb stibp vmmcall fsgsbase bmi1 avx2 smep bmi2 erms invpcid cqm rdt_a rdseed adx smap clflushopt clwb sha_ni xsaveopt xsavec xgetbv1 xsaves
L1d cache:                            128 KiB (4 instances)
L1i cache:                            128 KiB (4 instances)
L2 cache:                             2 MiB (4 instances)
L3 cache:                             4 MiB (1 instance)
""",
        "free": """               total        used        free      shared  buff/cache   available
Mem:      7678545920  3215892000  2145892000   312589000  2316761920  4150064920
Swap:     4294967296           0  4294967296
""",
        "/proc/meminfo": """MemTotal:        7498580 kB
MemFree:         2095596 kB
MemAvailable:    4052800 kB
Buffers:          215680 kB
Cached:          2101081 kB
SwapTotal:       4194304 kB
SwapFree:        4194304 kB
""",
        "lsblk": """{
   "blockdevices": [
      {
         "name": "sda",
         "size": "238.5G",
         "type": "disk",
         "mountpoint": null,
         "model": "KINGSTON SA400S37240G",
         "rota": false,
         "tran": "sata",
         "fstype": null,
         "children": [
            {
               "name": "sda1",
               "size": "512M",
               "type": "part",
               "mountpoint": "/boot/efi",
               "model": null,
               "rota": false,
               "tran": null,
               "fstype": "vfat"
            },
            {
               "name": "sda2",
               "size": "238G",
               "type": "part",
               "mountpoint": "/",
               "model": null,
               "rota": false,
               "tran": null,
               "fstype": "ext4"
            }
         ]
      }
   ]
}
""",
        "lspci": """Slot:	03:00.0
Class:	VGA compatible controller [0300]
Vendor:	Advanced Micro Devices, Inc. [AMD/ATI] [1002]
Device:	Lucienne [Radeon RX Vega 6] [164c]
SVendor:	Acer Incorporated [ALI] [1025]
SDevice:	Aspire A515-45 [1534]
Rev:	c1
""",
        "lspci_driver": """03:00.0 VGA compatible controller: Advanced Micro Devices, Inc. [AMD/ATI] Lucienne (rev c1)
	Subsystem: Acer Incorporated [ALI] Aspire A515-45
	Kernel driver in use: amdgpu
	Kernel modules: amdgpu
""",
        "nvidia_smi": "",
        "dmidecode_memory": """# dmidecode 3.4
Handle 0x0010, DMI type 16, 23 bytes
Physical Memory Array
	Location: System Board Or Motherboard
	Use: System Memory
	Error Correction Type: None
	Maximum Capacity: 16 GB
	Error Information Handle: Not Provided
	Number Of Devices: 1

Handle 0x0011, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x0010
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 8 GB
	Form Factor: SODIMM
	Set: None
	Locator: DIMM 0
	Bank Locator: P0 CHANNEL A
	Type: DDR4
	Type Detail: Synchronous Unbuffered (Unregistered)
	Speed: 3200 MT/s
	Manufacturer: Kingston
	Part Number: ACR32D4S2S1ME-8
	Configured Memory Speed: 3200 MT/s
""",
        "dmidecode_baseboard": """# dmidecode 3.4
Handle 0x0002, DMI type 2, 17 bytes
Base Board Information
	Manufacturer: Acer
	Product Name: Stego_LC
	Version: V1.12
	Serial Number: NBAG811001234567

Handle 0x0000, DMI type 0, 26 bytes
BIOS Information
	Vendor: Insyde Corp.
	Version: V1.12
	Release Date: 08/11/2022
""",
        "/sys/class/dmi/id": {
            "sys_vendor": "Acer",
            "product_name": "Aspire A515-45",
            "product_version": "V1.12",
            "board_vendor": "Acer",
            "board_name": "Stego_LC",
            "bios_vendor": "Insyde Corp.",
            "bios_version": "V1.12",
            "bios_date": "08/11/2022",
        },
    },
}

