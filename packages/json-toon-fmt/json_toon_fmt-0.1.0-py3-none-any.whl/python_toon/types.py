"""
Data types used throughout the JSON data format
"""

jsonPrimitive = str | int | float | bool | None

jsonObject = dict[str, "jsonData"]
jsonArray = list["jsonData"]

jsonData = jsonPrimitive | jsonObject | jsonArray

