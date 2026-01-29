# Importación del módulo core compilado
import os
import importlib.util

# Intentar import relativo primero (funciona en desarrollo cuando está compilado in-place)
try:
    from .core import add, Calculator
except (ImportError, ModuleNotFoundError):
    # Fallback: cargar el módulo directamente desde el archivo .so
    # Esto es necesario porque los imports relativos/absolutos pueden fallar
    # con módulos de extensión compilados en ciertos contextos
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Buscar el archivo .so (puede tener diferentes nombres según la plataforma)
    so_files = [f for f in os.listdir(current_dir) 
                if f.endswith('.so') and 'core' in f.lower()]
    
    if so_files:
        so_path = os.path.join(current_dir, so_files[0])
        spec = importlib.util.spec_from_file_location("PyDynML.core", so_path)
        if spec and spec.loader:
            core_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(core_module)
            add = core_module.add
            Calculator = core_module.Calculator
        else:
            raise ImportError(f"No se pudo crear spec para {so_path}")
    else:
        raise ImportError(f"No se encontró archivo .so de core en {current_dir}")

__all__ = ["add", "Calculator"]
__version__ = "0.1.1"
