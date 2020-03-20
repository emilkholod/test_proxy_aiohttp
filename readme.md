Simple proxy app, that return text from thie host site.

Run app with:
python -m proxy_app --host HOST_NAME

Also you can read help by using "--help" key.

You can send request:

curl -X GET "http://127.0.0.1:5000/get" -H  "accept: application/json"

and you will see some answer. Next time, if you send this request again in 10 minutes, you will see this answer again, but this answer will be from redis cache.