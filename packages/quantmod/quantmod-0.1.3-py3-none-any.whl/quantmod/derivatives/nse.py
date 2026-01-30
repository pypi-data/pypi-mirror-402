# updated to new nse api changes on 10th Dec 2025
import os, sys
import requests
import numpy as np
import pandas as pd
import json
import random
import datetime, time
import logging
import re
import urllib.parse

# --- Configuration ---
mode = "auto"  # can be "local", "vpn", or "auto"

headers = {"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", 
           "accept-language": "en-US,en;q=0.9,en-IN;q=0.8,en-GB;q=0.7", 
           "cache-control": "max-age=0", 
           "priority": "u=0, i", 
           "sec-ch-ua": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"', "sec-ch-ua-mobile": "?0", 
           "sec-ch-ua-platform": '"Windows"', 
           "sec-fetch-dest": "document", 
           "sec-fetch-mode": "navigate", 
           "sec-fetch-site": "none", 
           "sec-fetch-user": "?1", 
           "upgrade-insecure-requests": "1", 
           "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
}

curl_headers = ''' -H "authority: beta.nseindia.com" -H "cache-control: max-age=0" -H "dnt: 1" -H "upgrade-insecure-requests: 1" -H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36" -H "sec-fetch-user: ?1" -H "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9" -H "sec-fetch-site: none" -H "sec-fetch-mode: navigate" -H "accept-encoding: gzip, deflate, br" -H "accept-language: en-US,en;q=0.9,hi;q=0.8" --compressed'''

# --- Main function ---
def nsefetch(payload: str): 
    def encode(url: str) -> str: 
        if "%26" in url or "%20" in url: 
            return url 
        return urllib.parse.quote(url, safe=":/?&=")
 
    def refresh_cookies(): 
        os.popen(f'curl -c cookies.txt "https://www.nseindia.com" {curl_headers}').read() 
        os.popen(f'curl -b cookies.txt -c cookies.txt "https://www.nseindia.com/option-chain" {curl_headers}').read()
        
    def curl_fetch(url: str):
        encoded_url = encode(url)
        if not os.path.exists("cookies.txt"):
            refresh_cookies()
        cmd = f'curl -b cookies.txt "{encoded_url}" {curl_headers}'
        raw = os.popen(cmd).read()
        try:
            return json.loads(raw)
        except ValueError:
            refresh_cookies()
            raw = os.popen(cmd).read()
            try:
                return json.loads(raw)
            except ValueError:
                return {}

    def requests_fetch(url: str):
        try:
            s = requests.Session()
            s.get("https://www.nseindia.com", headers=headers, timeout=10)
            s.get("https://www.nseindia.com/option-chain", headers=headers, timeout=10)
            return s.get(url, headers=headers, timeout=10).json()
        except Exception:
            return {}

    # --- Auto / Mode selection ---
    if mode == "local":
        return requests_fetch(payload)
    elif mode == "vpn":
        return curl_fetch(payload)
    else:
        # Auto mode: try requests first, fallback to curl
        data = requests_fetch(payload)
        if not data:
            print("⚠️ Local fetch failed — switching to curl + cookies.")
            data = curl_fetch(payload)
        return data
    
# --- Utility constants ---
indices = ["NIFTY", "FINNIFTY", "BANKNIFTY"]


class OptionData:
    """
    A class to fetch and analyze option chain data from NSE.

    Parameters
    ----------
    symbol : str
        Trading symbol of the stock/index (e.g., 'NIFTY', 'RELIANCE')
    expiry_dt : str
        Expiry date in format '%d-%b-%Y' (e.g., '27-Mar-2025')
        Note: Month should be first 3 letters capitalized (Jan, Feb, Mar, etc.)

    Attributes
    ----------
    get_put_call_ratio : float
        Put-Call ratio based on open interest
    get_maximum_pain_strike : float
        Maximum pain strike price
    get_call_option_data : pandas.DataFrame
        Call option chain data
    get_put_option_data : pandas.DataFrame
        Put option chain data

    Methods
    -------
    get_option_quote : float
        Get option quote for specific strike price, option type and transaction intent
    get_synthetic_future_price : float
        Calculate synthetic futures price using put-call parity
    """

    def __init__(self, symbol, expiry_dt):
        """
        Initialize the OptionData class.

        Parameters
        ----------
        symbol : str
            Trading symbol of the stock/index (e.g., 'NIFTY', 'RELIANCE')
        expiry_dt : str
            Expiry date in format '%d-%b-%Y' (e.g., '27-Mar-2025')
            Note: Month should be first 3 letters capitalized (Jan, Feb, Mar, etc.)
        """
        self.expiry_dt = expiry_dt
        self.symbol = symbol.replace(
            "&", "%26"
        )  # URL Parse for Stocks Like M&M Finance
        self.payload = self._nse_optionchain_scrapper()

        self.get_put_call_ratio = self._get_option_pcr()
        self.get_maximum_pain_strike = self._get_maximum_pain_strike()
        self.get_call_option_data = self._get_call_option_data()
        self.get_put_option_data = self._get_put_option_data()

    def _nse_optionchain_scrapper(self):
        """
        Fetch option chain data from NSE website.

        Returns
        -------
        dict
            Raw option chain data from NSE API
        """
        if any(x in self.symbol for x in indices):
            payload = nsefetch(
                f"https://www.nseindia.com/api/option-chain-v3?type=Indices&symbol={self.symbol}&expiry={self.expiry_dt}"
            )
        else:
            payload = nsefetch(
                f"https://www.nseindia.com/api/option-chain-v3?type=Equity&symbol={self.symbol}&expiry={self.expiry_dt}"
            )
        return payload


    def get_option_quote(self, strikePrice, optionType, intent=""):
        """
        Get option quote for specific strike price and option type.

        Parameters
        ----------
        strikePrice : float
            Strike price of the option
        optionType : str
            Type of option, either 'CE' (Call) or 'PE' (Put)
        intent : str, optional
            Quote type:
            - '' (default) lastPrice
            - 'sell' for sellPrice1
            - 'buy' for buyPrice1

        Returns
        -------
        float
            Option price based on the specified intent
        """
        for x in range(len(self.payload["records"]["data"])):
            if (self.payload["records"]["data"][x]["strikePrice"] == strikePrice):
                if intent == "":
                    return self.payload["records"]["data"][x][optionType]["lastPrice"]
                if intent == "sell":
                    return self.payload["records"]["data"][x][optionType]["sellPrice1"]
                if intent == "buy":
                    return self.payload["records"]["data"][x][optionType]["buyPrice1"]

    
    def _get_option_pcr(self):
        """
        Calculate Put-Call Ratio based on open interest.

        Returns
        -------
        float
            Put-Call ratio rounded to 2 decimal places
        """
        ce_oi = 0
        pe_oi = 0
        for i in self.payload["records"]["data"]:
            try:
                ce_oi += i["CE"]["openInterest"]
                pe_oi += i["PE"]["openInterest"]
            except KeyError:
                pass
        return round(pe_oi / ce_oi, 2)

    
    def get_synthetic_future_price(self, strike):
        """
        Calculate synthetic futures price using put-call parity.

        Parameters
        ----------
        strike : float
            Strike price to use for calculation

        Returns
        -------
        float
            Synthetic futures price
        """
        synthetic_futures = (
            strike
            + self.get_option_quote(strike, "CE", "buy")
            - self.get_option_quote(strike, "PE", "sell")
        )
        return synthetic_futures


    def _get_call_option_data(self):
        """
        Get call options data for current expiry.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing call options data sorted by strike price
        """
        ce_values = [
            data["CE"]
            for data in self.payload["records"]["data"]
        ]
        return pd.DataFrame(ce_values).sort_values(["strikePrice"])
    
    
    
    def _get_put_option_data(self):
        """
        Get put options data for current expiry.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing put options data sorted by strike price
        """
        pe_values = [
            data["PE"]
            for data in self.payload["records"]["data"]
        ]
        return pd.DataFrame(pe_values).sort_values(["strikePrice"])
    
    
    def _get_maximum_pain_strike(self):
        """
        Calculate maximum pain strike price.

        Returns
        -------
        float
            Strike price where maximum pain occurs
        """
        calls = self._get_call_option_data()
        strikes = calls["strikePrice"]
        ce_oi = calls["openInterest"]
        pe_oi = self._get_put_option_data()["openInterest"]

        total_pain = [
            sum(ce_oi * np.maximum(0, expiry_price - strikes))
            + sum(pe_oi * np.maximum(0, strikes - expiry_price))
            for expiry_price in strikes
        ]

        return strikes[np.argmin(total_pain)]