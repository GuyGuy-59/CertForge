#!/bin/bash
#
# PKI Manager - Common Functions Library
# Shared utilities used by all PKI Manager scripts
#

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Error handling
error_exit() {
    echo -e "${RED}ERROR:${NC} $1" >&2
    exit 1
}

# Warning message
warning() {
    echo -e "${YELLOW}WARNING:${NC} $1" >&2
}

# Info message
info() {
    echo -e "${GREEN}INFO:${NC} $1"
}

# Success message
success() {
    echo -e "${GREEN}SUCCESS:${NC} $1"
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v openssl &> /dev/null; then
        missing_deps+=("openssl")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        error_exit "Missing required dependencies: ${missing_deps[*]}"
    fi
}

# Generate random password
generate_password() {
    local length="${1:-65}"
    local password
    
    # Try to generate password from /dev/urandom
    if [ -r /dev/urandom ]; then
        password=$(< /dev/urandom tr -dc "+=\-%*\!&#':;{}()[]|^~\$_2-9T-Z" | head -c"$length" 2>/dev/null || echo "")
    else
        # Fallback to openssl if /dev/urandom is not available
        password=$(openssl rand -base64 "$length" 2>/dev/null | tr -dc "+=\-%*\!&#':;{}()[]|^~\$_2-9T-Z" | head -c"$length" || echo "")
    fi
    
    # Verify password was generated
    if [ -z "$password" ] || [ ${#password} -lt "$length" ]; then
        return 1
    fi
    
    echo -n "$password"
    return 0
}

# Get script directory (handles symlinks)
get_script_dir() {
    local script_path="${BASH_SOURCE[0]}"
    if [ -L "$script_path" ]; then
        script_path=$(readlink -f "$script_path" 2>/dev/null || echo "$script_path")
    fi
    dirname "$script_path"
}

# Get project root directory (parent of lib/)
get_project_root() {
    local lib_dir
    lib_dir=$(get_script_dir)
    dirname "$lib_dir"
}

# Find template file
find_template() {
    local template_name="$1"
    local project_root
    project_root=$(get_project_root)
    local template_file="${project_root}/templates/${template_name}"
    
    if [ -f "$template_file" ]; then
        echo "$template_file"
        return 0
    fi
    
    return 1
}

# Validate project directory
validate_project_dir() {
    local project_dir="$1"
    local required_files=("ca.crt" "ca.key" "ca.pass" "ca.cnf")
    local missing_files=()
    
    if [ ! -d "$project_dir" ]; then
        error_exit "Project directory '$project_dir' does not exist. Please create the CA first."
    fi
    
    for file in "${required_files[@]}"; do
        if [ ! -f "${project_dir}/${file}" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        error_exit "Missing required CA files in project directory: ${missing_files[*]}

Please create the CA first using: bin/pki-ca create"
    fi
}

# Normalize serial number
normalize_serial() {
    local serial="$1"
    local normalized
    
    # Remove leading zeros and convert to uppercase
    normalized=$(echo "$serial" | sed 's/^0*//' | tr '[:lower:]' '[:upper:]')
    
    # Handle case where all zeros were removed
    if [ -z "$normalized" ]; then
        normalized="0"
    fi
    
    echo "$normalized"
}

