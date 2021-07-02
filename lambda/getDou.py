from datetime import date
from botocore.vendored import requests
from botocore.exceptions import ClientError
import botocore
import boto3
import os
import string
import urllib

outputBucket = "ab-document-search-4e393250"  # Set here for a seperate bucket otherwise it is set to the events bucket
outputPrefix = "dou/"  # Should end with /

s3 = boto3.client('s3')
s3r = boto3.resource('s3')

login = "xxxx@gmail.com"
senha = "xxxxx"
## Tipos de Diários Oficiais da União permitidos: do1 do2 do3 (Contempla as edições extras) ##
tipo_dou="do1 do2 do3"

url_login = "https://inlabs.in.gov.br/logar.php"
url_download = "https://inlabs.in.gov.br/index.php?p="

payload = {"email" : login, "password" : senha}
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
s = requests.Session()
response = s.request("POST", url_login, data=payload, headers=headers, verify=False)

if s.cookies.get('inlabs_session_cookie'):
    cookie = s.cookies.get('inlabs_session_cookie')
else:
    print("Falha ao obter cookie. Verifique suas credenciais");
    exit(37)

# Montagem da URL:
#ano = date.today().strftime("%Y")
#mes = date.today().strftime("%m")
#dia = date.today().strftime("%d")
ano = ("2021")
mes = ("02")
dia = ("17")

data_completa = ano + "-" + mes + "-" + dia

def upload_file(file_name, bucket, object_name):
    """Upload a file to an S3 bucket
    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    # s3_client = boto3.client('s3')
    try:
        response = s3.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def lambda_handler(event, context):
    print("Event :", event)

    #Download inicial
    for dou_secao in tipo_dou.split(' '):
        print("Aguarde Download...")
        url_arquivo = url_download + data_completa + "&dl=" + ano + "_" + mes + "_" + dia + "_ASSINADO_" + dou_secao + ".pdf"
        print(url_arquivo)
        cabecalho_arquivo = {'Cookie': 'inlabs_session_cookie=' + cookie, 'origem': '736372697074'}
        response_arquivo = s.request("GET", url_arquivo, headers = cabecalho_arquivo)
        
        if response_arquivo.status_code == 200:
            outputfname = outputPrefix + data_completa + "-" + dou_secao + ".pdf"
            fname = "/tmp/" + data_completa + "-" + dou_secao + ".pdf"
            with open("/tmp/" + data_completa + "-" + dou_secao + ".pdf", "wb") as f:
        	    f.write(response_arquivo.content)
        	    print(f)
        	    print("Arquivo %s salvo." % (ano + "_" + mes + "_" + dia + "_ASSINADO_" + dou_secao + ".pdf"))
        	    upload_file(fname, outputBucket, outputfname)
        	    del response_arquivo
        	    del f
        	    
        elif response_arquivo.status_code == 404:
    		    print("Arquivo não encontrado: %s" % (ano + "_" + mes + "_" + dia + "_ASSINADO_" + dou_secao + ".pdf"))

print("Aplicação encerrada")
