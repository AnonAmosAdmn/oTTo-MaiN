#!/bin/bash

#==============================================================================#
#                     oTTo-MAIN.sh™️ by Aenon Amos Adin Al Amin                 #
#==============================================================================#
#                  This code is the user entry point to oTTo-MaiN              #
#______________________________________________________________________________#

BLACK='\033[0;30m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
NC='\033[0m'
BOLD='\033[1m'

oTTo-ui() {
    local type=$1
    local message=$2
    case $type in
        clear)
            clear
            echo
            echo -e "${GREEN}${BOLD}
   ██████╗ ████████╗████████╗ ██████╗       ███╗   ███╗ █████╗ ██╗███╗   ██╗
  ██╔═══██╗╚══██╔══╝╚══██╔══╝██╔═══██╗      ████╗ ████║██╔══██╗██║████╗  ██║
  ██║   ██║   ██║      ██║   ██║   ██║█████╗██╔████╔██║███████║██║██╔██╗ ██║
  ██║   ██║   ██║      ██║   ██║   ██║╚════╝██║╚██╔╝██║██╔══██║██║██║╚██╗██║
  ╚██████╔╝   ██║      ██║   ╚██████╔╝      ██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
   ╚═════╝    ╚═╝      ╚═╝    ╚═════╝       ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝${NC}\n"
            echo -e "${GREEN}${BOLD}                oTTo-MaiN™️ v 0.11.0 ${BLACK}${BOLD} by Aenon Amos Adin Al Amin ${NC}\n"
            echo
            ;;
        spacer)
            echo -e "${GREEN}${BOLD}_______________________________________________________________________________${NC}\n"
            ;;
        pause)
            echo
            sleep 2
            #read -p "Press ENTER to continue..." -r
            clear
            ;;
        title)
            oTTo-ui clear
            oTTo-ui spacer
            echo -e "${GREEN}${BOLD}$(echo "$message" | tr '[:lower:]' '[:upper:]' | awk '{ printf "%*s\n", '"$(tput cols)"'/2+length($0)/2, $0 }')${NC}\n"
            ;;
        info)
            oTTo-ui spacer            
            echo -e "${MAGENTA}${BOLD}${message}${NC}\n"
            ;;
        data)
            echo -e "${CYAN}${BOLD}${message}${NC}\n"
            ;;
        text)
            echo -e "${BLACK}${BOLD}${message}${NC}\n"
            ;;
        menu)
            local title=$2
            shift 2
            local options=("$@")
            echo -e "${GREEN}${BOLD}$(echo "$title" | tr '[:lower:]' '[:upper:]')${NC}"
            for i in "${!options[@]}"; do
                echo -e "${WHITE}${BOLD}${options[$i]}${NC}"
            done
            ;;
        input)
            local input_variable=$3
            local placeholder=$4
            echo -en "${GREEN}$message [$placeholder]: ${NC}"
            read -r input
            input=$(oTTo-sanitize "$input")
            if [ -z "$input" ]; then
                input="$placeholder"
            fi
            export $input_variable="$input"
            ;;
        success)
            oTTo-ui spacer
            echo -e "${GREEN}${BOLD}SUCCESS : ${message}${NC} $CURRENT_DATE $CURRENT_TIME \n"
            ;;
        log)
            echo -e "${CYAN}${BOLD}LOG : ${message}${NC} $CURRENT_DATE $CURRENT_TIME \n"
            ;;
        alert)
            echo -e "${YELLOW}${BOLD}WARNING : ${message}${NC} $CURRENT_DATE $CURRENT_TIME \n"
            ;;
        error)
            echo -e "${RED}${BOLD}ERROR : ${message}${NC} $CURRENT_DATE $CURRENT_TIME \n"
            ;;
        erase)
            echo -en "\r\033[K"
            ;;
        progress)
            local duration=$2
            local elapsed=0
            already_done() { 
                for ((done=0; done<elapsed; done++)); do 
                    echo -n "🟩"; 
                done 
            }
            remaining() { 
                for ((remain=elapsed; remain<duration; remain++)); do 
                    echo -n "."; 
                done 
            }
            percentage() { 
                echo -n " $((elapsed * 100 / duration))%"; 
            }

            while (( elapsed < duration )); do
                elapsed=$((elapsed + 1))
                echo -ne "\r["
                already_done
                remaining
                echo -n "]"
                percentage
                sleep 1
                oTTo-ui erase
            done

            echo -ne "\r["
            already_done
            echo -n "] 100%"
            echo
            ;;
        confirm)
            echo -e "${YELLOW}${BOLD}$message (y/n)? ${NC}"
            read -r confirmation
            case "$confirmation" in
                [yY][eE][sS]|[yY]) return 0 ;;
                *) return 1 ;;
            esac
            ;;
        *)
            echo -e "${WHITE}${BOLD}${message}${NC}"
            ;;
    esac
}

command_exists() { command -v "$1" >/dev/null 2>&1; }

oTTo-sanitize() {
    local input="$1"
    input="$(echo "$input" | xargs)"
    input="$(echo "$input" | tr -cd '[:print:]')"
    input="$(echo "$input" | sed 's/[;|&<>]//g')"
    echo "$input"
}

oTTo-apt_lock() {
    while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
        oTTo-ui log "Waiting for apt lock 🔐"
        sleep 5
    done
}

oTTo-init() {
    trap 'echo; oTTo-ui error "Script interrupted."; exit 1' INT TERM
    rm -rf log venv visualize.py
    mkdir -p log
    exec > >(tee -i log/otto.log) 2>&1
}

oTTo-update() {
    oTTo-ui title "oTTo Update"
    oTTo-ui info "Cleaning Up ..."
    sudo apt-get clean && oTTo-apt_lock
    oTTo-ui info "Installing Required Packages ..."
    sudo apt-get install -y tmux sqlite3 xdg-utils software-properties-common apt-transport-https curl wget gzip tar unzip git build-essential python3 python3-venv python3-pip python3-tk python3-bs4 python3-flask python3-flask-cors python3-flask-socketio python3-flask-sqlalchemy python3-eventlet python3-dotenv libgtk-3-dev libvte-2.91-dev python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91 python3-m2crypto && oTTo-apt_lock
    oTTo-ui info "Updating Packages ..."
    sudo apt-get update && oTTo-apt_lock
    oTTo-ui info "Installing Full Upgrade ..."
    sudo apt-get full-upgrade -y && oTTo-apt_lock
    oTTo-ui info "Installing Distro Upgrade ..."
    sudo apt-get dist-upgrade -y && oTTo-apt_lock
    oTTo-ui info "AutoClean APT ..."
    sudo apt-get autoclean -y && oTTo-apt_lock
    oTTo-ui success "oTTo Update was Successful."
    oTTo-ui pause
}

oTTo-python() {
    oTTo-ui title "oTTo Python"
    oTTo-ui info "Updating venv..."
    if [ ! -d "venv" ]; then
        oTTo-ui error "Virtual environment not found."
        oTTo-ui info "Creating venv..."
        python3 -m venv venv || { oTTo-ui error "Failed to create virtual environment."; exit 1; }
    fi    
    source venv/bin/activate || { oTTo-ui error "Failed to activate virtual environment."; exit 1; }
    oTTo-ui success "Virtual environment activated."
    oTTo-ui info "Upgrading PIP..."
    python -m pip install --upgrade pip || { oTTo-ui error "Failed to upgrade pip."; exit 1; }
    oTTo-ui info "Installing pre-requisites ..."
    pip install --upgrade setuptools wheel || { oTTo-ui error "Failed to install pre-requisites."; exit 1; }
    oTTo-ui info "Installing Python requirements ..."
    pip install Flask Flask-Cors Flask-SocketIO Flask-SQLAlchemy eventlet python-dotenv bs4 || { oTTo-ui error "Failed to install Python requirements."; exit 1; }
    pip install qiskit spacy scikit-learn plotly numpy matplotlib || { oTTo-ui error "Failed to install advanced Python packages."; exit 1; }
    python -m spacy download en_core_web_md || { oTTo-ui error "Failed to download spaCy language model."; exit 1; }
    oTTo-ui success "Python setup successful."
    oTTo-ui pause
}

oTTo-ollama() {
    oTTo-ui title "Installing Ollama LLM ..."
    
    if command -v ollama &>/dev/null; then
        oTTo-ui success "Ollama is already installed."
    else
        oTTo-log "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | bash || { oTTo-error "Failed to install Ollama."; exit 1; }
        if [ $? -ne 0 ]; then
            oTTo-ui error "Failed to install Ollama. Exiting."
            return 1
        fi
        oTTo-ui success "Ollama installed successfully."
    fi

    if ! pgrep -x "ollama" > /dev/null; then
        oTTo-ui log "Starting Ollama service..."
        nohup ollama serve &
        sleep 5
        if ! pgrep -x "ollama" > /dev/null; then
            oTTo-ui error "Failed to start Ollama service. Exiting."
            exit 1
        else
            oTTo-ui success "Ollama service started successfully."
        fi
    else
        oTTo-ui log "Ollama service is already running."
    fi
    
    oTTo-ui log "Pulling required Ollama models..."
    if ! ollama list | grep -q "mistral"; then
        ollama pull mistral || { oTTo-ui error "Failed to pull Mistral model."; exit 1; }
    fi
    oTTo-ui success "Ollama LLM Tool and models configured successfully."
    oTTo-ui pause
}

oTTo-tmux() {
    python3 app.py & python3 dash.py &
    tmux select-layout tiled
    tmux -2 attach-session -d
}

oTTo-exit() {
    if command_exists deactivate; then
        deactivate 2>/dev/null
    fi
    oTTo-ui title "Good Bye oTTo ..."
    oTTo-ui progress 5
    clear
    exit 0
}

oTTo-main() {
    oTTo-init || { oTTo-ui error "Initialization failed. Exiting..."; exit 1; }
    oTTo-update || { oTTo-ui error "Update failed. Exiting..."; exit 1; }
    oTTo-python || { oTTo-ui error "Python setup failed. Exiting..."; exit 1; }
    oTTo-ollama || { oTTo-ui error "Ollama setup failed. Exiting..."; exit 1; }
    oTTo-tmux || { oTTo-ui error "Ollama setup failed. Exiting..."; exit 1; }
    oTTo-exit 
}


oTTo-main