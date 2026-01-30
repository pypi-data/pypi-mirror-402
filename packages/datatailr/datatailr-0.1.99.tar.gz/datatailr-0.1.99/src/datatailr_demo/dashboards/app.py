##########################################################################
#
#  Copyright (c) 2026 - Datatailr Inc.
#  All Rights Reserved.
#
#  This file is part of Datatailr and subject to the terms and conditions
#  defined in 'LICENSE.txt'. Unauthorized copying and/or distribution
#  of this file, in parts or full, via any medium is strictly prohibited.
##########################################################################
import os

import streamlit as st
import requests


def main():
    st.title("Streamlit + Data Service Integration Demo")

    if os.getenv("DATATAILR_JOB_TYPE") == "workspace":
        data_service_url = "http://localhost:1024"
    else:
        data_service_url = "http://simple-service-<>USERNAME<>"

    # Health check
    health_status = "Unknown"
    try:
        resp = requests.get(f"{data_service_url}/__health_check__.html", timeout=2)
        if resp.status_code == 200 and resp.text.strip() == "OK":
            health_status = "Healthy"
        else:
            health_status = f"Unhealthy: {resp.text.strip()}"
    except Exception as e:
        health_status = f"Error: {e}"
    st.info(f"Data Service Health: {health_status}")

    # Greeting functionality
    name = st.text_input("Enter your name:")
    if name:
        try:
            r = requests.get(
                f"{data_service_url}/greet", params={"name": name}, timeout=2
            )
            if r.status_code == 200:
                greeting = r.json().get("greeting", "")
                st.success(greeting)
            else:
                st.error("Data service error on /greet.")
        except Exception as e:
            st.error(f"Could not connect to Data service: {e}")

    # Random number functionality
    st.subheader("Get a Random Number from Data Service")
    col1, col2 = st.columns(2)
    with col1:
        min_val = st.number_input("Min value", value=0)
    with col2:
        max_val = st.number_input("Max value", value=100)
    if st.button("Get Random Number"):
        try:
            r = requests.get(
                f"{data_service_url}/random",
                params={"min": int(min_val), "max": int(max_val)},
                timeout=2,
            )
            if r.status_code == 200:
                rand_num = r.json().get("random_number", None)
                st.write(f"Random number: {rand_num}")
            else:
                st.error("Data service error on /random.")
        except Exception as e:
            st.error(f"Could not connect to Data service: {e}")


if __name__ == "__main__":
    main()
