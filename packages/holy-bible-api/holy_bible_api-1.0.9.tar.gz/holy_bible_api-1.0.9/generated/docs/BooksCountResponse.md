# BooksCountResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**num_books** | **int** |  | 

## Example

```python
from openapi_client.models.books_count_response import BooksCountResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BooksCountResponse from a JSON string
books_count_response_instance = BooksCountResponse.from_json(json)
# print the JSON string representation of the object
print(BooksCountResponse.to_json())

# convert the object into a dict
books_count_response_dict = books_count_response_instance.to_dict()
# create an instance of BooksCountResponse from a dict
books_count_response_from_dict = BooksCountResponse.from_dict(books_count_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


