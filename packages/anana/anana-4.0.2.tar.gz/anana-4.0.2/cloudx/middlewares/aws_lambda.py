import os
import asyncio
import base64
from ..utils.logger import logger
from typing import Dict, List, Any, Callable, Union, Tuple
from urllib.parse import urlencode
from ..asgi import ASGICore
from ..asgi import Response
from ..common import SingletonMeta
from ..utils.asyncify import asyncify
from ..asgi import Router

class AWSMiddleware(metaclass=SingletonMeta):
    """
    Middleware to adapt AWS events to ASGI applications.
    """

    def __init__(self, core: ASGICore) -> None:
        """
        Initialize the AWSMiddleware with an ASGI app.

        Parameters:
            asgi_app (ASGIApp): The ASGI application to adapt.
        """
        self.app = core
        self.base_scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "body": b"", "method": "POST", "scheme": "https", "path": "/", "query_string": urlencode(b""), 
            "server": ("0.0.0.0", "443"), "client": ("0.0.0.0", 0), "is_base64_encoded": False, 
            "headers": {"Content-Type": "application/json", "accept": "*/*", "accept-encoding": "gzip, deflate, br", "Connection": "keep-alive"},
            "messageId": "", "extra": {}, "metadata": {"source": "", "event": None}
        }
        
    def __call__(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handles incoming AWS Lambda events and generates responses.

        Parameters:
            event (Dict[str, Any]): The event data sent to the Lambda function.
            context (Any): The Lambda context object.

        Returns:
            Dict[str, Any]: The response to be returned by the Lambda function.
        """
        logger.debug(f"Received event: {event} and context: {context}")
        try:
            scopes = self._build_scopes(event, context)
        except Exception as ex:
            logger.exception(f"An error occurred. ex = {ex}\nevent={event}\ncontext={context}", exc_info=True)
            raise ex

        batch_responses = []
        tasks = []

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for scope in scopes:
            _, _, extra = Router().match(scope["path"].rstrip("/"), scope["method"])
            scope["extra"] = extra

            if isinstance(scope["body"],bool):
                body = scope["body"]
            else:
                body = base64.b64decode(scope["body"]) if scope["is_base64_encoded"] and scope["body"] else scope["body"] if scope["body"] else b""
            encoded_headers = [(k.lower().encode(), v.encode()) for k, v in scope["headers"].items()]
            scope.update({
                "body": body.encode() if isinstance(body, str) else body,
                "headers": encoded_headers,
                "raw_path": scope["path"].encode("utf-8"),
                "query_string": scope["query_string"].encode("utf-8")
            })
            scope["metadata"].update({"context": context})

            try:
                if extra.get("parallel", "False") == "False":
                    response = loop.run_until_complete(self._process_scope(scope))
                    batch_responses.append(response)
                else:
                    task = loop.create_task(self._process_scope(scope))
                    tasks.append(task)
            except Exception as ex:
                raise ex                  
        try:
            if len(tasks) > 0:
                batch_responses = loop.run_until_complete(asyncio.gather(*tasks))
        except Exception as ex:
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise ex        
        finally:
            loop.close()
                
        return self._build_response(batch_responses)
                
    async def _process_scope(self, scope: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Handles an individual ASGI request.

        Parameters:
            scope (Dict[str, Any]): The ASGI scope containing the request data.

        Returns:
            Tuple[str, Dict[str, Any]]: The event source and the response.
        """
        response = {"status": None, "headers": None, "body": b""}
        app_receive = asyncify(lambda: {"type": "http.request", "body": scope.get("body", b""), "more_body": False})
        async def app_send(message: Dict[str, Any]):
            try:
                if message["type"] == "http.response.start":
                    response.update({"status": message["status"], "headers": {k.decode(): v.decode() for k, v in message["headers"]}})
                elif message["type"] == "http.response.body":
                    response.update({"body": response["body"] + message["body"]})
            except Exception as ex:
                pass
        try:
            await self.app(scope, app_receive, app_send)
            response["body"] = response["body"].decode() if isinstance(response["body"], bytes) else response["body"]
            if scope["method"] == "HEAD": # Enforce stripping the body for HEAD requests and Ensure body is empty
                response["body"] = ""
        except UnicodeDecodeError as ex:
            pass
        except Exception as ex:
            response["status"] = 500
            response["body"] = Response.description(response["status"])
            response["headers"] = {}
        finally:
            event_source = response["headers"].get("source_trigger", scope["metadata"]["source"].split(":")[1])
            if response["status"] > 499 and event_source in ["sqs", "dynamodb", "s3", "sns"]:
                if scope["extra"].get("partial_batch_response_enabled", "False") == "False":
                    raise Exception(Response.description(response["status"]))
                else:
                    response["headers"]["partial_batch_response_enabled"] = True
            response["headers"]["messageId"] = scope["messageId"]
            
        response["headers"].update(scope["extra"]) 

        return event_source, {"statusCode": response["status"],
                "headers": response["headers"],
                "body": response["body"],
                "isBase64Encoded": False}       
            
    def _build_response(self, responses: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Generates a unified response for all processed scopes.

        Parameters:
            responses (List[Tuple[str, Dict[str, Any]]]): A list of responses from each scope.

        Returns:
            Dict[str, Any]: The final combined response.
        """
        event_source = responses[0][0]
        if event_source in ["apigateway", "function_url"]:
            response = responses[0][1].copy()
        elif event_source in ["lambda"]:
            response = responses[0][1].copy()
            if response["statusCode"] > 499:
                raise Exception(Response.description(response["statusCode"]))
        elif event_source in ["dynamodb", "s3", "sns", "sqs", "scheduled_event", "unsupported_event"]:
            response = {}
            response["statusCode"] = 700
            for single_response_touple in responses:
                single_response = single_response_touple[1]
                if single_response["statusCode"] < 400:
                    response["statusCode"] = single_response["statusCode"]
                    response["body"] = {}
                    if single_response["headers"].get("partial_batch_response_enabled", "False") == "True":
                        response.setdefault("batchItemFailures", [])
                elif single_response["statusCode"] > 499 and single_response["statusCode"] < 600:
                    if single_response["headers"].get("partial_batch_response_enabled", "False") == "False":
                        raise Exception(Response.description(single_response["statusCode"]))
                    else:
                        response.setdefault("batchItemFailures", []).append({"itemIdentifier": single_response["headers"]["messageId"]})
                        response["statusCode"] = 200
                        response["body"] = {}
                elif single_response["statusCode"] != 700:
                    if single_response["headers"].get("partial_batch_response_enabled", "False") == "False":
                        raise Exception(Response.description(single_response["statusCode"]))
                    else:
                        response.setdefault("batchItemFailures", []).append({"itemIdentifier": single_response["headers"]["messageId"]})
                        response["statusCode"] = 200
                        response["body"] = {}

        return response

    def _build_scopes(self, event: Dict[str, Any], context: Any) -> List[Dict[str, Any]]:
        """
        Builds ASGI scopes for the incoming AWS event.

        Parameters:
            event (Dict[str, Any]): The AWS event data.
            context (Any): The Lambda context object.

        Returns:
            List[Dict[str, Any]]: A list of ASGI scopes.
        """
        if isinstance(event, dict) and "Records" in event:
            return [self._build_scope(record, context) for record in event["Records"]]
        return [self._build_scope(event, context)]
    
    def _build_scope(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Builds a single ASGI scope for an AWS event record.

        Parameters:
            event (Dict[str, Any]): A single AWS event record.
            context (Any): The Lambda context object.

        Returns:
            Dict[str, Any]: An ASGI scope.
        """
        scope = self.base_scope.copy()
        source = "aws:lambda" if not isinstance(event, dict) else event.get("eventSource", None)
        if source is None:
            source = (f"aws:{'scheduled_event' if event.get('detail-type') == 'Scheduled Event' else 'unknown'}" if 'detail-type' in event else 
                'aws:lambda' if 'rawPath' not in event and 'path' not in event else '')

        if source == "aws:sqs":
            scope.update(self._sqs_scope(event, context))
        elif source == "aws:dynamodb":
            scope.update(self._dynamodb_scope(event, context))
        elif source == "aws:s3":
            scope.update(self._s3_scope(event, context))
        elif source == "aws:lambda":
            scope.update(self._lambda_scope(event, context))
        elif source == "aws:scheduled_event":
            scope.update(self._event_bridge_scope(event, context))
        else:
            source = "aws:function_url" if event.get("requestContext", {}).get("domainName", "").find("lambda-url") != -1 else "aws:apigateway"
            source = "aws:alb" if event.get("requestContext", {}).get("elb", None) is not None else source
            if source == "aws:apigateway" or source == "aws:function_url":
                scope.update(self._apigateway_scope(event, context))
            elif source == "aws:alb":
                scope.update(self._alb_scope(event, context))
            else:
                raise Exception("Unknown Event Type")
    
        scope["metadata"] = {"source": f"{source}", "event": event}
        return scope

    def _apigateway_scope(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Builds the ASGI scope for an API Gateway event.

        Parameters:
            event (Dict[str, Any]): The API Gateway event data.
            context (Any): The Lambda context object.

        Returns:
            Dict[str, Any]: The ASGI scope representing the API Gateway event.
        """
        if "path" in event:
            tmp_path = str(event["resource"]).replace("{proxy+}", event["pathParameters"].get("proxy", "")) if event["pathParameters"] else str(event["resource"])
            method = str(event["httpMethod"]).upper()
            client =  (event["requestContext"]["identity"]["sourceIp"], 0)
        elif "version" in event and "rawPath" in event:
            tmp_path = event["requestContext"]["http"]["path"]
            method = str(event["requestContext"]["http"]["method"]).upper()
            client =  (event["requestContext"]["http"]["sourceIp"], 0)
        else:
            raise Exception("Unknown Event Type")

        port = event["headers"].get("X-Forwarded-Port", 443)
        return {
            "path": tmp_path if tmp_path.startswith("/") else f"/{tmp_path}",
            "method": method,
            "body":event.get("body", None),
            "headers":event.get("headers", {}),
            "query_string": urlencode(b"" if event.get("queryStringParameters", b"") == None else event.get("queryStringParameters", b"")),
            "is_base64_encoded": event.get("isBase64Encoded", False),
            "server": (event["requestContext"]["domainName"], port),
            "client": client,
            "messageId": event.get("requestContext", {}).get("requestId", "") 
        }    
          
    def _alb_scope(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Builds the ASGI scope for an ALB event.

        Parameters:
            event (Dict[str, Any]): The ALB event record.
            context (Any): The Lambda context object.

        Returns:
            Dict[str, Any]: The ASGI scope representing the ALB event.
        """
        return {
            "body":event.get("body", None),
            "path": f'/alb/{event.get("requestContext", {}).get("domainName", "")}/', 
            "messageId": event.get("requestContext", {}).get("requestId", "") 
        }
    
    def _sqs_scope(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Builds the ASGI scope for an SQS event.

        Parameters:
            event (Dict[str, Any]): The SQS event record.
            context (Any): The Lambda context object.

        Returns:
            Dict[str, Any]: The ASGI scope representing the SQS event.
        """
        return {
            "body":event["body"],
            "path": f'/sqs/{str(event["eventSourceARN"].rsplit(":", 1)[1])}/', 
            "messageId": event.get("messageId", "")
        }
    
    def _dynamodb_scope(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Builds the ASGI scope for a DynamoDB stream event.

        Parameters:
            event (Dict[str, Any]): The DynamoDB stream event record.
            context (Any): The Lambda context object.

        Returns:
            Dict[str, Any]: The ASGI scope representing the DynamoDB event.
        """
        def from_ddb(attr):
            if isinstance(attr, dict):
                # Single-attribute wrappers
                if "S" in attr:
                    return attr["S"]
                if "N" in attr:
                    return attr["N"]
                if "BOOL" in attr:
                    return attr["BOOL"]
                if "NULL" in attr:
                    return None
                if "B" in attr:
                    return attr["B"]
                if "SS" in attr:
                    return list(attr["SS"])  # strings
                if "NS" in attr:
                    return list(attr["NS"])  # numbers as strings
                if "BS" in attr:
                    return list(attr["BS"])  # bytes
                if "L" in attr:
                    return [from_ddb(v) for v in attr["L"]]
                if "M" in attr:
                    return {k: from_ddb(v) for k, v in attr["M"].items()}
                # Plain map of attributes (e.g., Keys/OldImage/NewImage)
                return {k: from_ddb(v) for k, v in attr.items()}
            elif isinstance(attr, list):
                return [from_ddb(v) for v in attr]
            else:
                return attr

        table = str(event["eventSourceARN"].split(":")[5].split("/")[1])
        method = str(event["eventName"]).upper()
        ddb = event.get("dynamodb", {})
        body = {
            "table": table,
            "method": method,
            "id": event["eventID"],
            "type": ddb.get("StreamViewType", ""),
            "keys": from_ddb(ddb.get("Keys", {})),
            "old": from_ddb(ddb.get("OldImage", None)),
            "new": from_ddb(ddb.get("NewImage", None)),
        }
        return {
            "path": f"/dynamodb/{table}/",
            "method": method,
            "body": body,
            "messageId": event.get("messageId", "")
        }
        
    def _s3_scope(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Builds the ASGI scope for an S3 event.

        Parameters:
            event (Dict[str, Any]): The S3 event record.
            context (Any): The Lambda context object.

        Returns:
            Dict[str, Any]: The ASGI scope representing the S3 event.
        """
        bucket_name = event["s3"]["bucket"]["name"]
        event_type, event_action = str(event["eventName"]).split(":", 1) if ":" in str(event["eventName"]) else (str(event["eventName"]), None)
        return {
            "path": f"/s3/{bucket_name}/",
            "method": event_type.upper(),
            "body": {
                "time": event["eventTime"], 
                "bucket": bucket_name, 
                "type": event_type, 
                "action": event_action,
                "key": event["s3"]["object"]["key"], 
                "size": event["s3"]["object"]["size"],
                "eTag": event["s3"]["object"]["eTag"], 
                "sequencer": event["s3"]["object"]["sequencer"]},
            "messageId": event.get("messageId", "")
        }
        
    def _lambda_scope(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Builds the ASGI scope for a direct Lambda invocation event.

        Parameters:
            event (Dict[str, Any]): The Lambda event payload.
            context (Any): The Lambda context object.

        Returns:
            Dict[str, Any]: The ASGI scope representing the Lambda invocation.
        """
        return {
            "body":event,
            "path": f'/lambda/{os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "AWS_LAMBDA_FUNCTION_NAME")}/', 
        }
    
    def _event_bridge_scope(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Builds the ASGI scope for an EventBridge (scheduled event) event.

        Parameters:
            event (Dict[str, Any]): The EventBridge event payload.
            context (Any): The Lambda context object.

        Returns:
            Dict[str, Any]: The ASGI scope representing the EventBridge event.
        """
        return {
            "body":event.get("detail", None),
            "path": f'/lambda/{os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "AWS_LAMBDA_FUNCTION_NAME")}/', 
        }
    
    def _route(self, path: str, methods: Union[str, List[str]], handler: Callable, **kwargs) -> Callable:
        """
        Registers a route in the ASGI app for the given path and handler.

        Parameters:
            path (str): The path for the route.
            handler (Callable): The handler function for the route.
            **kwargs: Additional route configuration.

        Returns:
            Callable: The handler function.
        """
        self.app.route(path=path, methods=methods, callback=handler, **kwargs)
        return handler
    
    def on_sqs(self, names: Union[str, List[str]], batch: bool = False, parallel: bool = False) -> Callable:
        """
        Register a handler for SQS messages.

        Parameters:
            - `names` (Union[str, List[str]]): Queue name(s). Supports wildcards (e.g., "my-queue-*").
            - `batch` (bool): When True, enables partial batch responses (failed records are reported in `batchItemFailures`).
            - `parallel` (bool): When True, process multiple records concurrently.

        Payload:
            - `request.source`: "aws:sqs".
            - `request.path`: `/sqs/{queue}/`.
            - `request.method`: `POST`.
            - `request.body`: Raw SQS message body as bytes.
            - `request.text`: UTF-8 string if the body is plain text; otherwise `None`.
            - `request.json`: Parsed JSON if the body is valid JSON; otherwise `None`.
            - `request.attributes`: SQS `messageAttributes` dict from the record.
            - `request.metadata`: The full SQS record under `event` and the Lambda `context` under `context`.
        """
        return lambda handler: [self._route(path=f"/sqs/{q}/", methods="POST", handler=handler, partial_batch_response_enabled=str(batch), 
                                        parallel=str(parallel)) for q in ([names] if isinstance(names, str) else names)][-1]

    def on_sns(self, names: Union[str, List[str]], parallel: bool = False) -> Callable:
        """Register a handler for SNS topics. (Not implemented in this version.)"""
        raise NotImplementedError("SNS is not supported in this version.")

    def on_s3(self, buckets: Union[str, List[str]], events: Union[str, List[str]] = None, parallel: bool = False) -> Callable:
        """
        Handle S3 object events.

        Parameters:
            - `buckets` (Union[str, List[str]]): S3 bucket name(s). Supports wildcards (e.g., "my-bucket-*").
            - `events` (Union[str, List[str], None]): S3 operation(s) (e.g., "ObjectCreated", "ObjectRemoved").
              If None or empty, a default set is enabled.
            - `parallel` (bool): When True, process multiple records concurrently.

        Payload:
            - `request.source`: "aws:s3".
            - `request.path`: `/s3/{bucket}/`.
            - `request.method`: One of the S3 ops: ObjectCreated, ObjectRemoved, ObjectRestore, ReducedRedundancyLostObject, Replication, LifecycleExpiration, LifecycleTransition, IntelligentTiering, ObjectTagging, ObjectAcl.
            - `request.json`: { time: str, bucket: str, type: str, action: Optional[str], key: str, size: int, eTag: str, sequencer: str }.
            - `request.metadata`: The full S3 record under `event` and the Lambda `context` under `context`.
        """
        if events is None or events == []:
            events = ["ObjectCreated", "ObjectRemoved", "ObjectRestore", "ReducedRedundancyLostObject", "Replication",
                       "LifecycleExpiration", "LifecycleTransition", "IntelligentTiering", "ObjectTagging", "ObjectAcl"]
        return lambda handler: [self._route(path=f"/s3/{b}/", methods=events, handler=handler, parallel=str(parallel))
                        for b in ([buckets] if isinstance(buckets, str) else buckets)][-1]

    def on_dynamoDB_stream(self, tables: Union[str, List[str]], events: Union[str, List[str]] = None, parallel: bool = False) -> Callable:
        """
        Register a handler for DynamoDB stream events.

        Parameters:
            - `tables` (Union[str, List[str]]): Table name(s). Supports wildcards.
            - `events` (Union[str, List[str], None]): "INSERT", "MODIFY", or "REMOVE". If None/empty, all.
            - `parallel` (bool): When True, process multiple records concurrently.

        Payload (flattened):
            - `request.source`: "aws:dynamodb".
            - `request.path`: `/dynamodb/{table}/`.
            - `request.method`: INSERT | MODIFY | REMOVE.
            - `request.json`: { table: str, method: str, id: str, type: str, keys: dict, old: Optional[dict], new: Optional[dict] } where
              DynamoDB attribute values are converted to plain Python types (e.g., {"S": "v"} → "v", {"N": "123"} → "123", {"BOOL": true} → True).
            - `request.metadata`: The full stream record under `event` and the Lambda `context` under `context`.
        """
        if events is None or events == []:
            events = ["INSERT", "MODIFY", "REMOVE"]
        return lambda handler: [self._route(
            f"/dynamodb/{t}/", methods=events, 
            handler=handler, 
            parallel=str(parallel)
            ) for t in ([tables] if isinstance(tables, str) else tables)][-1]

    def on_lambda_trigger(self) -> Callable:
        """
        Register a handler for direct Lambda invocation events.

        Payload:
            - `request.source`: "aws:lambda".
            - `request.path`: `/lambda/{AWS_LAMBDA_FUNCTION_NAME}/`.
            - `request.method`: `POST`.
            - `request.json`: The invocation event if JSON; otherwise None.
            - `request.body`: Raw invocation payload as bytes.
            - `request.metadata`: Full event under `event` and Lambda `context` under `context`.
        """
        return lambda handler: self._route(
            path=f'/lambda/{os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "AWS_LAMBDA_FUNCTION_NAME")}/', 
            methods='POST', 
            handler=handler,
            )

    def on_scheduler(self) -> Callable:
        """
        Register a handler for scheduled EventBridge events.

        Payload:
            - `request.source`: "aws:scheduled_event".
            - `request.path`: `/lambda/{AWS_LAMBDA_FUNCTION_NAME}/`.
            - `request.method`: `POST`.
            - `request.json`: The EventBridge `detail` dict (or None).
            - `request.metadata`: Full EventBridge event under `event` and Lambda `context` under `context`.
        """
        return lambda handler: self._route(
            path=f'/lambda/{os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "AWS_LAMBDA_FUNCTION_NAME")}/', 
            methods='POST', 
            handler=handler,
            trigger='aws:scheduled_event',
            )
