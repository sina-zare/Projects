import os
from dotenv import load_dotenv
from ecsclient.client import Client
from prometheus_client import make_wsgi_app, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response, HTTPException

app = FastAPI(debug=True)

@app.get("/metrics")
async def get_metrics():
    get_ecs_namespaces_info()
    metrics = generate_latest()
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)


#################### CONFIGURATION ####################
load_dotenv()
client = Client('4',
                username=os.getenv('ECS_USERNAME'),
                password=os.getenv('ECS_PASSWORD'),
                token_endpoint=os.getenv('ECS_API_ENDPOINT') + '/login',
                ecs_endpoint=os.getenv('ECS_API_ENDPOINT'),
                cache_token=False)

#################### METRICS ####################
NAMESPACE_COUNT = Gauge('ecs_namespace_count', 'Number of namespaces')
NAMESPACE_QUOTA = Gauge('ecs_namespace_quota', 'Quota of namespace', ['namespace'])
NAMESPACE_USED = Gauge('ecs_namespace_used', 'Used of namespace', ['namespace', 'unit'])
NAMESPACE_TOTLA_OBJECTS = Gauge('ecs_namespace_total_objects', 'Total objects in namespace', ['namespace'])
# NAMESPACE_TOTAL_OBJECTS_DELETED = Gauge('namespace_total_objects_deleted', 'Total objects deleted in namespace', ['namespace'])
# NAMESPACE_TOTAL_OBJECTS_DELETED_SIZE = Gauge('namespace_total_objects_deleted_size', 'Total size of objects deleted in namespace', ['namespace', 'unit'])

BUCKET_COUNT = Gauge('ecs_namespace_bucket_count', 'Number of buckets in namespace', ['namespace'])
BUCKET_NAME = Gauge('ecs_namespace_bucket', 'Bucket name', ['namespace', 'bucket'])
BUCKET_USED = Gauge('ecs_namespace_bucket_used', 'Used of bucket', ['namespace', 'bucket', 'unit'])
BUCKET_TOTAL_OBJECTS = Gauge('ecs_namespace_bucket_total_objects', 'Total objects in bucket', ['namespace', 'bucket'])
# BUCKET_TOTAL_OBJECTS_DELETED = Gauge('ecs_namespace_bucket_total_objects_deleted', 'Total objects deleted in bucket', ['namespace', 'bucket'])
# BUCKET_TOTAL_OBJECTS_DELETED_SIZE = Gauge('ecs_namespace_bucket_total_objects_deleted_size', 'Total size of objects deleted in bucket', ['namespace', 'bucket', 'unit'])

#################### AGGREGATE DATA ####################
def get_namespaces():
    return client.namespace.list()['namespace']

def get_ecs_namespaces_info():
    namespaces = get_namespaces()
    NAMESPACE_COUNT.set(len(namespaces))

    ids = []
    for n in namespaces:
        ids.append(n['id'])

    namespaces_info = client.billing.get_namespaces_billing_info(ids)['namespace_billing_infos']
    for ni in namespaces_info:
        namespace_name = ni['namespace']
        namespace_quota = client.namespace.get_namespace_quota(namespace_name)['blockSize']
        NAMESPACE_QUOTA.labels(namespace=namespace_name).set(namespace_quota)
        NAMESPACE_USED.labels(namespace=namespace_name, unit=ni['total_size_unit']).set(ni['total_size'])
        NAMESPACE_TOTLA_OBJECTS.labels(namespace=namespace_name).set(ni['total_objects'])
        # NAMESPACE_TOTAL_OBJECTS_DELETED.labels(namespace=namespace_name).set(ni['total_objects_deleted'])
        # NAMESPACE_TOTAL_OBJECTS_DELETED_SIZE.labels(namespace=namespace_name, unit=ni['total_size_unit']).set(ni['total_size_deleted'])
        for b in ni['bucket_billing_info']:
            bucket_name = b['name']
            BUCKET_COUNT.labels(namespace=namespace_name).set(len(b))
            BUCKET_NAME.labels(namespace=namespace_name, bucket=bucket_name).set(1)
            BUCKET_USED.labels(namespace=namespace_name, bucket=bucket_name, unit=b['total_size_unit']).set(b['total_size'])
            BUCKET_TOTAL_OBJECTS.labels(namespace=namespace_name, bucket=bucket_name).set(b['total_objects'])
            # BUCKET_TOTAL_OBJECTS_DELETED.labels(namespace=namespace_name, bucket=bucket_name).set(b['total_objects_deleted'])
            # BUCKET_TOTAL_OBJECTS_DELETED_SIZE.labels(namespace=namespace_name, bucket=bucket_name, unit=b['total_size_unit']).set(b['total_size_deleted'])


#################### Handler AND MIDDLEWARE ####################
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Check for a token in the query parameters
    token = request.query_params.get('token')
    if not token or token != os.getenv('ACCESS_TOKEN'):
        raise HTTPException(status_code=401, detail="Unauthorized")

    response = await call_next(request)
    return response

#################### MAIN ####################
if __name__ == '__main__':
    print("Starting ECS metrics server...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
