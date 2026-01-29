# django-describe
django-describe generates a report on the run-time configuration of a Django site after 
everything has been loaded or created and initialised- generating lists of installed apps, 
models registered with the Django Admin, urls served, etc. The reports are generated in 
json format. 

The reports are the metadata for a site. You can use the reports for anything, but the 
reason django-describe was created was to feed the information into an LLM to generate 
tests.

# Usage
Generate a complete report using the following:

```shell
python manage.py describe
```

Reports, by default, are written to the console, but you can save them to a file either by 
redirecting the output, or using the `--output` option:
```
python manage,py describe --output metadata/description.json
```
