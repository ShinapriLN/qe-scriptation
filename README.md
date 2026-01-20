# qe-scriptation

**main**
- `project_dir` - project directory for calculation
- `pseudo_dir`- path to pseudopotentials directory
- `n_proc` - number of process used with open mpi ( default is 4 )
- `max_parallel` - max number of parallel process used ( default is 1 )
- `sequence` - mapping job for parallel process ( default is sequential )
- `binary_default` - binary use in calculation as default ( default is `pw.x` )
- `binary_map` - organize what key to use what binary
- `use_checkpoint` - specify key(s) to make the key calculate from that job
- `prevent_default` - specify key to prevent default script but use it's own
- `exclude_keys` - specify key(s) to prevent the key from calculation
- `include_keys` - specify key(s) to only include_keys in calculation
- `start_at_key` - specify a key to start ( default is first key below `default` if not exists start from `default` )

### Example
```json
{
    "main": {
        "project_dir": "test-project",
        "pseudo_dir": "pps",
        "n_proc": 4,
        "binary_default": "pw.x",
        "binary_map": {
            "loop-2": "bands.x"
        },
        "use_checkpoint": {
            "loop-2": "relax",
            "loop-1": "relax"
        },
        "prevent_default": ["conv-0", "conv-1"],
        "start_at_key": "conv-1",
        "exclude_keys": ["loop-2"],
        "sequence": [
            ["conv-[0-5]"], // write as range this will act same as below
            ["conv-6", "conv-7", "conv-8", "conv-9", "conv-10"]
        ],
        "max_parallel": 4,
    },
    "default": {...},
    "conv": [{...}, {...}],
    "relax": {...},
    "loop": [{...}, {...}]
}
```

can be used `script modules:function` to get the return value from the function, see the `example/example.json`.

*Note* each elements in `sequence` should be able to calculate independently for examples the first element of the above `sequence` is to tell the 'conv-0' to 'conv-5' can be run independently parallel, but the 'conv-6' to 'conv-10' use the result from the 'conv-0' to 'conv-5' so 'conv-[0-5]' should be run before 'conv-[6-10]' otherwise the script section e.g. `$script script.conv:get_best_ecutwfc` may be crashed from the results of 'conv-[0-5]` don't exist yet.

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
this will be copied the `default` and override (or add) to it.

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
## Quick Start

clone to the local

```bash
git clone https://github.com/ShinapriLN/qe-scriptation.git
cd qe-scriptation
```

change the `pseudo_dir` in `example/example.json` to yours

```bash
# install uv if hasn't
curl -LsSf https://astral.sh/uv/install.sh | sh 
```

run the test
```bash
PYTHONPATH=src uv run python main.py
```

---

**Shinapri**

MIT