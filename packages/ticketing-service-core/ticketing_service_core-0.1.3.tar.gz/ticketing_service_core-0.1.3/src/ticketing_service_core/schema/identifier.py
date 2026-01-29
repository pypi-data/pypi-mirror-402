"""
Category Message Schema
"""
from .rpc_fields import rpc_fields

Identifier = {
	"type": "object",
	"allOf": [
		{"$ref": "#/definitions/rpc_fields"},
	],
	"properties": {
		"id": {"type": "string"}
	},
    "unevaluatedProperties": False,
    "definitions": {
        "rpc_fields": rpc_fields
    },
  	"required": ["id"]
}
