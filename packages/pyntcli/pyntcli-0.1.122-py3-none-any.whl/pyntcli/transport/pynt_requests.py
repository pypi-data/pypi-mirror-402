import requests
import urllib3
import os
import pem
import certifi
import tempfile

from pyntcli.ui import ui_thread


class HostCaException(Exception):
    pass


class InvalidPathException(HostCaException):
    pass


class InvalidCertFormat(HostCaException):
    pass


verify = True

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def disable_tls_termination():
    global verify
    verify = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def add_host_ca(ca_path):
    global verify
    if not os.path.isfile(ca_path):
        raise InvalidPathException("{} - No such file".format(ca_path))
    if not pem.parse_file(ca_path):
        raise InvalidCertFormat("{} - Invalid Format".format(ca_path))

    cert_data = open(ca_path, "rb").read()

    cafile = certifi.where()
    ca_chain = open(cafile, "rb").read()

    bundle_path = os.path.join(tempfile.gettempdir(), "bundle.pem")
    with open(bundle_path, "wb") as f:
        f.write(ca_chain)
        f.write(b"\n")
        f.write(cert_data)

    verify = bundle_path


def get(url, params=None, **kwargs):
    return requests.get(url, params=params, verify=verify, **kwargs)


def post(url, data=None, json=None, **kwargs):
    return requests.post(url, data=data, json=json, verify=verify, **kwargs)


def put(url, data=None, **kwargs):
    return requests.put(url, data=data, verify=verify, **kwargs)


def request_from_xml(method, url, proxies=None, data=None, **kwargs):
    try:
        requests.request(
            method=method, url=url, data=data, verify=False, proxies=proxies, **kwargs
        )

        return url
    except requests.exceptions.TooManyRedirects as e:
        return "Too many redirects for {}".format(url)
    except Exception as e:
        ui_thread.print_verbose(f"Failed to send request to {url} - {e}")
        raise e
