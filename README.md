# qe-scriptation [still unorganized]

**main**
- `project_dir` - project directory for calculation
- `pseudo_dir`- path to pseudopotentials directory
- `n_proc` - number of process used with open mpi ( default is 4 )
- `default_bin` - binary use in calculation as default ( default is `pw.x` )
- `bin` - organize what key to use what binary
- `calc_from_key` - specify key(s) to make the key calculate from that job
- `prevent_default_script` - specify key to prevent default script but use it's own
- `except` - specify key(s) to prevent the key from calculation
- `include` - specify key(s) to only include in calculation
- `start_at` - specify a key to start ( default is first key below `default` if not exists start from `default` )

### Example
```json
{
    "main": {
        "project_dir": "test-project",
        "pseudo_dir": "pps",
        "n_proc": 4,
        "default_bin": "pw.x",
        "bin": {
            "loop-2": "bands.x"
        },
        "calc_from_key": {
            "loop-2": "relax",
            "loop-1": "relax"
        },
        "prevent_default_script": ["conv-0", "conv-1"],
        "start_at": "conv-1",
        "except": ["loop-2"]
    },
    "default": {...},
    "conv": [{...}, {...}],
    "relax": {...},
    "loop": [{...}, {...}]
}
```

**default**
*default quantum espresso script write in lower case*

```
&NAMELIST
    ...
/
CARD
    ...
```

can be written as 

```json
"namelist": {
    ...
},
"namelist_1": {
    "key_1": "val_1",
    "key_2": "val_2",
    "key_3": "val_3"
},
"card": [...],          // or
"card_1": "...",        // string
"card_2": [...],        // array each element each line
```

**below the default**
*any key below the default are assumed as a script*

```json
{
    "main": {...},
    "default": {...},
    "key_1": {...},
    "key_2": {...},
    "key_3_loop": [
        {...}, 
        {...}
    ]
}
```

- `key_1` and `key_2` are contain values to override the `default` ( if not specify prevent `key_1` and `key_2` to not use the `default` )
- `key_3_loop` have values of array type so will be looped and created key like `key_3_loop-1`, `key_3_loop-2`, and so on.

---
next
- Scheduler