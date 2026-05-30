"""
Week10 - AWS Lambda 핸들러
서버리스 배포 + /health 엔드포인트
"""
import json


def handler(event, context):
    path = event.get("rawPath", "/")

    if path == "/health":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "healthy",
                "service": "visa-navigator",
                "version": "1.0.0"
            })
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "Global Campus Visa Navigator API",
            "version": "1.0.0",
            "endpoints": ["/health"]
        })
    }
