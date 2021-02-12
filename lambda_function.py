import boto3

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
client = boto3.client('rekognition')

collection_id = 'Collection'

def add_to_dynamo(faceId, name):
    table = dynamodb.Table('faces')
    table.put_item(TableName="faces", Item={'face_id': faceId, 'name': name})


def lambda_handler(event, context):
    # portions of this borrowed from AWS Recognition Developer's Guide documentation

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    response = s3.head_object(Bucket=bucket, Key=key)
    name = response['ResponseMetadata']['HTTPHeaders']['x-amz-meta-name']

    print('bucket = {}'.format(bucket))
    print('file = {}'.format(key))
    print('name = {}'.format(name))

    #obj = s3.get_object(Bucket=bucket, Key=key)

	# identify the faces & add them to the collection
    response = client.index_faces(CollectionId=collection_id,
                                Image={'S3Object': {'Bucket': bucket, 'Name': key}},
                                ExternalImageId = key,
                                MaxFaces = 1,
                                QualityFilter = "AUTO",
                                DetectionAttributes = ['ALL'])

    print('Results for ' + key)

    faceID = ''
	
    # we're making a bold assumption that only one face is present in the photo
    for faceRecord in response['FaceRecords']:
        print('Face ID =  {}'.format(faceRecord['Face']['FaceId']))
        faceID = faceRecord['Face']['FaceId']

    print('Faces not indexed:')
    for unindexedFace in response['UnindexedFaces']:
        print('  Location: {}'.format(unindexedFace['FaceDetail']['BoundingBox']))
        print('  Reasons:')
        for reason in unindexedFace['Reasons']:
            print('    ' + reason)

    print("Faces indexed count: " + str(len(response['FaceRecords'])))

    # put the face ID into the DynamoDB table
    add_to_dynamo(faceID, name)
