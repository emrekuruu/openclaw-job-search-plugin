# !/bin/bash

#Uninstall the old plugin.
openclaw plugins uninstall job-search         
rm -rf ~/.openclaw/extensions/job-search

# Install current working directory as the plugin to test changes.
openclaw plugins install .

# Restart the gateway to apply changes.
openclaw gateway restart   
