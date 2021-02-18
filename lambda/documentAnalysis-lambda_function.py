import json
from text_extractor import TextExtractor
from document_analyzer import DocumentAnalyzer
from document_indexer import DocumentIndexer

document_indexer = DocumentIndexer()
document_analyzer = DocumentAnalyzer()
text_extractor = TextExtractor()


def handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])

    jobId = message['JobId']
    print("JobId="+jobId)

    status = message['Status']
    print("Status="+status)

    if status != "SUCCEEDED":
        return {
            # TODO : handle error with Dead letter queue (not in this workshop)
            # https://docs.aws.amazon.com/lambda/latest/dg/dlq.html
            "status": status
        }

    pages = text_extractor.extract_text(jobId)
    print(list(pages.values()))

    entities = document_analyzer.extract_entities(list(pages.values()))
    print(entities)

    doc = {
        "bucket": message['DocumentLocation']['S3Bucket'],
        "document": message['DocumentLocation']['S3ObjectName'],
        "size": len(list(pages.values())),
        "jobId": jobId,
        "pages": list(pages.values()),
        "entities": entities
    }

    print(doc)

    docId = document_indexer.index(doc)

    return {
        "jobId": jobId,
        "docId": docId
    }