#=============================================================================
# Refinitiv Data Platform demo app to get OAuth access tokens
# Following sequence is followed:
#    1. Read access token from the already created token file, if the token is not expired
#    2. Try using refresh token, if token is expired
#    3. Try to use password grant if refresh token fails, or no token file exists
#    For password grant:
#        a. Use credentials file, if available
#        b. Use the command line parameters, if available 
#        c. Use the hardcoded USERNAME, PASSWORD parameters from this module
#
# CLIENT_ID see instructions at https://developers.refinitiv.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/quick-start
# UUID is required for research messages only and will be provided by Refinitiv
#-----------------------------------------------------------------------------
#   This source code is provided under the Apache 2.0 license
#   and is provided AS IS with no warranty or guarantee of fit for purpose.
#   Copyright (C) 2021 Refinitiv. All rights reserved.
#=============================================================================
import requests, json, time, getopt, sys, configparser
import requests, json
from datetime import datetime, timedelta
import sys
import time
import getopt
import socket
import json

# User Credentials
USERNAME  = ''
PASSWORD  = ''
CLIENT_ID = ''
UUID       = ''

# Application Constants
base_URL = "https://api.refinitiv.com"
category_URL = "/auth/oauth2"
RDP_version = "/v1"
endpoint_URL = "/token"
CLIENT_SECRET = ""
SCOPE = "trapi"

CREDENTIALS_FILE = "credentials.ini"
TOKEN_FILE = "token.txt"

#==============================================
def _loadCredentialsFromFile():
#==============================================
    global USERNAME, PASSWORD, CLIENT_ID, UUID
    try:
        config = configparser.ConfigParser()
        config.read(CREDENTIALS_FILE)
        
        USERNAME = config['RDP']['username']
        PASSWORD = config['RDP']['password']
        CLIENT_ID = config['RDP']['clientId']
        UUID = config['RDP']['uuid']

        print("Read credentials from file")
    except Exception:
        # ignore if no creds file
        pass

#==============================================
def _requestNewToken(refreshToken):
#==============================================
    # try to read user credentials from a file
    _loadCredentialsFromFile()
    TOKEN_ENDPOINT = base_URL + category_URL + RDP_version + endpoint_URL
    
    if refreshToken is None:
        # formulate the request payload
        tData = {
            "username": USERNAME,
            "password": PASSWORD,
            "grant_type": "password",
            "scope": SCOPE,
            "takeExclusiveSignOnControl": "true"
        }
    else:
        tData = {
            "refresh_token": refreshToken,
            "grant_type": "refresh_token",
        }

    # Make a REST call to get latest access token
    response = requests.post(
        TOKEN_ENDPOINT,
        headers = {
            "Accept": "application/json"
        },
        data = tData, 
        auth = (
            CLIENT_ID,
            CLIENT_SECRET
        )
    )

    if (response.status_code == 400) and ('invalid_grant' in response.text):
        return None
    
    if response.status_code != 200:
        raise Exception("Failed to get access token {0} - {1}".format(response.status_code, response.text))

    # return the new token
    return json.loads(response.text)


#==============================================
def _saveToken(tknObject):
#==============================================
    tf = open(TOKEN_FILE, "w+")
    print("Saving the new token")
    # append the expiry time to token
    tknObject["expiry_tm"] = time.time() + int(tknObject["expires_in"]) - 10
    # store it in the file
    json.dump(tknObject, tf, indent=4)
    tf.close()
    
#==============================================
def _loadToken():
#==============================================
    tknObject = None
    try:
        # read the token from a file
        tf = open(TOKEN_FILE, "r+")
        tknObject = json.load(tf)
        tf.close()
        print("Existing token read from: " + TOKEN_FILE)
    except Exception:
        pass

    return tknObject

#==============================================
def getToken():
#==============================================
    global tknObject
    tknObject = _loadToken()

    if tknObject is not None:
        # is access token valid
        if tknObject["expiry_tm"] > time.time():
            # return access token
            return tknObject["access_token"]

        print("Token expired, refreshing a new one...")
        
        # get a new token using refresh token
        tknObject = _requestNewToken(tknObject["refresh_token"])
        # if refresh grant failed
        if tknObject is None:
            print("Refresh token expired, using Password Grant...")
            # use password grant
            tknObject = _requestNewToken(None)
    else:
        print("Getting a new token using Password Grant...")
        tknObject = _requestNewToken(None)

    # persist this token for future queries
    _saveToken(tknObject)
    # return access token
    return tknObject["access_token"]
