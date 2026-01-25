# SELinux Policy Mapping for Android 12 → 13 ROM Porting

## Overview

SELinux (Security-Enhanced Linux) policies enforce mandatory access control. When porting from Android 12 to Android 13, policy differences must be carefully handled to ensure services can function while maintaining security.

## SELinux Basics

### Enforcement Modes

- **Enforcing:** Denials are blocked (production mode)
- **Permissive:** Denials are logged but allowed (debugging mode)
- **Disabled:** SELinux is off (not recommended)

```bash
# Check current mode
adb shell getenforce

# Set permissive (temporary, for debugging)
adb shell setenforce 0

# Set enforcing
adb shell setenforce 1
```

## SELinux Policy Structure in Android

### Policy Locations

```
Android 12 (Target - Note 11):
├── /system/etc/selinux/
│   ├── plat_sepolicy.cil          # Platform policy
│   ├── plat_file_contexts
│   ├── plat_property_contexts
│   └── plat_service_contexts
├── /vendor/etc/selinux/
│   ├── vendor_sepolicy.cil        # Vendor policy
│   ├── vendor_file_contexts
│   ├── vendor_property_contexts
│   └── vndservice_contexts
└── /system_ext/etc/selinux/
    └── system_ext_sepolicy.cil

Android 13 (Source - Hot 30):
├── /system/etc/selinux/
│   ├── plat_sepolicy.cil          # Enhanced Android 13 policy
│   ├── plat_file_contexts
│   ├── plat_property_contexts
│   └── plat_service_contexts
├── /vendor/etc/selinux/
│   ├── vendor_sepolicy.cil
│   ├── vendor_file_contexts
│   ├── vendor_property_contexts
│   └── vndservice_contexts
└── /system_ext/etc/selinux/
    └── system_ext_sepolicy.cil
```

## Key Android 13 SELinux Changes

### 1. Stricter App Data Access

**Android 12:**
```
allow app_data_file all_apps rw_file_perms;
```

**Android 13:**
```
neverallow { all_apps -mediaprovider } app_data_file:dir_file_class_set create;
```

**Impact:** Apps have reduced access to other apps' data directories.

### 2. Expanded Treble Requirements

**Android 13 adds:**
- Stricter vendor/system separation
- More neverallow rules
- Enhanced VNDK enforcement

### 3. New Hardware Types

**Android 13 introduces:**
```
type hal_uwb_hwservice, hwservice_manager_type;
type hal_threadnetwork_hwservice, hwservice_manager_type;
```

**Porting Impact:** Old vendor policies may not define these types.

### 4. Property Context Changes

**New property prefixes in Android 13:**
```
vendor.camera.               u:object_r:vendor_camera_prop:s0
persist.vendor.camera.       u:object_r:vendor_camera_prop:s0
vendor.audio.                u:object_r:vendor_audio_prop:s0
```

## Common SELinux Denials in ROM Porting

### Denial 1: Vendor HAL Cannot Access System Libraries

**Denial:**
```
avc: denied { read } for pid=1234 comm="android.hardware.camera" name="libc++.so" 
dev="dm-0" ino=12345 scontext=u:r:hal_camera_default:s0 
tcontext=u:object_r:system_lib_file:s0 tclass=file permissive=0
```

**Meaning:** Camera HAL trying to read system library.

**Solution:**
```te
# In vendor_sepolicy.cil or additional_rules.te
allow hal_camera_default system_lib_file:dir r_dir_perms;
allow hal_camera_default system_lib_file:file r_file_perms;
```

### Denial 2: System Service Cannot Access Vendor Property

**Denial:**
```
avc: denied { set } for property=vendor.audio.volume 
scontext=u:r:system_server:s0 tcontext=u:object_r:vendor_audio_prop:s0 
tclass=property_service permissive=0
```

**Solution:**
```te
# Allow system_server to set vendor audio properties
set_prop(system_server, vendor_audio_prop)
```

### Denial 3: Init Cannot Execute Vendor Binary

**Denial:**
```
avc: denied { execute } for path="/vendor/bin/hw/android.hardware.camera.provider@2.6-service-mediatek" 
dev="dm-4" ino=234 scontext=u:r:init:s0 tcontext=u:object_r:vendor_file:s0 
tclass=file permissive=0
```

**Solution:**
```te
# Mark binary as executable domain
type hal_camera_default_exec, vendor_file_type, exec_type, file_type;

# In vendor_file_contexts:
/vendor/bin/hw/android\.hardware\.camera\.provider@2\.6-service-mediatek u:object_r:hal_camera_default_exec:s0
```

## Merging SELinux Policies

### Strategy for ROM Porting

1. **System partition:** Use Android 13 (source) policies
2. **Vendor partition:** Merge policies, preserving device-specific rules
3. **Add compatibility rules:** Bridge Android 12 vendor with Android 13 system

### File Contexts Merging

#### Source (Hot 30 - Android 13)
```
# /system/etc/selinux/plat_file_contexts
/system/bin/app_process32    u:object_r:zygote_exec:s0
/system/bin/app_process64    u:object_r:zygote_exec:s0
/system/framework(/.*)?      u:object_r:system_file:s0
```

#### Target (Note 11 - Android 12)
```
# /vendor/etc/selinux/vendor_file_contexts
/vendor/bin/hw/android\.hardware\.camera\.provider@2\.6-service-mediatek u:object_r:hal_camera_default_exec:s0
/vendor/lib64/hw/audio\.primary\.mt6769\.so u:object_r:vendor_hal_file:s0
/vendor/lib64/libmtk-ril\.so u:object_r:vendor_hal_file:s0
```

#### Merged Approach

```bash
# Use Android 13 system contexts
cp source/system/etc/selinux/plat_file_contexts \
   merged/system/etc/selinux/plat_file_contexts

# Use Note 11 vendor contexts (device-specific)
cp target/vendor/etc/selinux/vendor_file_contexts \
   merged/vendor/etc/selinux/vendor_file_contexts

# Add compatibility contexts if needed
cat >> merged/vendor/etc/selinux/vendor_file_contexts << EOF
# Compatibility rules for Android 13 system
/vendor/lib64/vndk-sp-29(/.*)?  u:object_r:vendor_file:s0
EOF
```

### Property Contexts Merging

#### Source (Android 13)
```
# plat_property_contexts
ro.build.                    u:object_r:build_prop:s0
persist.sys.                 u:object_r:system_prop:s0
```

#### Target (Android 12 Vendor)
```
# vendor_property_contexts
vendor.camera.               u:object_r:vendor_camera_prop:s0
persist.vendor.camera.       u:object_r:vendor_camera_prop:s0
vendor.audio.                u:object_r:vendor_audio_prop:s0
ro.vendor.mtk.               u:object_r:vendor_mtk_prop:s0
```

#### Merged
```bash
# System property contexts from Android 13
cp source/system/etc/selinux/plat_property_contexts \
   merged/system/etc/selinux/plat_property_contexts

# Vendor property contexts from Note 11
cp target/vendor/etc/selinux/vendor_property_contexts \
   merged/vendor/etc/selinux/vendor_property_contexts
```

### Service Contexts Merging

```bash
# Use Android 13 system service contexts
cp source/system/etc/selinux/plat_service_contexts \
   merged/system/etc/selinux/plat_service_contexts

# Use Note 11 vendor service contexts
cp target/vendor/etc/selinux/vndservice_contexts \
   merged/vendor/etc/selinux/vndservice_contexts

# Use Note 11 vendor hwservice contexts
cp target/vendor/etc/selinux/vendor_hwservice_contexts \
   merged/vendor/etc/selinux/vendor_hwservice_contexts
```

## Additional SELinux Rules for Compatibility

### Create additional_rules.te

```te
# Additional SELinux rules for Android 12 vendor → Android 13 system compatibility
# Place in /vendor/etc/selinux/ or compile into vendor_sepolicy.cil

### VENDOR HAL ACCESS TO SYSTEM LIBRARIES ###

# Allow vendor HALs to access system libraries
allow vendor_hal_domain system_lib_file:dir r_dir_perms;
allow vendor_hal_domain system_lib_file:file r_file_perms;

# Allow vendor HALs to access system_ext libraries
allow vendor_hal_domain system_ext_lib_file:dir r_dir_perms;
allow vendor_hal_domain system_ext_lib_file:file r_file_perms;

### PROPERTY ACCESS ###

# Allow system_server to read vendor properties
get_prop(system_server, vendor_default_prop)
get_prop(system_server, vendor_camera_prop)
get_prop(system_server, vendor_audio_prop)

# Allow HALs to set their own properties
set_prop(hal_camera_default, vendor_camera_prop)
set_prop(hal_audio_default, vendor_audio_prop)

### CAMERA HAL ###

# Camera HAL needs access to camera data
allow hal_camera_default vendor_camera_data_file:dir rw_dir_perms;
allow hal_camera_default vendor_camera_data_file:file create_file_perms;

# Camera server access
allow cameraserver vendor_camera_prop:file r_file_perms;

### AUDIO HAL ###

# Audio HAL access to audio data
allow hal_audio_default vendor_audio_data_file:dir rw_dir_perms;
allow hal_audio_default vendor_audio_data_file:file create_file_perms;

# AudioServer access
allow audioserver vendor_audio_prop:file r_file_perms;

### RADIO/RIL ###

# Radio daemon property access
allow radio vendor_radio_prop:property_service set;
allow rild vendor_radio_data_file:dir rw_dir_perms;
allow rild vendor_radio_data_file:file create_file_perms;

# Allow radio to access modem device
allow radio vendor_modem_device:chr_file rw_file_perms;

### SENSORS ###

# Sensors HAL access
allow hal_sensors_default vendor_sensors_data_file:dir rw_dir_perms;
allow hal_sensors_default vendor_sensors_data_file:file create_file_perms;

### GPU/DISPLAY ###

# SurfaceFlinger needs vendor GPU libs
allow surfaceflinger vendor_hal_file:file r_file_perms;
allow surfaceflinger vendor_hal_file:dir r_dir_perms;

### MEDIATEK SPECIFIC ###

# MTK specific services
allow mtk_hal_default vendor_mtk_data_file:dir rw_dir_perms;
allow mtk_hal_default vendor_mtk_data_file:file create_file_perms;

### DEBUGGING (REMOVE IN PRODUCTION) ###

# Uncomment for debugging - allows more permissive access
# userdebug_or_eng(`
#   allow domain domain:process ptrace;
# ')
```

### Compile Additional Rules (if using .te format)

```bash
# Convert .te to CIL format
checkpolicy -M -C -c 30 -o additional_rules.policy additional_rules.te
checkmodule -M -m -o additional_rules.mod additional_rules.te
semodule_package -o additional_rules.pp -m additional_rules.mod

# Or include in vendor policy build
# (requires full Android build environment)
```

### Apply Rules Without Recompilation

```bash
# If rules are in CIL format (.cil)
# Copy to /vendor/etc/selinux/
adb push additional_rules.cil /vendor/etc/selinux/

# Reboot for policies to take effect
adb reboot
```

## Testing SELinux Policies

### 1. Boot in Permissive Mode

```bash
# Set SELinux to permissive
adb shell setenforce 0

# Test all functionality
# - Camera, audio, calls, etc.

# Check for denials
adb shell dmesg | grep avc > denials.log
```

### 2. Analyze Denials

```bash
# Group similar denials
grep "avc: denied" denials.log | \
  sed 's/pid=[0-9]*/pid=XXXX/g' | \
  sed 's/ino=[0-9]*/ino=XXXX/g' | \
  sort | uniq -c | sort -rn > denials_summary.txt

# View top denials
head -20 denials_summary.txt
```

### 3. Generate Rules from Denials

```bash
# Use audit2allow (from full Android build)
adb shell dmesg | grep avc | audit2allow -p policy_file

# Manual rule creation based on denial format
# avc: denied { PERMISSION } for scontext=SOURCE tcontext=TARGET tclass=CLASS
#
# Becomes:
# allow SOURCE TARGET:CLASS PERMISSION;
```

### 4. Test in Enforcing Mode

```bash
# Apply rules and reboot
adb reboot

# Set to enforcing
adb shell setenforce 1

# Test all functionality again
# Any failures = missing rules
```

### 5. Validate No Critical Denials

```bash
# After full testing, check for critical denials
adb logcat -b all | grep "avc: denied"

# Should see minimal or no denials for core functionality
```

## Context Labeling

### File Contexts

```bash
# Check file context
adb shell ls -Z /vendor/lib64/hw/audio.primary.mt6769.so

# Should show:
# u:object_r:vendor_hal_file:s0 /vendor/lib64/hw/audio.primary.mt6769.so

# Relabel if incorrect (requires root)
adb shell chcon u:object_r:vendor_hal_file:s0 /vendor/lib64/hw/audio.primary.mt6769.so
```

### Process Contexts

```bash
# Check running process context
adb shell ps -Z | grep camera

# Should show:
# u:r:hal_camera_default:s0  root  1234  android.hardware.camera@2.6
```

### Property Contexts

```bash
# Check property context
adb shell getprop -Z vendor.camera.preview.size

# Should show:
# [vendor.camera.preview.size]: [u:object_r:vendor_camera_prop:s0] [1920x1080]
```

## Common SELinux Errors and Solutions

### Error 1: HAL Service Won't Start

**Log:**
```
init: Service 'vendor.camera-2-6' (pid 1234) killed by signal 9
init: Service 'vendor.camera-2-6' could not be started
```

**Check:**
```bash
adb logcat | grep camera
adb shell dmesg | grep camera | grep avc
```

**Solution:** Fix file_contexts for service binary and libraries.

### Error 2: Property Access Denied

**Log:**
```
system_server: type=1400 audit: avc: denied { set } for property=vendor.camera.mode
```

**Solution:**
```te
set_prop(system_server, vendor_camera_prop)
```

### Error 3: Binder Communication Denied

**Log:**
```
avc: denied { call } for scontext=u:r:system_app:s0 tcontext=u:r:hal_camera_default:s0 tclass=binder
```

**Solution:**
```te
binder_call(system_app, hal_camera_default)
```

## Policy Development Workflow

```
1. Port ROM with enforcing SELinux
   ↓
2. Boot fails or features don't work
   ↓
3. Switch to permissive mode: setenforce 0
   ↓
4. Test all features, collect denials
   ↓
5. Analyze denials, group by category
   ↓
6. Write policy rules for each category
   ↓
7. Apply rules, rebuild vendor partition
   ↓
8. Flash and reboot in enforcing mode
   ↓
9. Test again
   ↓
10. If issues remain, go to step 3
    If working, done!
```

## Best Practices

### 1. Minimize Custom Rules

- Use Android 13 system policies as-is
- Only add vendor compatibility rules
- Don't weaken existing neverallow rules

### 2. Follow Android Security Model

- Maintain vendor/system separation
- Don't allow unrestricted domain access
- Keep permissive rules specific

### 3. Test Thoroughly

- Test all hardware features
- Check for denials in all scenarios
- Verify in enforcing mode before release

### 4. Document Changes

```te
# Document why each rule is needed
# Example:
# Allow camera HAL to access calibration data from Note 11
# This is device-specific and required for proper camera function
allow hal_camera_default vendor_camera_data_file:file r_file_perms;
```

## References

- [SELinux for Android](https://source.android.com/security/selinux)
- [Writing SELinux Policy](https://source.android.com/security/selinux/device-policy)
- [SELinux Concepts](https://source.android.com/security/selinux/concepts)
- [Validating SELinux](https://source.android.com/security/selinux/validate)
