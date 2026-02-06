[app]

# (str) Title of your application
title = Neon Tetris Ultra

# (str) Package name
package.name = neontetrisultra

# (str) Package domain (needed for android packaging)
package.domain = org.antigravity

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,wav,mp3,ttf

# (str) Application version
version = 1.0

# (list) Application requirements
requirements = python3==3.10.12,pygame

# (str) Custom source folders for requirements
# packagelist.pygame = pygame

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientations (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) Permissions
android.permissions = INTERNET, WAKE_LOCK

# (int) Android API to use
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android entry point, default is to use start.py
android.entrypoint = main.py

# (str) Full name including package path of the Java class that implements Android Activity
# android.activity_class = org.kivy.android.PythonActivity

# (list) Pattern to exclude for the search
#android.exclude_patterns = bin, *.pyc, *.wmv

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jar files that you do not need, since each jar
# file can slow down the build process. (list of clob patterns)
#android.add_jars = foo.jar,bar.jar,path/to/extra/*.jar

# (list) List of Java files to add to the android project (can be java or a directory containing the files)
#android.add_src =

# (list) Android AAR archives to add (list of clob patterns)
#android.add_aars =

# (list) Gradle dependencies
#android.gradle_dependencies =

# (list) add java compile options
# android.add_compile_options = "sourceCompatibility = 1.8", "targetCompatibility = 1.8"

# (list) Android materials themes (best for newer android versions)
android.meta_data = android.max_aspect=2.1

# (list) Android additionnal libraries to copy into libs/armeabi
#android.add_libs_armeabi = libs/android-v7/libgnustl_shared.so

# (str) python-for-android branch to use, default is master
p4a.branch = master

# (str) OUUTPUT format (apk or aab)
android.release_artifact = apk

# (str) Log level (2 = error only, 1 = info, 0 = debug)
log_level = 2

# (int) display cutouts (notch)
android.notch_support = True

[buildozer]

# (int) log level (2 = error only, 1 = info, 0 = debug)
log_level = 2

# (int) display warning if buildozer is run as root (0 = off, 1 = on)
warn_on_root = 1
