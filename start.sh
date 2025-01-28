#!/bin/bash
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

streamlit run streamlitui.py --server.port=$PORT --server.address=0.0.0.0 --browser.serverAddress=0.0.0.0 --server.maxUploadSize=10
