### Java 17 Setup for PySpark (```msfootprint```)

PySpark requires **Java 17 or newer** to launch the JVM. If your system doesnot have this version, it might fail.
**Failure to install Java 17 results in:** `JAVA_GATEWAY_EXITED` or `UnsupportedClassVersionError`.

#### 1. Quick Verification
Run this in your terminal to see if you are already set up:

```bash
java -version
# Success: Output includes openjdk version "17.0.x" (or higher).

#Failure: Output is command not found or version is 1.8, 11, etc. -> Proceed to Installation.
```

#### 2. Installation
**(i) macOS (Apple Silicon & Intel)**
```bash
#Install via Homebrew:
brew install openjdk@17

#Link JDK to System (required): Apple Silicon:

sudo ln -sfn /opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-17.jdk

#Intel Mac:

sudo ln -sfn /usr/local/opt/openjdk@17/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-17.jdk

#Configure Shell: Copy and run this block to set JAVA_HOME permanently

echo 'export JAVA_HOME=$(/usr/libexec/java_home -v 17)' >> ~/.zshrc
echo 'export PATH="$JAVA_HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```
**(ii) Windows 10/11**

```bash
#Install JDK:
# Option a. Install via Terminal (Winget) - Recommended
winget install EclipseAdoptium.Temurin.17

# Option b: Manual Download
# Link: https://adoptium.net/temurin/releases/?version=17
# Important: Run installer and select "Set JAVA_HOME" feature.

#Verify/Set Variables:

System Variables: Ensure JAVA_HOME points to your install (e.g., C:\Program Files\Eclipse Adoptium\jdk-17...).

Path: Ensure %JAVA_HOME%\bin is added to your Path.

#Temporary PowerShell Override (If system settings fail):
PowerShell
$env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-17.0.xx.x-hotspot"
$env:Path="$env:JAVA_HOME\bin;$env:Path"