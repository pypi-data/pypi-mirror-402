# -*- coding: utf-8 -*-
'''AlazarTech Windows Driver Signature

Usage:
  windrvsign <cab_file> <output_zip>
  windrvsign -h | --help
  windrvsign --version

Arguments:
  <cab_file>      CAB file to be sent for signing.
  <output_zip>    Path and name of the output zip file for signed drivers.

'''

import os
import time
from datetime import datetime

import requests
from azure.storage.blob import BlobClient
from docopt import docopt

start = time.time()


def secs_since_start():
    return int(time.time() - start)


def try_getenv(key):
    '''Tries to get an environment variable, raises an exception if it fails'''
    env = os.getenv(key)
    if env is None:
        raise ValueError(f"{key} environment variable is missing")
    return env


def get_access_token():
    body = "grant_type=client_credentials" +\
        "&client_id="+try_getenv('AZURE_AD_APPLICATION_CLIENT_ID') +\
        "&client_secret="+try_getenv('AZURE_AD_APPLICATION_CLIENT_SECRET') +\
        "&resource=https://manage.devcenter.microsoft.com"

    req = requests.post("https://login.microsoftonline.com/" +
                        try_getenv('AZURE_AD_APPLICATION_TENANT_ID') +
                        "/oauth2/token",
                        data=body)

    if req.status_code != 200:
        raise Exception("Unable to get access token")

    access_token = req.json()['access_token']

    return access_token


def create_new_product(access_token):
    date_time = datetime.today().strftime("%Y-%m-%d" + "T" + "%H:%M:%S")

    body = {
        "productName":
        "Driver signature - " + date_time,
        "testHarness":
        "Attestation",
        "announcementDate":
        date_time,
        "deviceMetadataIds": [],
        "deviceType":
        "internal",
        "isTestSign":
        False,
        "isFlightSign":
        False,
        "marketingNames": [],
        "requestedSignatures": [
            "WINDOWS_v100_TH2_FULL", "WINDOWS_v100_X64_TH2_FULL",
            "WINDOWS_v100_RS1_FULL", "WINDOWS_v100_X64_RS1_FULL",
            "WINDOWS_v100_RS2_FULL", "WINDOWS_v100_X64_RS2_FULL",
            "WINDOWS_v100_RS3_FULL", "WINDOWS_v100_X64_RS3_FULL",
            "WINDOWS_v100_RS4_FULL", "WINDOWS_v100_X64_RS4_FULL",
            "WINDOWS_v100_RS5_FULL", "WINDOWS_v100_X64_RS5_FULL",
            "WINDOWS_v100_19H1_FULL", "WINDOWS_v100_X64_19H1_FULL",
            "WINDOWS_v100_X64_CO_FULL"
        ],
        "additionalAttributes": {}
    }

    req = requests.post(
        "https://manage.devcenter.microsoft.com/v2.0/my/hardware/products/",
        headers={"Authorization": "Bearer " + access_token},
        json=body)

    if req.status_code != 201:
        raise Exception("Unable to create new product")

    product_id = str(req.json()['id'])

    return product_id


def create_new_submission(access_token, product_id):

    date_time = datetime.today().strftime("%Y-%m-%d" + "T" + "%H:%M:%S")

    body = {"name": "Drivers signature - " + date_time, "type": "initial"}

    req = requests.post(
        "https://manage.devcenter.microsoft.com/v2.0/my/hardware/products/" +
        product_id + "/submissions",
        headers={"Authorization": "Bearer " + access_token},
        json=body)

    if req.status_code != 201:
        raise Exception("Unable to create new submission")

    submission_id = str(req.json()['id'])

    for item in req.json()['downloads']['items']:
        if item['type'] == "initialPackage":
            sas_url = item['url']
            return submission_id, sas_url

    raise Exception("Unable to retreive the shared access signature (SAS) URI")


def upload_package(sas_url, cab_file):

    blob = BlobClient.from_blob_url(sas_url)

    with open(cab_file, "rb") as data:
        blob.upload_blob(data)


def download_package(signed_package, zip_file):

    blob = BlobClient.from_blob_url(signed_package)

    with open(zip_file, "wb") as my_blob:
        blob_data = blob.download_blob()
        blob_data.readinto(my_blob)


def commit_submission(access_token, product_id, submission_id):

    req = requests.post(
        "https://manage.devcenter.microsoft.com/v2.0/my/hardware/products/" +
        product_id + "/submissions/" + submission_id + "/commit",
        headers={"Authorization": "Bearer " + access_token})

    if req.status_code != 202:
        raise Exception("Unable to commit product submission")


class SubmissionStatus():
    '''Parses the output of the submission status query API'''

    def __init__(self, json):
        workflow = json['workflowStatus']
        self.current_step = workflow['currentStep']
        self.state = workflow['state']
        self.messages = workflow.get('messages', '')
        if self.is_complete():
            dls = json['downloads']
            for item in dls['items']:
                if item['type'] == "signedPackage":
                    self.url = item['url']
                    return
            raise Exception(
                f"Unable to find signed package. Downloads are {dls}")

    def is_complete(self) -> bool:
        return (self.current_step == 'finalizeIngestion'
                and self.state == 'completed')

    def is_failed(self) -> bool:
        return self.state == 'failed'

    def failure_messages(self) -> bool:
        return self.messages

    def signed_url(self) -> str:
        return self.url


def get_submission_status(access_token, product_id, submission_id):
    req = requests.get(
        "https://manage.devcenter.microsoft.com/v2.0/my/hardware/products/" +
        product_id + "/submissions/" + submission_id,
        headers={"Authorization": "Bearer " + access_token})
    if req.status_code != 200:
        raise Exception("Unable to check submission status")
    return SubmissionStatus(req.json())


def windows_driver_sign(cabfile, outputzip):
    if not os.path.exists(cabfile):
        raise ValueError(f"{cabfile} doesn't exist")

    _, ext = os.path.splitext(outputzip)
    if ext != '.zip':
        raise ValueError(f"{outputzip} doesn't have the zip extension")

    outputdir = os.path.dirname(outputzip)
    if not os.path.exists(outputdir):
        raise ValueError("{outputdir} is not a valid path")

    print(f"[{secs_since_start(): 4}s] Getting access token")
    access_token = get_access_token()
    print(f"[{secs_since_start(): 4}s] Creating product")
    product_id = create_new_product(access_token)
    print(f"[{secs_since_start(): 4}s] Creating submission")
    submission_id, sas_url = create_new_submission(access_token, product_id)
    print(f"[{secs_since_start(): 4}s] Uploading package")
    upload_package(sas_url, cabfile)
    print(f"[{secs_since_start(): 4}s] Committing submission")
    commit_submission(access_token, product_id, submission_id)
    while True:
        status = get_submission_status(access_token, product_id, submission_id)
        if status.is_failed():
            raise ValueError(
                f"Submission {submission_id} for product {product_id} failed "
                + f"during step {status.current_step}." +
                str(status.failure_messages()))
        if status.is_complete():
            print(f"[{secs_since_start(): 4}s] Submission complete")
            download_package(status.signed_url(), outputzip)
            break
        print(f"[{secs_since_start(): 4}s] Current step: " +
              f"{status.current_step} - {status.state}")
        time.sleep(10)


def main():
    '''Main function'''
    arguments = docopt(__doc__, version='Windows Driver Signature Utility')
    windows_driver_sign(cabfile=arguments['<cab_file>'],
                        outputzip=arguments['<output_zip>'])


if __name__ == "__main__":
    main()
