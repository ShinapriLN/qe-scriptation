# qe-scriptation [still unorganized]

1. write quantum espresso input in json file
2. specify the path of json in python script

the script uses open mpi as default. 

```json
"main": {
    "project-dir": "test-project",  // project directory
    "pseudo-dir": "pps",            // path of pseudopotential
                // loop-n specify the key `loop` and the n-th element          
    "start_at": "loop-2",           // specific starting position 
    "except": ["relax"],            // not include in calculation
    "include": ["conv_test"],       // include only in calculation
    "n_proc": 4                     // num processing (default = 4)
}
```

`except` and `include` can't be specified in the same time, 
if there is no `except` but `include` the calculation only run from the key specified in `include`.
if there is `except` but no `include` the calculation run all keys except keys that are in the `except`
If there is no any of both `except` and `include` the calculation run all keys starting from specific in `start_at`.
If there is no `start_at` the calculation start at the after specify key of 'default' key.
If there is no any key after 'default' then the calculation start calculate from 'default' key.

```json
{
    "k_points (automatic)": "$script script.kp:get_kpoints"
}
```

the script eval at runtime or calculation time so can be added script as `$script python.file:function_name`. can be used to write a function that parse the previous job's output to be used as the current input.

**the flow run from up to down**

use `[]` for loop, or `{}` if not loop.