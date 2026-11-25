#!/bin/bash
# Simple launcher: runs the Microdrop source's own entry point,
# `pixi run microdrop --device <device>`, which always loads the current
# release's full plugin set. Git operations and pixi self-update live in
# microdrop_setup.py; launch_microdrop.sh is the fine-grained counterpart.
# Location-independent: --install-dir points at the pixi-microdrop checkout and
# defaults to this script's own folder (so a direct run from the repo root
# still works); microdrop_setup passes it explicitly when it lives elsewhere.

# Define Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GRAY='\033[0;90m'
NC='\033[0m'

# Paths (may be overridden by --install-dir below):
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
INSTALL_DIR="$SCRIPT_DIR"
DEVICE="dropbot"

# Parse arguments: --install-dir takes the checkout root, --device the device.
while [[ $# -gt 0 ]]; do
    case "$1" in
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --device)
            DEVICE="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Error: unknown argument '$1'${NC}"
            exit 1
            ;;
    esac
done

case "$DEVICE" in
    dropbot|portable|opendrop|mock) ;;
    *)
        echo -e "${RED}Error: unknown device '$DEVICE' (dropbot, portable, opendrop or mock)${NC}"
        exit 1
        ;;
esac

# Set the terminal window title (xterm/VTE escape; ignored by terminals that
# don't support it).
echo -ne '\033]0;Microdrop (Beta)\007'

# Configuration:
export QT_MEDIA_BACKEND=gstreamer
systemctl --user stop wireplumber
echo "Wireplumber stopped and QT backend variable set."

# Paths:
PARENT_PATH="$INSTALL_DIR/microdrop-py"

# Environment and Plugins:
ENV_ROOT="$PARENT_PATH/.pixi/envs/default"
export LD_LIBRARY_PATH="$ENV_ROOT/lib:$LD_LIBRARY_PATH"

QT_PLATFORMS=$(ls -d "$ENV_ROOT"/lib/python*/site-packages/PySide6/Qt/plugins/platforms 2>/dev/null | head -n 1)
export QT_QPA_PLATFORM_PLUGIN_PATH="$QT_PLATFORMS"
echo "Qt Platforms path set to: $QT_PLATFORMS"

echo -e "${CYAN}----------------------------------------${NC}"
echo -e "${GREEN}      Pixi Microdrop Launcher           ${NC}"
echo -e "${CYAN}----------------------------------------${NC}"

if ! command -v pixi &> /dev/null; then
    echo -e "${RED}Error: 'pixi' command not found. Is it installed and in your PATH?${NC}"
    exit 1
fi

if [ ! -d "$PARENT_PATH" ]; then
    echo -e "${RED}Error: microdrop-py not found at $PARENT_PATH${NC}"
    exit 1
fi

cd "$PARENT_PATH" || exit 1

echo -e "${MAGENTA}Starting Microdrop...${NC}"
pixi run microdrop --device "$DEVICE"

echo -e "${CYAN}----------------------------------------${NC}"
echo -e "${GRAY}Done.${NC}"
