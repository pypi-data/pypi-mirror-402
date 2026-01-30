__all__ = ['in_interactive', 'in_notebook']
import sys

def in_interactive():
    return hasattr(sys, 'ps1')

def in_notebook():
    try:
        from IPython import get_ipython
        ipy = get_ipython()
        return ipy is not None and hasattr(ipy, 'config') and isinstance(ipy.config, dict) and ('IPKernelApp' in ipy.config)
    except ImportError:
        return False