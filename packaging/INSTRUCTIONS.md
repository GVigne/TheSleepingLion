This short document is a memo to create an installer for The Sleeping Lion on Windows. There are no prerequisites other than having a computer running on Windows 10 or Windows 11.

## Step 0: install MSYS2
Download and install MSYS2: https://www.msys2.org/. From here on, we will be working with MINGW64.

## Step 1: install system-wide dependencies
Run the following commands to upgrade the MSYS packages and install all necessary dependencies.
- `pacman -Suy`
- `pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-python3 mingw-w64-x86_64-python3-gobject mingw-w64-x86_64-nsis mingw-w64-x86_64-nsis-nsisunz zip unzip mingw-w64-x86_64-python-numpy mingw-w64-x86_64-python-cffi mingw-w64-x86_64-python-pillow mingw-w64-x86_64-python-manimpango mingw-w64-x86_64-python-yaml mingw-w64-x86_64-python-regex`

## Step 2: downgrade pango to version 1.50.11
Pango's recent versions seem to be bugged with Windows: namely, using fonts added at runtime using the Windows API doesn't seem to work. The latest working version is `1.50.11`, which we will be using.
- Download the appropriate pango version: `https://repo.msys2.org/mingw/x86_64/mingw-w64-x86_64-pango-1.50.11-1-any.pkg.tar.zst`
- Navigate to the folder containing the downloaded archive and downgrade pango: `pacman -U mingw-w64-x86_64-pango-1.50.11-1-any.pkg.tar.zst`

## Step 3: create a Python venv and install The Sleeping Lion
Create a Python venv using system-wide packages, then activate it:
- `python3 -m venv path_to_venv --system-site-packages`
- `source path_to_venv/bin/activate`
- Download or clone The Sleeping Lion.
- `pip install cairocffi==1.0.0`. cairocffi's latest versions don't seem to compile using MSYS, so we have to use an older version.
- `pip install pyinstaller`
- `pip install .`. Install The Sleeping Lion.

## Step 4: package The Sleeping Lion using Nsis
Nsis is a tool which helps distribute apps through Windows. We will also be using ResourceHacker to set an icon on the resulting executable (this icon will be shown in the task bar to the user).
- Download an install ResourceHacker from http://www.angusj.com/resourcehacker/. Then, move the `ResourceHacker.exe` file to the `packaging` folder.
- Navigate to the `packaging` folder, and run `./build.sh`. This will launch the `build.sh` script which will take care of the creation of the executable.

The `build.sh` script starts by using PyInstaller to create an executable, then calls Nsis and Resource hacker to have a nice Setup Wizard and making sure The Sleeping Lion can be uninstalled in a "clean Windows way" (via "Add or Remove programs").

 Note that the icon located in `packaging` and named `the_sleeping_lion_square.ico` is different from the ones in `gui_images`: Windows can't deal with rectangular icons, so we have to use a dedicated square icon.

The `build.sh` script will create folders named `dist` and `build`, as well as other files in the `packaging` folder. You can ignore them: the interesting file should be named something like `the_sleeping_lion-1.0.0-x86_64.exe` and corresponds to The Sleeping Lion's Windows installer.