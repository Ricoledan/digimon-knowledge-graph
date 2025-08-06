#!/bin/bash
# Main entry point script for common operations

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════╗"
    echo "║     Digimon Knowledge Graph          ║"
    echo "║      Project Management Script       ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

show_menu() {
    echo "What would you like to do?"
    echo ""
    echo "  ${GREEN}Setup & Configuration:${NC}"
    echo "    1) Initial setup"
    echo "    2) Check requirements"
    echo "    3) Install dependencies"
    echo ""
    echo "  ${GREEN}Database Operations:${NC}"
    echo "    4) Start Neo4j"
    echo "    5) Stop Neo4j"
    echo "    6) Backup database"
    echo "    7) Restore database"
    echo ""
    echo "  ${GREEN}Scraping Operations:${NC}"
    echo "    8) Investigate HTML structure"
    echo "    9) Run scraper"
    echo "   10) Resume scraping"
    echo ""
    echo "  ${GREEN}Analysis:${NC}"
    echo "   11) Run analysis"
    echo "   12) Export results"
    echo "   13) Start Jupyter notebook"
    echo ""
    echo "  ${GREEN}Other:${NC}"
    echo "   14) View logs"
    echo "   15) Clean cache"
    echo "    0) Exit"
    echo ""
}

execute_choice() {
    case $1 in
        1) $SCRIPT_DIR/setup/init.sh ;;
        2) $SCRIPT_DIR/setup/check_requirements.sh ;;
        3) $SCRIPT_DIR/setup/install_deps.sh ;;
        4) $SCRIPT_DIR/database/start_neo4j.sh ;;
        5) docker-compose stop neo4j ;;
        6) $SCRIPT_DIR/database/backup_neo4j.sh ;;
        7) 
            echo "Available backups:"
            ls -la ./backups/*.dump 2>/dev/null || echo "No backups found"
            read -p "Enter backup file path: " backup_file
            $SCRIPT_DIR/database/restore_neo4j.sh "$backup_file"
            ;;
        8) $SCRIPT_DIR/scraping/investigate_structure.sh ;;
        9) $SCRIPT_DIR/scraping/run_scraper.sh ;;
        10) $SCRIPT_DIR/scraping/resume_scraping.sh ;;
        11) $SCRIPT_DIR/analysis/run_analysis.sh ;;
        12) 
            echo "Export format: [csv|json|graphml|all]"
            read -p "Enter format: " format
            $SCRIPT_DIR/analysis/export_results.sh "$format"
            ;;
        13) 
            if [ -z "$VIRTUAL_ENV" ] && [ ! -n "$IN_NIX_SHELL" ]; then
                echo "Please activate your Python environment first"
            else
                jupyter notebook
            fi
            ;;
        14) 
            if [ -f "./logs/digimon_kg.log" ]; then
                tail -f ./logs/digimon_kg.log
            else
                echo "No log file found"
            fi
            ;;
        15) 
            read -p "Are you sure you want to clean the cache? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -rf ./data/cache/*
                echo "[OK] Cache cleaned"
            fi
            ;;
        0) 
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *) 
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
}

# Main loop
show_banner

while true; do
    show_menu
    read -p "Enter your choice: " choice
    echo ""
    execute_choice $choice
    echo ""
    read -p "Press Enter to continue..."
    clear
    show_banner
done