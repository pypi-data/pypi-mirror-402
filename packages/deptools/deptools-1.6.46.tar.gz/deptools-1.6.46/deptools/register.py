# -*- coding: utf-8 -*-
'''AlazarTech Package Registration Script

Usage:
  register [--dev] [--dry-run] [--email-notif] [-p <passfile>] <endpoint> <specfile> <base_url> <version>
  register -h | --help
  register --version

Options:
  -h --help      Show this screen
  -p <passfile>  If a password should be registered with the website, you can
                 give the file containing the password here.
  --dev          Register packages specified with the development website,
                 instead of the release version.
  --dry-run      Performs a practice run of the operation, without actually
                 sending an HTTP request to the website.
  --email-notif  Send an email notification to <marketing@alazartech.com> after 
                 succesfull package registration.

Arguments:
  <endpoint>      Enpoint where to send request payload.
  <specfile>      Path to the YAML deployment specification file to use for
                  this deployment. See deploy.py for more information about the
                  file's format.
  <base_url>      Azure blob storage container path where the files are hosted.
  <version>       The version of the application to release

'''

import os

import smtplib

import json
from collections import namedtuple
from re import search

from azure.storage.blob import BlobClient, ContainerClient, generate_blob_sas, BlobSasPermissions
import datetime
import time
import hashlib

from docopt import docopt
import requests

from .spec import get_specs_from_file, get_things, getenv
from glob import glob

# The nomenclature in this module can be confusing. Here is a breakdown of all
# important concepts:
#
# - Product: An item that can be sold or distributed for free by AlazarTech.
#   For example, ATS-SDK is a product. Each product has:
#
#   * a product key: a string of characters that is used in the filename of the
#    installation packages for products to identify them
#
#   * a product ID: a number used by the website to uniquely identify each
#     product.
#
# - Package: The installation software for a product on a specific OS. The .exe
#   package to install ATS-SDK on Windows is a package. In the code, we refer to
#   `PackageId` to mean the combination of a product key and an OS. This should
#   not be confused with product IDs.

PRODUCTS = {
    # Key: ID
    "Alazar-Package-Manager": '733',
    "ATS-GPU-BASE": '1034',
    "ATS-GPU-OCT": '1035',
    "ATS-GPU-NUFFT": '1040',
    "AlazarDSO": '1017',
    "ATS-SDK": '1018',
    "ATS310": '13',
    "ATS330": '12',
    "ATS460": '11',
    "ATS660": '1025',
    "ATS850": '15',
    "ATS860": '14',
    "ATS9120": '1028',
    "ATS9130": '1030',
    "ATS9146": '1039',
    "ATS9182": '3007',
    "ATS9350": '4',
    "ATS9351": '5',
    "ATS9352": '1036',
    "ATS9353": '1041',
    "ATS9360": '2',
    "ATS9364": '3004',
    "ATS9371": '1027',
    "ATS9373": '1',
    "ATS9376": '3006',
    "ATS9380": '3005',
    "ATS9416": '1016',
    "ATS9428": '3008',
    "ATS9437": '3002',
    "ATS9440": '9',
    "ATS9442": '1048',
    "ATS9453": '1037',
    "ATS9462": '8',
    "ATS9470": '1043',
    "ATS9473": '3003',
    "ATS9625": '6',
    "ATS9626": '7',
    "ATS9628": '1047',
    "ATS9870": '3',
    "ATS9872": '1042',
    "ATST872": '3012',
    #"ATST371": '1044',
    "ATST352": '1045',
    "ATST146": '1046',
    "ATST364": '3009',
    "ATS9637": '1031',
    "ATS9362": '3011',
    # Negative product IDs are for products that we want to send to the website 
    # but are to be associated with other products. For instance, some packages 
    # are to be sent to Linux drivers resources.
    "libats": '-1',
    "Alazar-Front-Panel": '-2',
    "fwupdater-cli": '-3',
    "fwupdater-gui": '-4',
    "atssync": '-5',
    "fwupdater": "8002", #keep it after fwupdater-cli and fwupdater-gui
}

ATSSYNC_PRODUCTS = {
    # Key: ID
    "ATS9120": '6228',
    "ATS9130": '6227',
    "ATS9146": '6226',
    #"ATS9182": '',
    "ATS9350": '6225',
    "ATS9351": '6224',
    "ATS9352": '6223',
    "ATS9353": '6222',
    "ATS9360": '6221',
    "ATS9364": '6220',
    "ATS9371": '6219',
    "ATS9373": '6218',
    "ATS9416": '6217',
    "ATS9428": '6216',
    "ATS9437": '6215',
    "ATS9440": '6214',
    #"ATS9442": '',
    "ATS9462": '6213',
    #"ATS9470": '',
    #"ATS9473": '',
    "ATS9625": '6212',
    "ATS9626": '6211',
    "ATS9628": '6210',
    "ATS9870": '6208',
    "ATS9872": '6207',
    "ATST872": '6243',
    #"ATST371": '1044',
    "ATST352": '6205',
    "ATST146": '6206',
    "ATST364": '6204',
    "ATS9637": '6209',
    "ATS9362": '6234',
}

# Identifies a package that can be registered to the website
PackageId = namedtuple(
    'PackageId',
    [
        'key',  # type: str
        'os',  # type: str
        'arch',  # type: str
    ])


def get_os(filename):
    filename = filename.lower()
    if filename.endswith('.exe'):
        return 'Windows'
    if filename.endswith('.deb'):
        return 'Linux (.deb)'
    if filename.endswith('.rpm'):
        return 'Linux (.rpm)'
    if 'windows' in filename:
        return 'Windows'
    if 'debian' in filename:
        return 'Linux (.deb)'
    if 'deb' in filename:
        return 'Linux (.deb)'
    if 'centos' in filename:
        return 'Linux (.rpm)'
    if 'rpm' in filename:
        return 'Linux (.rpm)'
    raise ValueError("Could not determine OS for file {}".format(filename))

def get_arch(filename):
    filename = filename.lower()
    if 'arm64' in filename:
        return 'arm64'
    if 'aarch64' in filename:
        return 'arm64'
    else:
        return 'x86_64'

def is_driver(key):
    driver_infix = tuple('0123456789T')
    for c in driver_infix:
        if key.startswith("ATS"+c):
            return True
    return False

def get_name(packageid):
    if is_driver(packageid.key):
        if packageid.os == 'Windows':
            name =  packageid.key + " " + packageid.arch + " driver for Windows"
        elif packageid.os == 'Linux (.deb)' or packageid.os == 'Linux (.rpm)':
            name =  packageid.key + " " + packageid.arch + " driver for Linux"
        name = name.replace("ATST", "ATS9")
        return name
    if packageid.key == 'libats':
        return "Libats library [REQUIRED]"
    if packageid.key == 'fwupdater-cli':
        return "Firmware Update Utility (CLI)"
    if packageid.key == 'fwupdater-gui':
        return "Firmware Update Utility (GUI)"
    if packageid.key == 'fwupdater':
        return "Firmware Update Utility for Windows"
    if packageid.key == 'atssync':
        return "ATS Sync Application & Driver"
    if packageid.key == 'Alazar-Package-Manager':
        return "Alazar Package Manager for Windows"
    if packageid.key in ['ATS-GPU-BASE', 'ATS-GPU-OCT', 'ATS-GPU-NUFFT', 'ATS-SDK']:
        name = packageid.key + " Installation Program for " + packageid.os
        if ((packageid.os == 'Linux (.deb)' or packageid.os == 'Linux (.rpm)')):
            if (packageid.arch == 'arm64'):
                name = name + " ARM64"
            elif (packageid.arch == 'x86_64'):
                name = name + " x86_64"
            else:
                raise ValueError("Invalid architecture.")
        return name
    return packageid.key

def get_french_name(packageid):
    if is_driver(packageid.key):
        if packageid.os == 'Windows':
            name =  "Pilotes " + packageid.key + " " + packageid.arch + " pour Windows"
        elif packageid.os == 'Linux (.deb)' or packageid.os == 'Linux (.rpm)':
            name =  "Pilotes " + packageid.key + " " + packageid.arch + " pour Linux"
        name = name.replace("ATST", "ATS9")
        return name
    if packageid.key == 'libats':
        return "Librairie libats [REQUISE]"
    if packageid.key == 'fwupdater-cli':
        return "Utilitaire pour mise a jour du micrologiciel (CLI)"
    if packageid.key == 'fwupdater-gui':
        return "Utilitaire pour mise a jour du micrologiciel (GUI)"
    if packageid.key == 'fwupdater':
        return "Utilitaire Windows pour mise a jour du micrologiciel"
    if packageid.key == 'atssync':
        return "Application et pilote ATS Sync"
    if packageid.key == 'Alazar-Package-Manager':
        return "Gestionnaire de packets Alazar pour Windows"
    if packageid.key in ['ATS-GPU-BASE', 'ATS-GPU-OCT', 'ATS-GPU-NUFFT', 'ATS-SDK']:
        name = packageid.key + " Programme d'installation pour " + packageid.os
        if ((packageid.os == 'Linux (.deb)' or packageid.os == 'Linux (.rpm)')):
            if (packageid.arch == 'arm64'):
                name = name + " ARM64"
            elif (packageid.arch == 'x86_64'):
                name = name + " x86_64"
            else:
                raise ValueError("Invalid architecture.")
        return name
    return packageid.key

def get_md5_content(filename):
    path = glob('**/' + filename, recursive=True)
    if (len(path) == 1):
        file = open(path[0],'rb')
        md5_content = str(bytearray(hashlib.md5(file.read()).digest()))
        file.close()
    elif (len(path) == 0):
        raise ValueError("No such file or directory: " + filename)
    else:
        raise ValueError("Multiple files with same name: " + filename)
    return md5_content

def major_minor_patch(version):
    major, minor, patch = search('(\d+)\.(\d+)\.(\d+)', version).groups()
    return int(major), int(minor), int(patch)

def get_latest_apm_url():
    # Get url of latest Alazar Package Manager (APM)
    url = "https://alazarblob1.blob.core.windows.net/packages"
    container_client = ContainerClient.from_container_url(url)
    blob_list = container_client.list_blob_names(
        name_starts_with="alazar-package-manager")
    latest_apm = max(blob_list, key=major_minor_patch)
    return url + "/" + latest_apm


def get_latest_lkg_url(os, arch):
    # Get url of latest License Key Generator (LKG)
    if (os == 'Linux (.deb)'):
        url = "https://alazarblob1.blob.core.windows.net/packages-deb"
        if (arch == 'arm64'):
            arch_name = arch
        elif (arch == 'x86_64'):
            arch_name = 'amd64'
        else:
            raise ValueError("Could not find latest LKG due to invalid architecture.")
    elif (os == 'Linux (.rpm)'):
        url = "https://alazarblob1.blob.core.windows.net/packages-rpm"
        if (arch == 'arm64'):
            arch_name = 'aarch64'
        elif (arch == 'x86_64'):
            arch_name = arch
        else:
            raise ValueError("Could not find latest LKG due to invalid architecture.")
    else:
        raise ValueError("Could not find latest LKG due to invalid OS.")
    
    container_client = ContainerClient.from_container_url(url)
    blob_list = container_client.list_blob_names(
        name_starts_with="ats-license")
    list = []
    for name in blob_list:
        if (arch_name in name):
            list += [name]
    latest_lkg = max(list, key=major_minor_patch)
    
    return url + "/" + latest_lkg


def get_category(key):
    if is_driver(key):
        return 'driver'
    elif key == "libats":
        return 'driver'
    elif key == "fwupdater-cli" or \
         key == "fwupdater-gui" or \
         key == "fwupdater":
        return 'utilities'
    else:
        return 'software'

def get_product_key(filename):
    for key in PRODUCTS:
        if key.lower() in filename.lower():
            return key
    raise ValueError("Could not identify product for file {}".format(filename))

def get_thunderbolt_equivalent(drv_key):
    if is_driver(drv_key):
        tb_key = drv_key.replace(drv_key[0:4], "ATST", 1)
        for key in PRODUCTS:
            if key == tb_key:
                return tb_key
    return ''

def create_service_sas_blob(base_url: str, blob_name: str):
    # Create a SAS token that is valid for a period of time
    start_time = datetime.datetime.now(datetime.timezone.utc)
    expiry_time = start_time + datetime.timedelta(days=30000)
    account_name = "alazarblob1"
    account_key = os.getenv('AZURE_ACCOUNT_KEY')
    count = 0
    max_count = 15
    while (count < max_count):
        try:
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=os.path.basename(os.path.normpath(base_url)),
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=expiry_time,
                start=start_time
            )
            url = f"{base_url + blob_name}?{sas_token}"
            # Check if url works correctly
            blob = BlobClient.from_blob_url(url) 
            if (blob.get_blob_properties().etag):
                break
        except:
            count += 1
            time.sleep(30)
            pass
    if (count==max_count):
        raise ValueError("Could not generate valid SAS token for blob: '{}'.".format(blob_name))
    return url

# The file and optional release notes associated with a package
Package = namedtuple(
    'Package',
    [
        'os',  # type: str
        'product_id',  # type: str
        'installer',  # type: str
        'readme',  # type: str
        'name',  # type: str
        'arch',  # type: str
        'category',  # type: str
        'name_french',  # type: str
    ])


def packages_from_files(files):
    installers = {}  # type: Dict[PackageId, PackageContents]
    readmes = {}  # type: Dict[str, PackageContents]
    for filename in files:
        key = get_product_key(filename)
        if filename.endswith('.html'):
            # This is a release notes file
            if key in readmes:
                raise ValueError(
                    "Multiple release notes files for package {} found".format(
                        key))
            filename = os.path.normpath(filename)
            readmes[key] = filename.split(os.sep)[-1]
        else:
            # This is an installer
            packageid = PackageId(key, get_os(filename), get_arch(filename))
            if packageid in installers:
                raise ValueError(
                    "Multiple installers files for package ID {} found.".
                    format(packageid))
            filename = os.path.normpath(filename)
            installers[packageid] = filename.split(os.sep)[-1]
    packages = []  # type: List[Package]
    for packageid in installers:
        packages.append(
            Package(os=packageid.os,
                    product_id=PRODUCTS[packageid.key],
                    installer=installers[packageid],
                    readme=readmes[packageid.key],
                    name=get_name(packageid),
                    arch=packageid.arch,
                    category=get_category(packageid.key),
                    name_french=get_french_name(packageid)))

        tb_key = get_thunderbolt_equivalent(packageid.key)
        if tb_key != '':
            tb_packageid = PackageId(tb_key, packageid.os, packageid.arch)
            packages.append(
                Package(os=tb_packageid.os,
                        product_id=PRODUCTS[tb_packageid.key],
                        installer=installers[packageid],
                        readme=readmes[packageid.key],
                        name=get_name(tb_packageid),
                        arch=tb_packageid.arch,
                        category=get_category(tb_packageid.key),
                        name_french=get_french_name(tb_packageid)))

    return packages

# Packages to be sent to Linux drivers resources.
def is_linux_resource(package):
    if package.os != 'Linux (.deb)' and package.os != 'Linux (.rpm)':
        return False
    if package.name == 'Libats library [REQUIRED]' or \
       package.name == 'Alazar-Front-Panel' or \
       package.name == 'Firmware Update Utility (CLI)' or \
       package.name == 'Firmware Update Utility (GUI)':
        return True
    return False

def is_accessory(package):
    if package.name == 'ATS Sync Application & Driver':
        return True
    return False

def payload_from_packages(packages, base_url, version, password):
    if not base_url.endswith('/'):
        base_url = base_url + '/'
    if password is None:
        password = ""
    payload = []
    for package in packages:
        if ('ats-gpu-base' in package.installer or 'ats-gpu-oct' in package.installer
            or 'ats-gpu-nufft' in package.installer or 'ats-sdk' in package.installer):
            licensed_product = True 
            notes_url = create_service_sas_blob(base_url, package.readme)
        else:
            licensed_product = False     

        if is_linux_resource(package):
            for key in PRODUCTS:
                if is_driver(key):
                    payload.append({
                        "os": package.os,
                        "product_id": PRODUCTS[key],
                        "url": base_url + package.installer,
                        "release_notes_url": base_url + package.readme,
                        "version": version,
                        "password": password,
                        "name": package.name,
                        "arch": package.arch,
                        "category": package.category,
                        "name_french": package.name_french,
                        "id": get_md5_content(package.installer) + "_" + PRODUCTS[key],
                    })
        if is_accessory(package):
            for key in ATSSYNC_PRODUCTS:
                payload.append({
                    "os": package.os,
                    "product_id": ATSSYNC_PRODUCTS[key],
                    "url": base_url + package.installer,
                    "release_notes_url": base_url + package.readme,
                    "version": version,
                    "password": password,
                    "name": package.name,
                    "arch": package.arch,
                    "category": package.category,
                    "name_french": package.name_french,
                    "id": get_md5_content(package.installer) + "_" + ATSSYNC_PRODUCTS[key],
                })            
        if not package.product_id.startswith('-'):
            if (licensed_product):
                if (package.os == 'Linux (.deb)' or package.os == 'Linux (.rpm)'):
                    payload.append({
                        "os": package.os,
                        "product_id": package.product_id,
                        "url": get_latest_lkg_url(package.os, package.arch),
                        "release_notes_url": notes_url,
                        "version": version,
                        "password": "",
                        "name": package.name,
                        "arch": package.arch,
                        "category": package.category,
                        "name_french": package.name_french,
                        "id": get_md5_content(package.installer) + "_" + package.product_id,
                    })
                else:
                    payload.append({
                        "os": package.os,
                        "product_id": package.product_id,
                        "url": get_latest_apm_url(),
                        "release_notes_url": notes_url,
                        "version": version,
                        "password": "",
                        "name": package.name,
                        "arch": package.arch,
                        "category": package.category,
                        "name_french": package.name_french,
                        "id": get_md5_content(package.installer) + "_" + package.product_id,
                    })
            else: 
                payload.append({
                    "os": package.os,
                    "product_id": package.product_id,
                    "url": base_url + package.installer,
                    "release_notes_url": base_url + package.readme,
                    "version": version,
                    "password": password,
                    "name": package.name,
                    "arch": package.arch,
                    "category": package.category,
                    "name_french": package.name_french,
                    "id": get_md5_content(package.installer) + "_" + package.product_id,
                })
    return json.dumps(payload)

def send_email_notif(url_endpoint):
    server = smtplib.SMTP('smtp.videotron.ca')
    
    message = """\
    Subject: New product release
    From: GitLab <gitlab@gitlab.alazartech.com>
    To: Marketing <marketing@alazartech.com>

    Hi there! 

    A new product sent to """ + url_endpoint + """ is now ready for release."""

    server.sendmail("gitlab@gitlab.alazartech.com", "marketing@alazartech.com", message)
    server.quit()


def register(endpoint, development, passfile, specsfile, baseurl, version, dry_run, email_notif):
    specs = get_specs_from_file(specsfile)
    files = [thing for spec in specs for thing in get_things(spec)]
    packages = packages_from_files(files)
    if development:
        url_endpoint = "https://test.alazartech.com/go/to/the/dci/" + endpoint + "/"
    else:
        url_endpoint = "https://www.alazartech.com/go/to/the/dci/" + endpoint + "/"
    password = None
    if passfile:
        with open(passfile, 'r') as passf:
            password = passf.readline().strip()
    payload = payload_from_packages(packages, baseurl, version, password)
    print("The POST request parameters:")
    print("- endpoint: {}".format(url_endpoint))
    print("- data: {}".format(payload))
    if dry_run:
        print("Dry run, stopping here.")
        return
    res = requests.post(url_endpoint,
                        params={"key": getenv("WEBSITE_API_KEY")},
                        data=payload)
    if res.status_code != 200:
        raise ValueError("Registration request returned status code {}".format(
            res.status_code))
    if email_notif:
        send_email_notif(url_endpoint)


def main():
    '''Main function'''
    arguments = docopt(__doc__, version='Deloy Utility')
    register(endpoint=arguments['<endpoint>'],
             development=arguments['--dev'],
             passfile=arguments['-p'],
             specsfile=arguments['<specfile>'],
             baseurl=arguments['<base_url>'],
             version=arguments['<version>'],
             dry_run=arguments['--dry-run'],
             email_notif=arguments['--email-notif'])

if __name__ == "__main__":
    main()
