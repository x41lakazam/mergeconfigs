Mergeconfigs is a package that help managing configuration files.

**For now only YAML is supported.**

Mergeconfigs makes easy to merge several yaml files into one, using includes, placeholders and extends.
That way you can split your configurations into several files and merge them into one single yaml.  

# Install

Run `pip install mergeconfigs` to install.  

Run `python -m mergeconfigs --help` for help.

# Syntax
In a YAML file, one can use the following syntax:

- Include this file in another file: `#extends path/to/file.yaml`, if the current file contain
common keys with the other file, the current file will override it.
- Load context from a file: `#load path/to/file.yaml`, all the variables of this file will be loaded into a
context and can be used as a placeholder.
- Include the content of another file: `#include path/to/file.yaml`, if the file contain keys 
that are shared by the current file, it will override it.
- Use a variable from the context: `${namespace@variable}`, namespace here refer to 
the name of the file (without its extension) that contain the variable. It supports accessing 
dictionary keys, for example a variable `foo["bar"]` from `logging.yaml` can be used with `${logging@foo.bar}`.
The current file can be referenced with the special namespace `this`: `${this@myvar}`.

> **Note:** The file is read line by line, which mean if an #include is used in a file, 
> some values can still be overriden in the following lines.

# Example

Mergeconfigs use basic templating functions like variables insertion and 
including or extending other templates. 
It also provides support for different environment. 
It is best to explain how it works with an example:

Say we have an application directory with two settings config file, 
`settings-prod.yaml` is the production settings file and `settings-local.yaml`
is a copy of `settings-prod.yaml` but use a local mongoDB:

```
| app/
  | src/
     | my_program.py
     | settings-prod.yaml  
     | settings-local.yaml  
```

The config files contain the following content:

**settings-prod.yaml**
```
app_name: "MY_APP"
app_port: 5000
app_secret_key = "my-very-secret-key"

my_service:
    health_check_url: "http://my_service.com/check"
    
mongodb:
    uri: "mongodb://user:passwd@
    auto_connect: false
    print_errors: true
    db_alias: "my_database_alias"
  
log_messages: true
log_level: info 
log_prefix: "my_app_logger:"
```

**settings-local.yaml**
```
app_name: "MY_APP"
app_port: 5000
app_secret_key = "my-very-secret-key"

my_service:
    health_check_url: "http://my_service.com/check"
    
mongodb:
    uri: "mongodb://127.0.0.1:27017/my_database?readpreferenceaen=rest"
    auto_connect: false
    print_errors: true
    db_alias: "my_database_alias"
  
log_messages: true
log_level: info 
log_prefix: "my_app_logger:"
```

Big config files can be overwhelming, especially if you need to update/edit them to fit
your needs. Mergeconfigs help to split them to multiple files, here
is an example of how it can be used, add a `config` directory to `app/`,
move all the core content into `core.yaml` and split the other contents
into other files, adding a `hosts.yaml` file with all the hosts can be very useful:

```
| app/
  | src/
  |  | my_program.py
  | config/
     | core.yaml
     | logging.yaml
     | prod
     |  | hosts.yaml
     | local
     |  | hosts.yaml
```
Then generate a single `settings.yaml` file using: 

```
python -m mergeconfigs --workdir config --file core.yaml --env local
```


Here is the content of the files:

**core.yaml**
```
#load $$ENV$$/hosts.yaml

app_name: "MY_APP"
app_port: 5000
app_secret_key = "my-very-secret-key"

my_service:
    health_check_url: "http://${hosts@my_service.host}/check"
    
mongodb:
    uri: "mongodb://${hosts@mongodb.host}/my_database?readpreferenceaen=rest"
    auto_connect: false
    print_errors: true
    db_alias: "my_database_alias"

#include logging.yaml
```

The first line load all the variables in the `$$ENV$$/hosts.yaml` file, here
`$$ENV$$` is replaced by `local` because of the `--env local` parameter. Therefore,
it will load the `local/hosts.yaml` file, which itself extends the
`prod/hosts.yaml` file.

The hosts are then replaced using placeholders, like `${hosts@my_service.host}` 

Then `logging.yaml` is added to the content of the yaml file.

**logging.yaml**
```
log_messages: true
log_level: info 
log_prefix: "my_app_logger:"
```

**prod/hosts.yaml**
```
my_service:
    host: my_service.com
   
mongodb:
    host: mymongodb.net:27017
```

**local/hosts.yaml**
```
#extends prod/hosts.yaml

mongodb:
    host: 127.0.0.1:27017
```

The `local/hosts.yaml` file extends `prod/hosts.yaml` file, it only
overrides one of its attribute, the `mongodb.host` one.



# TODO
- Add support for list indices in variables: `${file@variable.0}`