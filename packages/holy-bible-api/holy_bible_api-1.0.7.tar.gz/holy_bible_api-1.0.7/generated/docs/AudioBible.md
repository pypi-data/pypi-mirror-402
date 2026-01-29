# AudioBible


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**audio_bible_id** | **int** |  | 
**language** | **str** |  | 
**version** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.audio_bible import AudioBible

# TODO update the JSON string below
json = "{}"
# create an instance of AudioBible from a JSON string
audio_bible_instance = AudioBible.from_json(json)
# print the JSON string representation of the object
print(AudioBible.to_json())

# convert the object into a dict
audio_bible_dict = audio_bible_instance.to_dict()
# create an instance of AudioBible from a dict
audio_bible_from_dict = AudioBible.from_dict(audio_bible_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


