# Device Tree Guide for MT6769H Devices

## Overview

The Device Tree (DT) is a data structure that describes hardware components to the Linux kernel. On MediaTek MT6769H devices, the device tree is essential for proper hardware initialization and driver binding.

## Device Tree Structure

### Components

1. **DTB (Device Tree Blob)** - Compiled device tree, stored in boot.img
2. **DTBO (Device Tree Overlay)** - Additional overlays, stored in dtbo.img
3. **DTS (Device Tree Source)** - Human-readable source format

## Device Tree Location

### In Boot Image
```
boot.img structure:
├── kernel
├── ramdisk
├── dtb (appended or separate)
└── header
```

### In DTBO Image
```
dtbo.img structure:
├── DTBO header
├── DT entry[0] (overlay for config 0)
├── DT entry[1] (overlay for config 1)
└── DT entry[N]
```

## Extraction Methods

### Method 1: Using unpack_bootimg (Recommended)

```bash
# Extract boot.img
unpack_bootimg --boot_img boot.img --out dtb_extracted/

# Output files:
# - kernel
# - ramdisk
# - dtb (if present)
```

### Method 2: Manual Extraction

```bash
# Find DTB magic (0xD00DFEED) in boot.img
hexdump -C boot.img | grep "d0 0d fe ed"

# Extract from offset
dd if=boot.img of=extracted.dtb bs=1 skip=<offset> count=<size>
```

### Method 3: Using extract_dtb Tool

```bash
# Install extract_dtb
pip3 install extract_dtb

# Extract all DTBs
extract_dtb boot.img -o dtb_output/
```

## DTBO Extraction

### Using mkdtboimg

```bash
# Dump DTBO information
mkdtboimg dump dtbo.img

# Extract individual overlays
mkdtboimg dump dtbo.img -b dtbo_output/overlay
```

### Manual DTBO Extraction

```bash
# Check DTBO header
hexdump -C dtbo.img -n 256

# DTBO magic: 0xD7B7AB1E
```

## Decompilation

### DTB to DTS

```bash
# Decompile DTB to DTS
dtc -I dtb -O dts -o device.dts device.dtb

# With additional options for better formatting
dtc -I dtb -O dts -o device.dts device.dtb --sort -s
```

### Handling Decompile Errors

```bash
# Force decompilation (may have warnings)
dtc -I dtb -O dts -f -o device.dts device.dtb

# Specific MT6769H decompile
dtc -I dtb -O dts -o device.dts device.dtb -W no-unit_address_vs_reg
```

## Device Tree Structure for MT6769H

### Typical DTS Layout

```dts
/dts-v1/;

/ {
    model = "Infinix NOTE 11";
    compatible = "infinix,note11", "mediatek,mt6769";
    
    #address-cells = <2>;
    #size-cells = <2>;
    
    interrupt-parent = <&gic>;
    
    aliases {
        serial0 = &uart0;
        i2c0 = &i2c0;
        // ...
    };
    
    memory@40000000 {
        device_type = "memory";
        reg = <0 0x40000000 0 0x80000000>; // 2GB example
    };
    
    reserved-memory {
        #address-cells = <2>;
        #size-cells = <2>;
        ranges;
        
        consys-reserve-memory {
            compatible = "mediatek,consys-reserve-memory";
            // ...
        };
    };
    
    cpus {
        #address-cells = <1>;
        #size-cells = <0>;
        
        cpu0: cpu@0 {
            device_type = "cpu";
            compatible = "arm,cortex-a55";
            reg = <0x000>;
            enable-method = "psci";
            // ...
        };
        
        // cpu1-cpu7 ...
    };
    
    soc {
        #address-cells = <2>;
        #size-cells = <2>;
        compatible = "simple-bus";
        ranges;
        
        gic: interrupt-controller@0c000000 {
            compatible = "arm,gic-v3";
            #interrupt-cells = <3>;
            interrupt-controller;
            reg = <0 0x0c000000 0 0x40000>;
        };
        
        uart0: serial@11002000 {
            compatible = "mediatek,mt6765-uart";
            reg = <0 0x11002000 0 0x1000>;
            interrupts = <GIC_SPI 91 IRQ_TYPE_LEVEL_LOW>;
            clocks = <&infracfg CLK_INFRA_UART0>;
            clock-names = "baud";
            status = "okay";
        };
        
        i2c0: i2c@11007000 {
            compatible = "mediatek,mt6765-i2c";
            reg = <0 0x11007000 0 0x1000>;
            interrupts = <GIC_SPI 80 IRQ_TYPE_LEVEL_LOW>;
            clocks = <&infracfg CLK_INFRA_I2C0>;
            clock-names = "main";
            #address-cells = <1>;
            #size-cells = <0>;
            
            // I2C devices
            touchscreen@38 {
                compatible = "focaltech,ft5x46";
                reg = <0x38>;
                interrupt-parent = <&pio>;
                interrupts = <10 IRQ_TYPE_EDGE_FALLING>;
            };
        };
        
        // More SoC devices...
    };
};
```

## Key Device Tree Nodes for MT6769H

### CPU Configuration

```dts
cpus {
    cpu0: cpu@0 {
        device_type = "cpu";
        compatible = "arm,cortex-a55";
        reg = <0x000>;
        enable-method = "psci";
        cpu-idle-states = <&CPU_SLEEP &CLUSTER_SLEEP>;
        capacity-dmips-mhz = <640>;
        dynamic-power-coefficient = <105>;
    };
    
    // 6x Cortex-A55 @ 2.0 GHz
    // 2x Cortex-A75 @ 2.0 GHz (for Helio G88)
};
```

### Memory Configuration

```dts
memory@40000000 {
    device_type = "memory";
    // Actual size filled by bootloader
    reg = <0 0x40000000 0 0xC0000000>; // 3GB
    // reg = <0 0x40000000 1 0x00000000>; // 4GB
    // reg = <0 0x40000000 1 0x80000000>; // 6GB
    // reg = <0 0x40000000 2 0x00000000>; // 8GB
};
```

### Display Panel

```dts
panel@0 {
    compatible = "infinix,note11-panel";
    reg = <0>;
    reset-gpios = <&pio 45 GPIO_ACTIVE_LOW>;
    power-supply = <&lcd_1v8>;
    backlight = <&backlight>;
    
    port {
        panel_in: endpoint {
            remote-endpoint = <&dsi_out>;
        };
    };
    
    display-timings {
        native-mode = <&timing0>;
        timing0: timing0 {
            clock-frequency = <140000000>;
            hactive = <1080>;
            vactive = <2400>;
            hfront-porch = <20>;
            hback-porch = <20>;
            hsync-len = <2>;
            vfront-porch = <8>;
            vback-porch = <8>;
            vsync-len = <4>;
        };
    };
};
```

### Camera Sensors

```dts
&i2c2 {
    camera_main@10 {
        compatible = "mediatek,camera-main";
        reg = <0x10>;
        pinctrl-names = "default", "suspend";
        pinctrl-0 = <&camera_main_active>;
        pinctrl-1 = <&camera_main_suspend>;
        
        clocks = <&topckgen CLK_TOP_CAMTG_SEL>;
        clock-names = "mclk";
        
        reset-gpios = <&pio 101 GPIO_ACTIVE_LOW>;
        powerdown-gpios = <&pio 102 GPIO_ACTIVE_HIGH>;
        
        vcam-supply = <&camera_vcam_2v8>;
        vio-supply = <&camera_vio_1v8>;
        vaf-supply = <&camera_vaf_2v8>;
    };
    
    camera_sub@20 {
        compatible = "mediatek,camera-sub";
        reg = <0x20>;
        // Front camera configuration
    };
};
```

### Audio Codec

```dts
&sound {
    compatible = "mediatek,mt6765-mt6357-sound";
    mediatek,platform = <&afe>;
    
    mediatek,adsp-platform = <&adsp_pcm>;
    mediatek,audio-codec = <&codec>;
    mediatek,hp-detect-gpios = <&pio 8 0>;
    
    /* Audio routing */
    audio-routing =
        "Headphone", "HPOL",
        "Headphone", "HPOR",
        "Speaker", "LINEOUT",
        "AMIC1", "Mic Bias 1",
        "AMIC2", "Mic Bias 2";
};
```

### Touch Controller

```dts
&i2c0 {
    touchscreen@38 {
        compatible = "focaltech,ft5x46";
        reg = <0x38>;
        
        interrupt-parent = <&pio>;
        interrupts = <10 IRQ_TYPE_EDGE_FALLING>;
        
        pinctrl-names = "default", "suspend";
        pinctrl-0 = <&ts_active>;
        pinctrl-1 = <&ts_suspend>;
        
        reset-gpios = <&pio 174 GPIO_ACTIVE_LOW>;
        vdd-supply = <&touch_vdd>;
        vio-supply = <&touch_vio>;
        
        touchscreen-size-x = <1080>;
        touchscreen-size-y = <2400>;
    };
};
```

### Fingerprint Sensor

```dts
&spi1 {
    fingerprint@0 {
        compatible = "goodix,fingerprint";
        reg = <0>;
        
        spi-max-frequency = <8000000>;
        
        interrupt-parent = <&pio>;
        interrupts = <5 IRQ_TYPE_EDGE_RISING>;
        
        reset-gpios = <&pio 178 GPIO_ACTIVE_LOW>;
        power-gpios = <&pio 179 GPIO_ACTIVE_HIGH>;
        
        pinctrl-names = "default", "suspend";
        pinctrl-0 = <&fingerprint_default>;
        pinctrl-1 = <&fingerprint_suspend>;
    };
};
```

### Battery / Charger

```dts
&charger {
    compatible = "mediatek,charger";
    algorithm_name = "SwitchCharging";
    
    /* Charging current limits */
    ac_charger_current = <2000000>;
    ac_charger_input_current = <2000000>;
    non_std_ac_charger_current = <500000>;
    
    /* Battery temperature protection */
    temp_t4_threshold = <50>;
    temp_t3_threshold = <45>;
    temp_t2_threshold = <10>;
    temp_t1_threshold = <0>;
};

&battery {
    compatible = "simple-battery";
    
    constant-charge-current-max-microamp = <2000000>;
    constant-charge-voltage-max-microvolt = <4400000>;
    precharge-current-microamp = <300000>;
    charge-term-current-microamp = <150000>;
    
    // Capacity will be read from fuel gauge
};
```

## Comparing Device Trees

### Extract Key Differences

```bash
# Decompile both DTBs
dtc -I dtb -O dts -o hot30.dts hot30_dtb.dtb
dtc -I dtb -O dts -o note11.dts note11_dtb.dtb

# Generate diff
diff -u note11.dts hot30.dts > device_tree.diff

# Or use specialized tool
python3 scripts/device_tree_extractor.py \
    --compare hot30.dts note11.dts \
    --diff dt_differences.patch
```

### Important Differences to Check

1. **Memory Size**
   ```dts
   - reg = <0 0x40000000 1 0x80000000>; // Note 11: 6GB
   + reg = <0 0x40000000 2 0x00000000>; // Hot 30: 8GB
   ```

2. **Display Panel**
   ```dts
   - compatible = "infinix,note11-panel";
   + compatible = "infinix,hot30-panel";
   ```

3. **Camera Sensors**
   ```dts
   - camera_main@10 { /* Note 11: 50MP sensor */
   + camera_main@10 { /* Hot 30: 64MP sensor */
   ```

4. **Touch Controller**
   ```dts
   - touchscreen@38 { /* Focaltech FT5x46 */
   + touchscreen@5d { /* Ilitek ILI9882N */
   ```

## Modifying Device Tree

### For ROM Porting

**DO NOT modify these (use target device DT):**
- Memory configuration
- Camera sensor definitions
- Touch controller configuration
- Fingerprint sensor
- Display panel timings
- Audio routing

**Can modify (adapt from source):**
- CPU frequency tables (if compatible)
- GPU configuration (same SoC)
- Some power management settings

### Best Practice

**Use target device (Note 11) DTB/DTBO as-is** when porting. The device tree is hardware-specific and should not be mixed between devices.

```bash
# In porting process, use Note 11's boot.img DTB
cp target/boot/boot.img output/flashable/boot.img
# Or extract and repack with Note 11 DTB
```

## Overlays (DTBO)

### Purpose of DTBO

Device tree overlays allow runtime modification without recompiling DTB:

- Different display panels (for same device variants)
- Board revisions
- Optional peripherals

### Viewing DTBO Contents

```bash
# Dump DTBO information
mkdtboimg dump dtbo.img

# Sample output:
# dt_table_header:
#   magic = d7b7ab1e
#   total_size = 524288
#   header_size = 32
#   dt_entry_size = 32
#   dt_entry_count = 4
```

### Extracting Individual Overlays

```bash
# Extract all overlays
mkdtboimg dump dtbo.img -b overlay_

# Decompile each
for i in overlay_*.dtbo; do
    dtc -I dtb -O dts -o ${i%.dtbo}.dts $i
done
```

## Recompiling Device Tree

### DTS to DTB

```bash
# Compile DTS to DTB
dtc -I dts -O dtb -o device_new.dtb device.dts

# With specific options
dtc -I dts -O dtb -o device_new.dtb device.dts \
    -@ \  # Generate symbols
    -W no-unit_address_vs_reg
```

### Creating DTBO

```bash
# Create DTBO from overlay DTS
dtc -I dts -O dtb -o overlay.dtbo overlay.dts -@

# Package into dtbo.img
mkdtboimg create dtbo_new.img overlay0.dtbo overlay1.dtbo overlay2.dtbo
```

### Repacking Boot Image with New DTB

```bash
# Method 1: Using mkbootimg
mkbootimg \
    --kernel kernel \
    --ramdisk ramdisk \
    --dtb device_new.dtb \
    --header_version 2 \
    --os_version 13 \
    --os_patch_level 2024-11 \
    --output boot_new.img

# Method 2: Using AIK (Android Image Kitchen)
./repackimg.sh
```

## Device Tree Properties Reference

### Common Properties

```dts
compatible = "vendor,device";    // Device identifier
reg = <address size>;            // Register address/size
interrupts = <type num flags>;   // Interrupt configuration
clocks = <&provider ID>;         // Clock source
status = "okay" | "disabled";    // Enable/disable node
pinctrl-0 = <&pin_config>;      // Pin configuration
```

### GPIO Properties

```dts
reset-gpios = <&pio 45 GPIO_ACTIVE_LOW>;
// &pio: GPIO controller
// 45: Pin number
// GPIO_ACTIVE_LOW: Active low polarity
```

### Power Supply Properties

```dts
vdd-supply = <&regulator>;       // Power rail
regulator-min-microvolt = <1800000>;
regulator-max-microvolt = <1800000>;
```

## Debugging Device Tree Issues

### Boot Failure Due to DT

```bash
# Check kernel log for DT errors
adb shell dmesg | grep -i "device tree"
adb shell dmesg | grep -i "of:"

# Common errors:
# - "Failed to find device-tree" → Missing or corrupt DTB
# - "OF: ERROR: Bad of_node_put()" → Node reference issue
```

### Verify DTB in Boot Image

```bash
# Extract boot.img
unpack_bootimg --boot_img boot.img --out check/

# Check if DTB exists
file check/dtb
# Should show: Device Tree Blob version 17

# Verify magic
hexdump -C check/dtb -n 4
# Should show: d0 0d fe ed
```

### Check Hardware Detection

```bash
# See what devices kernel detected from DT
adb shell cat /sys/firmware/devicetree/base/model
adb shell cat /proc/device-tree/model

# List DT nodes
adb shell "ls -la /proc/device-tree/"
```

## Best Practices for ROM Porting

### 1. Always Use Target Device DT

```bash
# Extract Note 11 boot.img DTB
unpack_bootimg --boot_img note11_boot.img --out note11_dt/

# Use Note 11 DTB with ported kernel
mkbootimg \
    --kernel hot30_kernel \
    --ramdisk hot30_ramdisk \
    --dtb note11_dt/dtb \
    --output boot_ported.img
```

### 2. Compare for Understanding Only

```bash
# Compare to understand hardware differences
# But do NOT merge device trees
diff -u note11.dts hot30.dts > understanding.diff
```

### 3. Keep DTBO from Target

```bash
# Use Note 11 dtbo.img as-is
cp note11_dtbo.img output/flashable/dtbo.img
```

### 4. Test Boot with Target DT First

```bash
# Test boot with completely target (Note 11) boot.img first
fastboot boot note11_boot.img

# Then gradually introduce source components
```

## References

- [Device Tree Specification](https://www.devicetree.org/)
- [Linux Kernel Device Tree Documentation](https://www.kernel.org/doc/Documentation/devicetree/)
- [Android Boot Image Header](https://source.android.com/devices/bootloader/boot-image-header)
- [MediaTek Device Tree Documentation](https://www.mediatek.com/)
