from __future__ import print_function

import email
import zipfile
import os
import gzip
import string
import boto3
import urllib

print('Loading function')

s3 = boto3.client('s3')
s3r = boto3.resource('s3')
xmlDir = "/tmp/output/"

outputBucket = "ab-document-search-4e393250"  # Set here for a seperate bucket otherwise it is set to the events bucket
outputPrefix = "mail/"  # Should end with /

def validate_prefix(prefix):
    return prefix.endswith('jpeg') or prefix.endswith('jpg') or prefix.endswith('png') or prefix.endswith('pdf')

def get_attachment_index(payload):
    global index
    index = 0
    for text in payload:
        print("anexo: ", index)
        print("content type: " + text.get_content_type())
        print("prefixo válido: ", validate_prefix(text.get_content_type()))
    
        if validate_prefix(text.get_content_type()):
            break
        index = index + 1

    if index > (len(payload) - 1): 
        raise Exception("invalid file format")
    return index


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

    try:
        outputBucket = bucket
        response = s3r.Bucket(bucket).Object(key)
        msg = email.message_from_bytes(response.get()["Body"].read())
        
        get_attachment_index(msg.get_payload())
            
        if len(msg.get_payload()) > 1:
            # Create directory for XML files (makes debugging easier)
            if os.path.isdir(xmlDir) == False:
                os.mkdir(xmlDir)

            attachment = msg.get_payload()[index]
            extract_attachment(attachment)
            upload_resulting_files_to_s3()
        else:
            print("Could not see file/attachment.")
        return 0
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist '
            'and your bucket is in the same region as this '
            'function.'.format(key, bucket))
        raise e
    delete_file(key, bucket)
    

def extract_attachment(attachment):
    print("getting attachment")
    # Process filename.zip attachments
    if "gzip" in attachment.get_content_type():
        contentdisp = string.split(attachment.get('Content-Disposition'), '=')
        fname = contentdisp[1].replace('\"', '')
        open('/tmp/' + contentdisp[1], 'wb').write(attachment.get_payload(decode=True))
        # This assumes we have filename.xml.gz, if we get this wrong, we will just
        # ignore the report
        xmlname = fname[:-3]
        open(xmlDir + xmlname, 'wb').write(gzip.open('/tmp/' + contentdisp[1], 'rb').read())

    # Process filename.xml.gz attachments (Providers not complying to standards)
    elif "zip" in attachment.get_content_type():
        print("eh zip memo!")
        open('/tmp/attachment.zip', 'wb').write(attachment.get_payload(decode=True))
        with zipfile.ZipFile('/tmp/attachment.zip', "r") as z:
            z.extractall(xmlDir)

    else:
        contentdisp = attachment.get('Content-Disposition')
        print("content disp: " + contentdisp)
        strarray = contentdisp.split("=")
        fname = strarray[1].replace('\"', '')
        fname = fname.replace('; size', '')
        open(xmlDir + fname, 'wb').write(attachment.get_payload(decode=True))
        print('wrote to s3 xml path')


def upload_resulting_files_to_s3():
    # Put all XML back into S3 (Covers non-compliant cases if a ZIP contains multiple results)
    for fileName in os.listdir(xmlDir):
        if not fileName.endswith("MACOSX"):
            print("Uploading: " + fileName)  # File name to upload
            print("bucket: " + outputBucket)
            s3r.meta.client.upload_file(xmlDir+'/'+fileName, outputBucket, outputPrefix+fileName)

# Delete the file in the current bucket
def delete_file(key, bucket):
    s3.delete_object(Bucket=bucket, Key=key)
    print("%s deleted fom %s ") % (key, bucket)