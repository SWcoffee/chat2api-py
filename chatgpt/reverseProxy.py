import copy
import json
import random
import warnings

from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse, Response
from starlette.background import BackgroundTask

from utils.Client import Client
from utils.config import chatgpt_base_url_list, proxy_url_list, enable_gateway
from curl_cffi.requests.errors import RequestsError
from utils.Logger import logger
from utils.title import gen_title

headers_reject_list = [
    "x-real-ip",
    "x-forwarded-for",
    "x-forwarded-proto",
    "x-forwarded-port",
    "x-forwarded-host",
    "x-forwarded-server",
    "cf-warp-tag-id",
    "cf-visitor",
    "cf-ray",
    "cf-connecting-ip",
    "cf-ipcountry",
    "cdn-loop",
    "remote-host",
    "x-frame-options",
    "x-xss-protection",
    "x-content-type-options",
    "content-security-policy",
    "host",
    "cookie",
    "connection",
    "content-length",
    "content-encoding",
    "x-middleware-prefetch",
    "x-nextjs-data",
    "purpose",
    "x-forwarded-uri",
    "x-forwarded-path",
    "x-forwarded-method",
    "x-forwarded-protocol",
    "x-forwarded-scheme",
    "cf-request-id",
    "cf-worker",
    "cf-access-client-id",
    "cf-access-client-device-type",
    "cf-access-client-device-model",
    "cf-access-client-device-name",
    "cf-access-client-device-brand",
    "x-middleware-prefetch",
    "x-forwarded-for",
    "x-forwarded-host",
    "x-forwarded-proto",
    "x-forwarded-server",
    "x-real-ip",
    "x-forwarded-port",
    "cf-connecting-ip",
    "cf-ipcountry",
    "cf-ray",
    "cf-visitor",
]

async def log_aiter_content(r, chunk_size=None, decode_unicode=False):
    """
    iterate streaming content chunk by chunk in bytes.
    """
    if chunk_size:
        warnings.warn("chunk_size is ignored, there is no way to tell curl that.")
    if decode_unicode:
        raise NotImplementedError()

    assert r.queue and r.curl, "stream mode is not enabled."

    while True:
        chunk = await r.queue.get()

        # re-raise the exception if something wrong happened.
        if isinstance(chunk, RequestsError):
            await r.aclose()
            raise chunk

        # end of stream.
        if chunk is None:
            await r.aclose()
            return
        # save title
        new_chunk = copy.deepcopy(chunk)
        if "title_generation" in new_chunk:
            data = json.loads(new_chunk)
            conversation_id = data["data"]["conversation_id"]
            title = data["data"]["title"]
            gen_title[conversation_id] = title
            logger.info("conversation_id:"+conversation_id)
            logger.info("title:"+title)
        # logger.info("chunk:"+new_chunk.decode("utf-8"))
        yield chunk


async def chatgpt_reverse_proxy(request: Request, path: str):
    if not enable_gateway:
        raise HTTPException(status_code=404, detail="Gateway is disabled")
    try:
        if "gen_title" in path:
            
            conversion_id =path.split("/")[-1]
            logger.info("gen_title:"+conversion_id)
            if conversion_id in gen_title.keys():
                data = {
                    "title":gen_title.get(conversion_id),
                    "conversation_id":conversion_id
                }
                return Response(content=json.dumps(data), media_type="application/json",
                                status_code=200, background=None)
            else :
                return Response(content=json.dumps({"title":"user request"}), media_type="application/json",
                                status_code=200, background=None)
            
        origin_host = request.url.netloc
        if ":" in origin_host:
            petrol = "http"
        else:
            petrol = "https"
        if path.startswith("v1/"):
            base_url = "https://ab.chatgpt.com"
        else:
            base_url = random.choice(chatgpt_base_url_list) if chatgpt_base_url_list else "https://chatgpt.com"
        params = dict(request.query_params)
        headers = {
            key: value for key, value in request.headers.items()
            if (key.lower() not in ["host", "origin", "referer", "user-agent",
                                    "authorization"] and key.lower() not in headers_reject_list)
        }
        request_cookies = dict(request.cookies)

        headers.update({
            "accept-Language": "en-US,en;q=0.9",
            "host": base_url.replace("https://", "").replace("http://", ""),
            "origin": base_url,
            "referer": f"{base_url}/",
            "sec-ch-ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
        })

        if request.headers.get('Authorization'):
            headers['Authorization'] = request.headers['Authorization']

        if headers.get("Content-Type") == "application/json":
            data = await request.json()
        else:
            data = await request.body()

        client = Client(proxy=random.choice(proxy_url_list) if proxy_url_list else None)
        try:
            background = BackgroundTask(client.close)
            r = await client.request(request.method, f"{base_url}/{path}", params=params, headers=headers,
                                     cookies=request_cookies, data=data, stream=True, allow_redirects=False)
            if r.status_code == 304:
                return Response(status_code=304, background=background)
            elif r.status_code == 307:
                if "oai-dm=1" not in r.headers.get("Location"):
                    return Response(status_code=307, headers={
                        "Location": r.headers.get("Location").replace("chat.openai.com", origin_host)
                                    .replace("chatgpt.com", origin_host)
                                    .replace("https", petrol) + "?oai-dm=1"}, background=background)
                else:
                    return Response(status_code=307, headers={"Location": r.headers.get("Location")},
                                    background=background)
            elif r.status_code == 302:
                return Response(status_code=302,
                                headers={"Location": r.headers.get("Location").replace("chatgpt.com", origin_host)
                                .replace("chat.openai.com", origin_host)
                                .replace("ab.chatgpt.com", origin_host)
                                .replace("cdn.oaistatic.com", origin_host)
                                .replace("https", petrol)}, background=background)
            elif 'stream' in r.headers.get("content-type", ""):
                return StreamingResponse(log_aiter_content(r), media_type=r.headers.get("content-type", ""),
                                         background=background)
                # return StreamingResponse(r.aiter_content(), media_type=r.headers.get("content-type", ""),
                #                          background=background)
            else:
                if "/conversation" in path or "/register-websocket" in path:
                    logger.info(f"atext: {r.atext()}")
                    response = Response(content=(await r.atext()), media_type=r.headers.get("content-type"),
                                        status_code=r.status_code, background=background)
                else:
                    content = ((await r.atext()).replace("chatgpt.com", origin_host)
                               .replace("chat.openai.com", origin_host)
                               .replace("ab.chatgpt.com", origin_host)
                               .replace("cdn.oaistatic.com", origin_host)
                               .replace("https", petrol))
                    response = Response(content=content, media_type=r.headers.get("content-type"),
                                        status_code=r.status_code, background=background)
                for cookie_name in r.cookies:
                    if cookie_name in request_cookies:
                        continue
                    for cookie_domain in [".chatgpt.com"]:
                        cookie_value = r.cookies.get(name=cookie_name, domain=cookie_domain)
                        if cookie_name.startswith("__"):
                            response.set_cookie(key=cookie_name, value=cookie_value, secure=True, httponly=True)
                        else:
                            response.set_cookie(key=cookie_name, value=cookie_value)
                return response
        except Exception:
            await client.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
