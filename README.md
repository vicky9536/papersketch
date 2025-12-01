# Running Steps

## Step 1: Setup
make sure you have papersketch url and api key
install mcp, uv, httpx
check official doc: https://modelcontextprotocol.io/docs/develop/build-server

## Step 2: Run Server
open project folder
run: uv run src/papersketch/server.py

## Step 3: Open MCP Inspector
open a separate terminal window
run: npx @modelcontextprotocol/inspector

## Step 4: Create ChatCPT Connector
run: ngrok http 8000
note: need to setup ngrok
get the url from ngrok output
then create the ChatGPT connector
