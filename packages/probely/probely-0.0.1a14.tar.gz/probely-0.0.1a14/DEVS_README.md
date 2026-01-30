# Command behavior guidelines
* Arguments must be `kebab-case`
* Filter arguments must be prefixed with `--f-`
* Commands must accept list of ID's or filters.
  * Filters must be consistent among any particular subcommand
* Command validations:
  * Any IDS or filter is provided (except if command can affect ALL entities, like `get`)
  * IDs and Filters mutually exclusiveness (Can use both ID and filters)

# How to add pydantic schemas

`--output json` and `--output yaml` should return single instance with single ID command and list for multiple and filters

Step 1: generate schema files
```bash
datamodel-codegen  --url https://developers.probely.com/openapi.yaml --input-file-type openapi --output-model-type pydantic_v2.BaseModel  --output deleteme_generated_schema.py --use-annotated --field-constraints --wrap-string-literal --use-double-quotes  --snake-case-field
```
Step 2: extract expected Pydantic models and add to sdk.schemas._schemas.py   
Step 3: delete generated file  
