import subprocess
import logging
import time

dh_api_url = "https://api.dreamhost.com/?key="
api_key = "API-KEY-GOES-HERE"
fqdn = "FQDN-GOES-HERE"

logging.basicConfig(
    filename='ddns.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',  # basic format
)

# Monkey-patch to force UTC (simple trick)
logging.Formatter.converter = time.gmtime

# Get current public IP address of host.
public_ipv4 = subprocess.check_output(
    ['dig', '-4', '+short', 'myip.opendns.com', '@resolver1.opendns.com'],
    text=True
).strip()

get_dns = (dh_api_url + api_key + "&cmd=dns-list_records")

# GET DNS record for fqdn.
result = subprocess.run(
    ["curl", get_dns],
    capture_output=True,          # capture stdout & stderr
    text=True,                    # return strings instead of bytes
    check=True                    # raise exception if curl fails
)

# Convert the result into a string.
output_text = result.stdout

# Isolate the IP for fqdn
current_dns = None

for line in output_text.splitlines():
    parts = line.split()
    if len(parts) >= 5 and parts[2] == fqdn and parts[3] == "A":
        current_dns = parts[4]
        break

# Now use current_dns
if current_dns:
    logging.info(f"IP is: {current_dns}")
else:
    logging.info("DNS A record not found. Adding " + public_ipv4 + " as A record for " + fqdn + ".")
    add_dns = (dh_api_url + api_key + "&cmd=dns-add_record&record=" + fqdn + "&type=A&value=" + public_ipv4)
    addDNS = subprocess.run(
        ["curl", add_dns],
        capture_output=True,          # capture stdout & stderr
        text=True,                    # return strings instead of bytes
        check=True                    # raise exception if curl fails
    )

    logging.info(addDNS.stdout)              # the response body
    logging.info(addDNS.returncode)          # 0 = success
    raise SystemExit(0)

if(public_ipv4 == current_dns):
    logging.info("Public IP (" + public_ipv4 + ") and A record for " + fqdn + " (" + current_dns + ") match. Nothing to do.")
    exit
elif current_dns == None:
    logging.info("No current DNS A record.")
    exit
else:       # Update the A record if Public IP and DNS A record doesn't match.
    # Delete current record.
    logging.info("Deleting DNS Record", current_dns)
    del_dns = (dh_api_url + api_key + "&cmd=dns-remove_record&record=" + fqdn + "&type=A&value=" + current_dns)

    push0 = subprocess.run(
        ["curl", del_dns],
        capture_output=True,          # capture stdout & stderr
        text=True,                    # return strings instead of bytes
        check=True                    # raise exception if curl fails
    )

    logging.info(push0.stdout)              # the response body
    logging.info(push0.returncode)          # 0 = success


    # Add new record
    logging.info("Adding DNS Record", public_ipv4)
    update_dns = (dh_api_url + api_key + "&cmd=dns-add_record&record=" + fqdn + "&type=A&value=" + public_ipv4)

    # Update DNS record for fqdn

    push1 = subprocess.run(
        ["curl", update_dns],
        capture_output=True,          # capture stdout & stderr
        text=True,                    # return strings instead of bytes
        check=True                    # raise exception if curl fails
    )

    logging.info(push1.stdout)              # the response body
    logging.info(push1.returncode)          # 0 = success