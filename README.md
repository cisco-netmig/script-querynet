![Project Logo](./__icon__.ico)

# Querynet

## Overview  
**Querynet** is a network automation tool designed to interact with Azure AI to automate the process of querying network devices. It runs device commands and formats the results into a concise and readable format to assist in network diagnostics and troubleshooting.

## Features  
- Runs device-specific commands on multiple network devices using Azure AI's natural language processing.  
- Retrieves and formats results in a structured layout for easy readability.  
- Handles connections via proxy and supports multiple network device types.  
- Uses threading to execute commands concurrently on multiple devices.  
- Integrates with Azure AI to automatically generate necessary network commands.

## Migration Lifecycle 
- **Pre-Migration**: Collect and analyze device information before migration.  
- **Post-Migration**: Collect data and compare post-migration device states.

## Usage  
- Add network devices (IPs or hostnames) to the input field.  
- Enter a query to ask the network devices (e.g., "Check OSPF neighbors").  
- Click the "Send" button to execute the query.  
- The results will be formatted and displayed in the chat interface.  
- Access the AzureAI configuration via the "Configure" button to update the `.env` file.

## Tags  
`#NetworkAutomation` `#AzureAI` `#Netmig` `#NetworkMigration` `#Diagnostics` `#Automation` `#NetworkCommands` `#DeviceLogs` `#AI` `#AzureIntegration` `#ThreadedExecution`
