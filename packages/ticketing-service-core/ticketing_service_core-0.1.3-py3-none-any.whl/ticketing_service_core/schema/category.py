"""
Category Message Schema
"""
from .rpc_fields import rpc_fields

Category = {
	"type": "object",
	"allOf": [
		{"$ref": "#/definitions/rpc_fields"},
	],
	"properties": {
		"id": {"type": "string"},
		"created": {"type": "integer"},
		"modified": {"type": "integer"},
		"name": {"type": "string"},
		"subcategories": {"type": "array", "items": {"type": "string"}}
	},
    "unevaluatedProperties": False,
    "definitions": {
        "rpc_fields": rpc_fields
    },
  	"required": ["name"]
}
