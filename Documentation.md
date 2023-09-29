# API Documentation

To test the API, you can use the following cURL commands. You can also use Postman or any other API testing tool.

------------------------------------------------------------------------------------------

## Upload File

<details>
 <summary><code>POST</code> <code><b>/</b></code><code>api</code><code>(Upload File)</code></summary>

 ### Request Body

> | Name | Type | Description | Required |
> | ---- | ---- | ----------- | -------- |
> | `file` | `file` | The file to be uploaded | Yes |
> |Bucket_name|`string`|The name of the bucket to upload the file to|Yes|

### Response 

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json`                | `{"message": "File uploaded successfully"}`                         |
> | `400`         | `application/json`                | `{"message": "File not uploaded"}`                                  |
> | `500`         | `application/json`                | `{"message": "Internal Server Error"}`                              |
>


### Example Request

>```javascript
> curl -X POST \
>   http://localhost:8000/api \
>   -H 'Content-Type: multipart/form-data' \
>   -F file=@/path/to/file \
>   -F Bucket_name=Bucket_name
>```

>```python
> import requests
>
> url = "http://localhost:8000/api"
>
> payload = {}
> files = [
>   ('file', open('/path/to/file','rb'))
> ]
> headers= {}
>
> response = requests.request("POST", url, headers=headers, data = payload, files = files)
>
> print(response.text.encode('utf8'))
>```

</details>

------------------------------------------------------------------------------------------

## Get File

<details>
 <summary><code>GET</code> <code><b>/</b></code><code>api</code><code>(Get File)</code></summary>

 ### Request Body

> | Name | Type | Description | Required |
> | ---- | ---- | ----------- | -------- |
> | `file_name` | `string` | The name of the file to be retrieved | Yes |
> |Bucket_name|`string`|The name of the bucket to retrieve the file from|Yes|

### Response

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json`                | `{"message": "File retrieved successfully"}`                        |
> | `400`         | `application/json`                | `{"message": "File not retrieved"}`                                 |
> | `500`         | `application/json`                | `{"message": "Internal Server Error"}`                              |
>
>

### Example Request

>```javascript
> curl -X GET \
>   'http://localhost:8000/api?file_name=file_name&Bucket_name=Bucket_name' \
>   -H 'Content-Type: application/json' \
>   -H 'cache-control: no-cache'
>```

>```python
> import requests
>
> url = "http://localhost:8000/api"
>
> payload = {}
> headers= {}
>
> response = requests.request("GET", url, headers=headers, data = payload)
>
> print(response.text.encode('utf8'))
>```

</details>

------------------------------------------------------------------------------------------

## Get All Files

<details>
 <summary><code>GET</code> <code><b>/</b></code><code>api</code><code>(Get All Files)</code></summary>

 ### Request Body

> | Name | Type | Description | Required |
> | ---- | ---- | ----------- | -------- |
> |Bucket_name|`string`|The name of the bucket to retrieve the files from|Yes|

### Response

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json`                | `{"message": "Files retrieved successfully"}`                       |
> | `400`         | `application/json`                | `{"message": "Files not retrieved"}`                                |
> | `500`         | `application/json`                | `{"message": "Internal Server Error"}`                              |
>

### Example Request

>```javascript
> curl -X GET \
>   'http://localhost:8000/api?Bucket_name=Bucket_name' \
>   -H 'Content-Type: application/json' \
>   -H 'cache-control: no-cache'
>```

>```python
> import requests
>
> url = "http://localhost:8000/api"
>
> payload = {}
> headers= {}
>
> response = requests.request("GET", url, headers=headers, data = payload)
>
> print(response.text.encode('utf8'))
>```

</details>

------------------------------------------------------------------------------------------

## Delete File

<details>
 <summary><code>DELETE</code> <code><b>/</b></code><code>api</code><code>(Delete File)</code></summary>

 ### Request Body

> | Name | Type | Description | Required |
> | ---- | ---- | ----------- | -------- |
> | `file_name` | `string` | The name of the file to be deleted | Yes |
> |Bucket_name|`string`|The name of the bucket to delete the file from|Yes|

### Response

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json`                | `{"message": "File deleted successfully"}`                          |
> | `400`         | `application/json`                | `{"message": "File not deleted"}`                                   |
> | `500`         | `application/json`                | `{"message": "Internal Server Error"}`                              |
>

### Example Request

>```javascript
> curl -X DELETE \
>   'http://localhost:8000/api?file_name=file_name&Bucket_name=Bucket_name' \
>   -H 'Content-Type: application/json' \
>   -H 'cache-control: no-cache'
>```

>```python
> import requests
>
> url = "http://localhost:8000/api"
>
> payload = {}
> headers= {}
>
> response = requests.request("DELETE", url, headers=headers, data = payload)
>
> print(response.text.encode('utf8'))
>```

</details>

------------------------------------------------------------------------------------------