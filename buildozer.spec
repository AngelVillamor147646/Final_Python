[app]
title = Tasklyn
package.name = tasklyn
package.domain = org.tasklyn

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,json,md

version = 1.0.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer,matplotlib,pillow,sqlite3

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE,RECEIVE_BOOT_COMPLETED
android.api = 33
android.minapi = 24
android.sdk = 33
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.wakelock = False

[buildozer]
log_level = 2
warn_on_root = 1
