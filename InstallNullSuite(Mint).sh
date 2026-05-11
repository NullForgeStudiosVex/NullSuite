#!/bin/bash

# ==============================
# NullSuite Installer
# ==============================

BASE_DIR="$(dirname "$(realpath "$0")")"
RUNTIME_DIR="$BASE_DIR/Runtime"
ORIGINAL_DIR="$BASE_DIR"

cd "$BASE_DIR" || exit

echo "=== NullSuite Installer ==="

# ==============================
# Environment Warning
# ==============================

if ! grep -qi "mint" /etc/os-release; then
    echo ""
    echo "WARNING:"
    echo "This was built and tested on Linux Mint."
    echo "Other distros may require manual fixes."
    echo ""
fi

# ==============================
# Ensure Git
# ==============================

if ! command -v git >/dev/null 2>&1; then
    echo "Git not found. Installing..."
    sudo apt update
    sudo apt install -y git
fi

# ==============================
# NullGit Setup
# ==============================

echo ""
echo "Do you intend to use NullGit?"
echo "It provides Git/GitHub integration for NullSuite."
echo ""

read -r -p "Proceed? (y/n): " confirm

if [[ "$confirm" =~ ^[Yy]$ ]]; then

    echo ""
    echo "Setting up NullGit..."

    # ------------------------------
    # Ensure Git
    # ------------------------------

    if ! command -v git >/dev/null 2>&1; then

        echo ""
        echo "Git not found. Installing..."

        sudo add-apt-repository ppa:git-core/ppa -y
        sudo apt update

        sudo apt install -y \
            git \
            wget \
            tar \
            gnome-keyring \
            seahorse
    fi

    echo ""
    echo "Git Version:"
    git --version

    # ------------------------------
    # Ensure GitHub CLI
    # ------------------------------

    if ! command -v gh >/dev/null 2>&1; then

        echo ""
        echo "GitHub CLI not found. Installing..."

        sudo apt install -y gh
    fi

    # ------------------------------
    # Git Credential Manager
    # ------------------------------

    if [ ! -f "$HOME/.gcmcore/git-credential-manager" ]; then

        echo ""
        echo "Installing Git Credential Manager..."

        wget \
            https://github.com/GitCredentialManager/git-credential-manager/releases/download/v2.4.1/gcm-linux_amd64.2.4.1.tar.gz

        mkdir -p "$HOME/.gcmcore"

        tar -xvf \
            gcm-linux_amd64.2.4.1.tar.gz \
            -C "$HOME/.gcmcore"

        rm gcm-linux_amd64.2.4.1.tar.gz

        echo ""
        echo "Configuring Git Credential Manager..."

        git config --global credential.helper \
            "$HOME/.gcmcore/git-credential-manager"

        git config --global credential.credentialStore secretservice
    fi

    # ------------------------------
    # GitHub Authentication
    # ------------------------------

    echo ""
    echo "Checking GitHub authentication..."

    if gh auth status >/dev/null 2>&1; then

        echo "GitHub already authenticated."

    else

        echo ""
        echo "GitHub login required for:"
        echo "- Repo ownership detection"
        echo "- Push/Pull management"
        echo "- Browser OAuth authentication"
        echo "- NullGit integration"
        echo ""

        gh auth login
    fi

    echo ""
    echo "NullGit setup complete."
    echo ""
    echo "You can now use GitHub features directly inside NullGit."

else

    echo "Skipping NullGit setup."

fi

# ==============================
# Ensure Zenity
# ==============================

if ! command -v zenity >/dev/null 2>&1; then
    echo "Zenity not found. Installing..."
    sudo apt install -y zenity >/dev/null 2>&1

    if ! command -v zenity >/dev/null 2>&1; then
        echo "Failed to install zenity."
    fi
fi

# ==============================
# Optional Git Setup
# ==============================

if [ ! -d "$BASE_DIR/.git" ]; then
    echo ""
    echo "This install is not linked to git."
    echo "Enable auto-updates by cloning the repository?"

    read -r -p "(y/n): " confirm

    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo ""

        DEFAULT_REPO="$HOME/.local/share/NullSuiteRepo"

        REPO_BASE=$(zenity --file-selection \
            --directory \
            --title="Select location for NullSuite repository" \
            --filename="$DEFAULT_REPO/")

        if [ -z "$REPO_BASE" ]; then
            echo "Cancelled. Skipping git setup."

        else
            REPO_DIR="$REPO_BASE/NullSuite"

            echo "Setting up repository at:"
            echo "$REPO_DIR"

            if [ -d "$REPO_DIR" ]; then
                zenity --question \
                    --text="NullSuite folder already exists here. Overwrite?" || exit 1

                rm -rf "$REPO_DIR"
            fi

            mkdir -p "$REPO_BASE"

            git clone \
                https://github.com/NullForgeStudiosVex/NullSuite.git \
                "$REPO_DIR" || {

                echo "Git clone failed."
                read
                exit 1
            }

            echo ""
            echo "Repository created at:"
            echo "$REPO_DIR"

            echo ""
            echo "Do you want to delete this original ZIP folder?"
            read -r -p "(y/n): " confirm

            if [[ "$confirm" =~ ^[Yy]$ ]]; then

                xdg-open "$REPO_DIR" >/dev/null 2>&1 &

                if [ -z "$ORIGINAL_DIR" ] || \
                   [ "$ORIGINAL_DIR" = "/" ] || \
                   [ "$ORIGINAL_DIR" = "$HOME" ] || \
                   [ "$ORIGINAL_DIR" = "$REPO_DIR" ]; then

                    echo "Refusing to delete unsafe directory:"
                    echo "$ORIGINAL_DIR"

                else
                    echo "Deleting:"
                    echo "$ORIGINAL_DIR"

                    rm -rf "$ORIGINAL_DIR"

                    echo "Deleted."
                fi
            fi

            xdg-open "$REPO_DIR" >/dev/null 2>&1 &

            exit 0
        fi
    else
        echo "Skipping git setup."
    fi
fi

chmod +x "$BASE_DIR/Updater.sh" 2>/dev/null

# ==============================
# Dependency Check
# ==============================

MISSING=()

check_cmd() {
    command -v "$1" >/dev/null 2>&1 || MISSING+=("$1")
}

check_cmd python3
check_cmd jq
check_cmd inotifywait
check_cmd pactl
check_cmd pw-link
check_cmd pw-dump
check_cmd wpctl
check_cmd xdotool
check_cmd xrandr
check_cmd HandBrakeCLI
check_cmd wmctrl

# tkinter
python3 - <<EOF 2>/dev/null || MISSING+=("python3-tk")
import tkinter
EOF

# gi / AppIndicator
python3 - <<EOF 2>/dev/null || MISSING+=("python3-gi" "gir1.2-appindicator3-0.1")
import gi
gi.require_version('AppIndicator3', '0.1')
EOF

# venv
python3 -m venv --help >/dev/null 2>&1 || MISSING+=("python3-venv")

# ==============================
# Install Missing Dependencies
# ==============================

if [ ${#MISSING[@]} -ne 0 ]; then
    echo ""
    echo "Missing dependencies:"
    echo "${MISSING[*]}"
    echo ""

    echo "Calculating install size..."

    SIZE_INFO=$(apt-get -s install \
        python3 python3-venv python3-tk \
        python3-gi gir1.2-appindicator3-0.1 \
        jq inotify-tools \
        pipewire pipewire-audio-client-libraries \
        xdotool x11-xserver-utils \
        wmctrl \
        handbrake-cli 2>/dev/null | grep "After this operation")

    echo "$SIZE_INFO"
    echo ""

    echo "Continue? (y/n)"
    read -r confirm

    [[ "$confirm" != "y" ]] && exit 1

    sudo apt update

    sudo apt install -y \
        python3 python3-venv python3-tk \
        python3-gi gir1.2-appindicator3-0.1 \
        jq inotify-tools \
        pipewire pipewire-audio-client-libraries \
        xdotool x11-xserver-utils \
        wmctrl \
        handbrake-cli
fi

# ==============================
# GNOME Tray Support
# ==============================

DE="$XDG_CURRENT_DESKTOP"

if [[ "$DE" == *"GNOME"* ]]; then
    echo ""
    echo "GNOME detected — tray icons may require extension."

    if grep -qi ubuntu /etc/os-release; then
        echo "Installing GNOME tray extension..."

        sudo apt install -y gnome-shell-extension-appindicator

        echo "Log out and back in if tray doesn't appear."
    fi
fi

# ==============================
# VENV SETUP
# ==============================

cd "$RUNTIME_DIR" || exit

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv --system-site-packages
fi

source venv/bin/activate

echo "Upgrading pip..."
python3 -m pip install --upgrade pip

echo "Installing Python dependencies..."
python3 -m pip install \
    setproctitle \
    mido \
    python-rtmidi \
    python-uinput

deactivate

# ==============================
# VLC Detection
# ==============================

HAS_VLC_NATIVE=0
HAS_VLC_FLATPAK=0

if command -v vlc >/dev/null 2>&1; then
    HAS_VLC_NATIVE=1
fi

if command -v flatpak >/dev/null 2>&1; then
    if flatpak list --app 2>/dev/null | grep -q "org.videolan.VLC"; then
        HAS_VLC_FLATPAK=1
    fi
fi

if [ $HAS_VLC_NATIVE -eq 0 ] && [ $HAS_VLC_FLATPAK -eq 0 ]; then

    echo ""
    echo "VLC is optional but recommended."
    echo "Used for DVD previews in NullRip."
    echo ""

    echo "1) apt"
    echo "2) flatpak"
    echo "3) skip"
    echo ""

    read -r -p "Choice (1/2/3): " choice

    case "$choice" in

        1)
            sudo apt install -y vlc
            ;;

        2)
            if ! command -v flatpak >/dev/null 2>&1; then
                sudo apt install -y flatpak
            fi

            flatpak install -y flathub org.videolan.VLC

            echo ""
            echo "If DVD playback fails:"
            echo "flatpak override --user --filesystem=/media org.videolan.VLC"
            ;;

        *)
            echo "Skipping VLC install."
            ;;
    esac
fi

# ==============================
# Permissions
# ==============================

chmod +x "$RUNTIME_DIR"/*.sh 2>/dev/null

# ==============================
# Desktop Entry
# ==============================

DESKTOP_FILE="$HOME/.local/share/applications/nullsuite.desktop"

FULL_PATH="$(realpath "$RUNTIME_DIR/NSLauncher.sh")"

ICON_PATH="$(realpath "$RUNTIME_DIR/NullSuite.png" 2>/dev/null)"

echo "Creating desktop entry..."

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=NullSuite
Exec=$FULL_PATH
Icon=$ICON_PATH
Type=Application
Terminal=false
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"

update-desktop-database \
    "$HOME/.local/share/applications" \
    2>/dev/null

# ==============================
# NullProton Setup
# ==============================

echo ""
echo "Installation complete...but wait theres more!"
echo ""

echo "Do you intend to use NullProton?"
echo "It allows you to run games outside Steam 😉"
echo ""

read -r -p "Proceed? (y/n): " confirm

if [[ "$confirm" =~ ^[Yy]$ ]]; then

    echo ""
    echo "Setting up NullProton..."

    HOME_DIR="$HOME"

    PATH1="$HOME_DIR/.steam/root/compatibilitytools.d"
    PATH2="$HOME_DIR/.local/share/Steam/compatibilitytools.d"

    if [ -d "$PATH1" ]; then
        START_DIR="$PATH1"

    elif [ -d "$PATH2" ]; then
        START_DIR="$PATH2"

    else
        START_DIR="$HOME_DIR"
    fi

    PROTON_PATH=$(zenity --file-selection \
        --title="Select Proton executable (proton)" \
        --filename="$START_DIR/" \
        --file-filter="Proton executable | proton")

    if [ -z "$PROTON_PATH" ]; then

        echo "User cancelled. Skipping NullProton."

    elif [ "$(basename "$PROTON_PATH")" != "proton" ]; then

        echo "Invalid selection."

    else

        echo "Proton set to:"
        echo "$PROTON_PATH"

        CONFIG_DIR="$BASE_DIR/Runtime/Config"
        CONFIG_FILE="$RUNTIME_DIR/NullSuite.json"
        PROTON_DRIVE="$RUNTIME_DIR/ProtonDrive"

        if [ ! -f "$CONFIG_FILE" ]; then

            cat > "$CONFIG_FILE" <<EOF
{
  "NullProton": {},
  "NullWire": {},
  "NullCursor": {},
  "NullMidi": {}
}
EOF
        fi

        # Patch NullProton section
        TMP_FILE=$(mktemp)

        if jq --arg proton "$PROTON_PATH" '
            .NullProton.Default = $proton
        ' "$CONFIG_FILE" > "$TMP_FILE"; then

            mv "$TMP_FILE" "$CONFIG_FILE"

        else
            echo "Failed to update NullSuite config."
            rm -f "$TMP_FILE"
        fi

        QUICK_DESKTOP="$HOME/.local/share/applications/QuickNullProton.desktop"

        QUICK_PATH="$(realpath "$RUNTIME_DIR/QuickNullProton.sh")"

        ICON_PATH2="$(realpath "$RUNTIME_DIR/NullSuite.png" 2>/dev/null)"

        cat > "$QUICK_DESKTOP" <<EOF
[Desktop Entry]
Name=NullProton
Exec=$QUICK_PATH %f
Type=Application
Icon=$ICON_PATH2
MimeType=application/x-ms-dos-executable;application/x-dosexec;application/x-executable;
Terminal=true
NoDisplay=true
EOF

        chmod +x "$QUICK_DESKTOP"

        mkdir -p "$PROTON_DRIVE"

        echo ""
        echo "Proton Drive created at:"
        echo "$PROTON_DRIVE"
        echo ""

        echo "You can now right-click .exe files"
        echo "and launch them with NullProton."

    fi
else
    echo "Skipping NullProton setup."
fi

update-desktop-database \
    "$HOME/.local/share/applications" \
    2>/dev/null

echo ""
echo "You're done 👍"
echo "Launch NullSuite from your applications menu."
echo ""

read