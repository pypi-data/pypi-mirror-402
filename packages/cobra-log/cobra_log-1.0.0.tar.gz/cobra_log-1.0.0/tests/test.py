import sys
sys.path.insert(0, "/data/tianzhen/my_packages/cobra-log/src")


# tests/test_log.py
from cobra_log import trace_exc, enable_color, warning, error, critical, info, log_init, set_trace
from cobra_log._utils import trace_stack, box_lines
from cobra_color import cstr
import cobra_log

import os

# use_color(False)
log_init("test_log.log", log_level="debug", use_color=True)

set_trace(min_width=1)

def a():
    s = ZeroDivisionError("123")
    raise ZeroDivisionError("division by zero44", s)
    1 / 0


def b():
    a()


def c():
    b()



def test_cobra_log():
    
    
    try:
        c()

    except Exception as e1:
        # dataset.multi_targets not defined
        try:
           
            try:
                
                raise ValueError(f"Try To Create From [dataset.targets], Dimension Error")
                
            except Exception as e3:
                # dataset.targets not defined
                try:
                    # try multi_targets in original_samples_arr
                    assert 1 == 0, ("Dataset Has No Attribute [samples]", e3, e3)
                except Exception as e4:
                    raise ValueError(e4, "Try To Create From [dataset.samples] Error", e4, e4, "dada")
        
        except Exception as e2:
            
            # print(" ".join(e2.args) + ".")
            raise
            # f = trace_exc(e2, with_traceback=True)
            
            # print(f"WARNING: AAA  {trace_stack(0)}", f)
            
            # print(f.plain)
    
    

try:
    test_cobra_log()
except Exception as e:
    # raise
    f = trace_exc(e, exc_depth=-3, tb_depth=3, exc_args_limit=2, indent=3)
    print(len(f))
    
    print(type(f))
    
    
    ss = f.splitlines(keepends=True)
    
    print(len(ss))
    
    a = cstr("WARNING", f"[{trace_stack(0)}]", "XXXXXdadaaaaaaaaaaaaaaaaaaaaaaaaaaaa.", fg="y", styles={"bold"})

    # print(a, box_lines(f.splitlines(), top_indent=len(a) + 2, fg="y"))
    print("next")
    
    ff = warning("This is a warning message", e, dim=True)
    
    error("This is an error message", e, loc=2)
    
    # critical("This is a critical message", e, loc=3)

    info("This is an info message", e, indent=8, outline=True)

    info("This is an info message", e, indent=8, outline=False)
