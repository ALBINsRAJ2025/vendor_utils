# Vendor Blob Reference for MT6769H Devices

## Overview

This document categorizes vendor blobs (binaries and libraries) for MediaTek MT6769H (Helio G88) devices, identifying which are:
- **Device-specific** - Must be preserved from target device
- **SoC-specific** - Can be shared between devices with same chipset
- **Generic** - Standard MediaTek implementations

## Critical Device-Specific Blobs

These **MUST** be preserved from the target device (Infinix Note 11) during ROM porting:

### Audio HALs

**Device-Specific (PRESERVE):**
```
vendor/lib64/hw/audio.primary.mt6769.so
vendor/lib64/libaudiocustparam.so
vendor/lib64/libaudiocustparam_vendor.so
vendor/etc/audio_policy_configuration.xml
vendor/etc/audio_policy_volumes.xml
vendor/etc/audio_effects.xml
vendor/etc/mixer_paths.xml
```

**Why device-specific:**
- Audio routing configuration varies by device PCB layout
- Speaker/mic calibration data
- Headphone jack detection configuration
- Device-specific amplifier control

**SoC-Specific (SHAREABLE):**
```
vendor/lib64/libaudiotoolkit.so
vendor/lib64/libaudiocomponentengine.so
vendor/lib64/libalsautils.so
vendor/lib/soundfx/*.so
```

### Camera HALs

**Device-Specific (PRESERVE):**
```
vendor/lib64/libcam.*.so (some variants)
vendor/lib64/libmtkcam_*.so (device calibration)
vendor/lib64/lib3a.*.so (auto-exposure/focus calibration)
vendor/lib64/hw/camera.provider@2.6-impl-mediatek.so
vendor/etc/camera/*.xml
vendor/etc/camera/calibration/*.bin
```

**Why device-specific:**
- Camera sensor models differ (Hot 30 vs Note 11 have different cameras)
- Lens calibration data
- ISP tuning parameters
- Sensor-specific 3A algorithms

**SoC-Specific (SHAREABLE):**
```
vendor/lib64/libcam_utils.so
vendor/lib64/libcam_platform.so
vendor/lib64/libmtkcam_stdutils.so
vendor/lib64/libcamalgo.*.so (generic algorithms)
```

### Display & Graphics

**Device-Specific (PRESERVE):**
```
vendor/lib64/hw/hwcomposer.mt6769.so
vendor/lib64/hw/gralloc.mt6769.so
vendor/lib64/libged.so
vendor/etc/display_id_*.xml
```

**Why device-specific:**
- Display panel initialization sequences
- Touch controller integration
- Display resolution and timing
- Panel-specific calibration

**SoC-Specific (SHAREABLE):**
```
vendor/lib64/libGLES_mali.so
vendor/lib64/egl/libGLES_mali.so
vendor/lib64/hw/vulkan.mt6769.so
vendor/lib64/libgpu_*.so
```

### Radio / Modem

**Device-Specific (PRESERVE):**
```
vendor/lib64/libmtk-ril.so
vendor/lib64/libratconfig.so
vendor/lib64/libmdfx.so
vendor/etc/md_params/*.bin
vendor/firmware/modem_*.img
```

**Why device-specific:**
- Antenna configuration
- RF calibration data
- IMEI/EFS partition access
- Carrier-specific configurations

**SoC-Specific (SHAREABLE):**
```
vendor/lib64/libc2kutils.so
vendor/lib64/libcarrierconfig.so
vendor/bin/rild (may be shareable)
```

### Sensors

**Device-Specific (PRESERVE):**
```
vendor/lib64/hw/sensors.mt6769.so
vendor/lib64/libhwm.so
vendor/etc/sensor/*.conf
```

**Why device-specific:**
- Different sensor models
- Sensor placement/orientation
- Calibration data
- Fusion algorithm parameters

### GPS

**Device-Specific (PRESERVE):**
```
vendor/bin/mtk_agpsd
vendor/lib64/hw/gps.mt6769.so
vendor/etc/gps/*.conf
```

**Why device-specific:**
- Antenna configuration
- GNSS chipset variants

**SoC-Specific (SHAREABLE):**
```
vendor/lib64/libmnl.so
vendor/lib64/liblbs_*.so
```

### Fingerprint

**Device-Specific (PRESERVE):**
```
vendor/lib64/hw/fingerprint.*.so
vendor/lib64/libgf_*.so (Goodix)
vendor/lib64/libfp_*.so (FPC)
vendor/lib64/libegis_*.so (Egistec)
vendor/firmware/fpc_*.bin
```

**Why device-specific:**
- Different fingerprint sensor models
- Sensor-specific firmware
- Calibration data

### WiFi & Bluetooth

**Device-Specific (PRESERVE):**
```
vendor/etc/wifi/wpa_supplicant.conf
vendor/etc/bluetooth/bt_stack.conf
vendor/firmware/WIFI_RAM_CODE_*.bin
vendor/firmware/BT_RAM_CODE_*.bin
```

**Why device-specific:**
- MAC address storage
- Antenna configuration
- Regional regulatory settings

**SoC-Specific (SHAREABLE):**
```
vendor/lib64/libwifi-hal.so
vendor/lib64/libwpa_client.so
vendor/bin/wpa_supplicant
vendor/bin/hostapd
```

### Thermal Management

**Device-Specific (PRESERVE):**
```
vendor/lib64/hw/thermal.mt6769.so
vendor/etc/thermal*.conf
vendor/etc/.tp/*.conf
```

**Why device-specific:**
- Different cooling solutions
- Thermal sensor placement
- Throttling thresholds

### Power Management

**Device-Specific (PRESERVE):**
```
vendor/lib64/hw/power.mt6769.so
vendor/lib64/libpowerhal.so
vendor/etc/powercontable.xml
vendor/etc/powerscntbl.xml
```

**Why device-specific:**
- Battery capacity differences
- Charging controller
- Power consumption profiles

## SoC-Specific Blobs (Shareable)

These can typically be shared between MT6769H devices:

### Core Platform Libraries
```
vendor/lib64/libmtk_drvb.so
vendor/lib64/libmtkperf_client.so
vendor/lib64/libmtkcutils.so
vendor/lib64/libmtkrilutils.so
vendor/lib64/libmtksysutils.so
vendor/lib64/libion_mtk.so
vendor/lib64/libion.so
```

### GPU Drivers
```
vendor/lib64/libGLES_mali.so
vendor/lib64/egl/libGLES_mali.so
vendor/lib64/libOpenCL.so
vendor/lib64/hw/vulkan.mt6769.so
vendor/lib64/libgpu_*.so
vendor/lib64/libged.so
vendor/lib64/libgpud.so
```

### Media Codecs
```
vendor/lib64/libstagefright_*.so
vendor/lib64/libomx_*.so
vendor/lib64/libvcodec_*.so
vendor/lib64/libvc1dec_sa.ca7.so
vendor/lib64/libh264enc_sa.ca7.so
vendor/lib64/libh265dec_sa.ca7.so
vendor/lib64/libvp9dec_sa.ca7.so
```

### DRM Libraries
```
vendor/lib64/libdrmmtkutil.so
vendor/lib64/libdrmwvmplugin.so
vendor/lib64/libwvhidl.so
vendor/lib64/liboemcrypto.so
vendor/lib64/mediadrmserver
```

### Neural Network / AI
```
vendor/lib64/libneuropilot_*.so
vendor/lib64/libapusys.so
vendor/lib64/libapu_*.so
```

## Categorization by Function

### Category: Audio

| File | Device-Specific | SoC-Specific | Notes |
|------|----------------|--------------|-------|
| audio.primary.mt6769.so | ✓ | | Device audio routing |
| libaudiocustparam.so | ✓ | | Calibration data |
| libaudiotoolkit.so | | ✓ | Generic toolkit |
| libtinyalsa.so | | ✓ | ALSA library |
| audio_effects.xml | ✓ | | Device-specific config |

### Category: Camera

| File | Device-Specific | SoC-Specific | Notes |
|------|----------------|--------------|-------|
| camera.provider@*.so | ✓ | | Sensor HAL |
| libmtkcam_3ahal.so | ✓ | | 3A calibration |
| libcam_utils.so | | ✓ | Generic utilities |
| libcamalgo.*.so | | ✓ | Generic algorithms |

### Category: Display

| File | Device-Specific | SoC-Specific | Notes |
|------|----------------|--------------|-------|
| hwcomposer.mt6769.so | ✓ | | Panel-specific |
| gralloc.mt6769.so | ✓ | | Display config |
| libGLES_mali.so | | ✓ | GPU driver |
| vulkan.mt6769.so | | ✓ | Vulkan driver |

### Category: Radio

| File | Device-Specific | SoC-Specific | Notes |
|------|----------------|--------------|-------|
| libmtk-ril.so | ✓ | | IMEI/RF specific |
| libratconfig.so | ✓ | | Antenna config |
| libc2kutils.so | | ✓ | CDMA utilities |
| rild | Mixed | Mixed | May need testing |

## Firmware Files

### Device-Specific Firmware
```
vendor/firmware/modem_*.img          # Modem firmware (IMEI calibration)
vendor/firmware/fpc_*.bin            # Fingerprint sensor
vendor/firmware/goodix_*.bin         # Fingerprint sensor
vendor/firmware/WIFI_RAM_CODE_*.bin  # WiFi (MAC address)
vendor/firmware/BT_RAM_CODE_*.bin    # Bluetooth (MAC address)
```

### SoC-Specific Firmware
```
vendor/firmware/APU_*.img            # Neural processor
vendor/firmware/gpu_*.bin            # GPU firmware
vendor/firmware/scp.img              # Sensor processor
vendor/firmware/sspm.img             # System power manager
```

## Configuration Files

### Device-Specific Configs
```
vendor/etc/audio_policy_configuration.xml
vendor/etc/mixer_paths.xml
vendor/etc/thermal*.conf
vendor/etc/camera/*.xml
vendor/etc/sensor/*.conf
vendor/etc/gps/*.conf
vendor/etc/md_params/*.bin
```

### SoC-Specific Configs
```
vendor/etc/media_codecs_*.xml
vendor/etc/vintf/manifest.xml (partially)
vendor/etc/permissions/*.xml (most)
```

## Binary Executables

### Device-Specific Binaries
```
vendor/bin/mtk_agpsd       # GPS daemon (antenna config)
vendor/bin/thermald        # Thermal management
```

### SoC-Specific Binaries
```
vendor/bin/hw/*            # Most HAL binaries
vendor/bin/program_binary_service
vendor/bin/vtservice
vendor/bin/mnld
```

## Porting Decision Matrix

### What to Take from Source ROM (Hot 30)
- ✓ system partition (Android 13 framework)
- ✓ system_ext partition
- ✓ product partition (with device overlay adjustments)
- ✓ SoC-specific vendor libs (GPU, media codecs, generic MTK libs)
- ✓ Boot image kernel (test first)

### What to Preserve from Target ROM (Note 11)
- ✓ ALL device-specific vendor HALs
- ✓ Device firmware (modem, WiFi, BT, fingerprint)
- ✓ Device-specific configs (audio, camera, sensors)
- ✓ Calibration data
- ✓ IMEI/EFS partitions (never modify!)

### What to Merge/Adapt
- ⚠ vendor/build.prop (hybrid approach)
- ⚠ system/build.prop (device identity from target)
- ⚠ SELinux policies (merge both)
- ⚠ VINTF manifests (ensure HAL versions match)

## Testing Priority

After porting, test in this order:

1. **Boot success** (kernel, init, system services)
2. **Display** (critical for seeing anything)
3. **Touch** (critical for interaction)
4. **WiFi** (for updates and debugging)
5. **Audio** (calls, media)
6. **Mobile network** (IMEI, calls, data)
7. **Camera** (front, back)
8. **Sensors** (accelerometer, gyro, proximity)
9. **Bluetooth**
10. **GPS**
11. **Fingerprint**
12. **Charging**

## Common Mistakes

### ❌ Don't Do This:
1. Replace Note 11's audio HAL with Hot 30's → No sound or wrong routing
2. Use Hot 30's camera HAL → Camera won't work
3. Replace modem firmware → IMEI loss, no network
4. Copy Hot 30's thermal config → Overheating or aggressive throttling
5. Forget to adapt build.prop → Wrong device identity

### ✓ Do This:
1. Preserve ALL Note 11 HALs in critical categories
2. Test incrementally (one partition at a time if issues arise)
3. Keep backups of original partitions
4. Check logcat for HAL failures
5. Verify SELinux contexts are correct

## Quick Reference Commands

### Extract vendor blobs
```bash
python3 scripts/vendor_blob_extractor.py \
    --vendor target/partitions/vendor_mount \
    --output vendor_blobs \
    --device note11 \
    --extract-critical
```

### Compare vendor partitions
```bash
diff -r source/vendor_mount/ target/vendor_mount/ > vendor_diff.txt
```

### Check for missing libraries
```bash
adb logcat | grep "dlopen failed"
adb logcat | grep "cannot locate symbol"
```

### Verify HAL services
```bash
adb shell "ps -A | grep android.hardware"
adb shell "lshal"
```

## References

- [Android HAL Documentation](https://source.android.com/devices/architecture/hal)
- [MediaTek Platform](https://www.mediatek.com/)
- [Vendor Interface Object (VINTF)](https://source.android.com/devices/architecture/vintf)
