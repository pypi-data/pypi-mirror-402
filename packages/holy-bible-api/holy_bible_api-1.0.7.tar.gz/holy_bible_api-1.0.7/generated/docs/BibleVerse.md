# BibleVerse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bible_id** | **int** |  | 
**book** | **int** |  | 
**chapter** | **int** |  | 
**text** | **str** |  | 
**verse** | **int** |  | 

## Example

```python
from openapi_client.models.bible_verse import BibleVerse

# TODO update the JSON string below
json = "{}"
# create an instance of BibleVerse from a JSON string
bible_verse_instance = BibleVerse.from_json(json)
# print the JSON string representation of the object
print(BibleVerse.to_json())

# convert the object into a dict
bible_verse_dict = bible_verse_instance.to_dict()
# create an instance of BibleVerse from a dict
bible_verse_from_dict = BibleVerse.from_dict(bible_verse_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


