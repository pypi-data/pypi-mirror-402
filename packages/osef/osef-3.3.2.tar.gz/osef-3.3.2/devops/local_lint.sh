#!/bin/bash

BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}## Format code${NC}"
black .

echo -e "\n${BLUE}${BOLD}## Pylint code${NC}"
pylint osef/ --rcfile=devops/.pylintrc

# TODO. Add mypy
# echo -e "${BLUE}${BOLD}## Static typing${NC}"
# mypy --install-types --non-interactive osef/ tests/
