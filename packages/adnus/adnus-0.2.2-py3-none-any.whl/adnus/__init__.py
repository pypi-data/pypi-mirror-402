"""
adnus (AdNuS): Advanced Number Systems
======================================

A comprehensive Python library for advanced number systems including:
- Hypercomplex numbers (via Cayley-Dickson construction)
- Bicomplex numbers
- Neutrosophic numbers
- And other advanced algebraic structures

Key Features:
-------------
1. Unified interface for all number systems
2. Complete Cayley-Dickson construction implementation
3. Mathematical operations with proper algebraic properties
4. Parsing utilities for various input formats
5. Mathematical sequences and functions
6. Compatibility with kececinumbers (if available)

Example Usage:
--------------
>>> from adnus import Complex, Quaternion, Octonion
>>> c = Complex(3, 4)
>>> q = Quaternion(1, 2, 3, 4)
>>> o = Octonion(1, 2, 3, 4, 5, 6, 7, 8)
>>> print(c.norm())  # 5.0
>>> print(q * q)     # Quaternion multiplication
"""

# Core version information
__version__ = "0.2.2"
__author__ = "Mehmet Keçeci"
__license__ = "AGPL-3.0-or-later"
__copyright__ = "Copyright (C) 2025-2026 Mehmet Keçeci"

# Export control
__all__ = [
    # Core classes and functions
    'AdvancedNumber',
    'ComplexNumber',
    'BicomplexNumber', 
    'NeutrosophicNumber',
    'HypercomplexNumber',
    
    # Cayley-Dickson construction
    'cayley_dickson_process',
    'cayley_dickson_cebr',
    
    # Predefined algebras
    'Real',
    'Complex',
    'Quaternion',
    'Octonion',
    'Sedenion',
    'Pathion',
    'Chingon',
    'Routon',
    'Voudon',
    'Bicomplex',
    'Neutrosophic',
    
    # Parsing functions
    '_parse_complex',
    '_parse_universal',
    
    # Mathematical sequences and utilities
    'oresme_sequence',
    'harmonic_numbers',
    'binet_formula',
    'generate_cd_chain',
    'generate_cd_chain_names',
    
    # Utility functions
    'cd_number_from_components',
    
    # Constants and flags
    'HAS_KECECI',
]

# Import core modules
from .main import (
    AdvancedNumber,
    ComplexNumber,
    BicomplexNumber,
    NeutrosophicNumber,
    HypercomplexNumber,

# Import Cayley-Dickson implementation
    cayley_dickson_process,
    cayley_dickson_cebr,
    Real,
    Complex,
    Bicomplex,
    Neutrosophic,
    Quaternion,
    Octonion,
    Sedenion,
    Pathion,
    Chingon,
    Routon,
    Voudon,
    generate_cd_chain,
    cd_number_from_components,
    oresme_sequence,
    harmonic_numbers,
    binet_formula,
    generate_cd_chain_names,

# Import parsing utilities
    _parse_complex,
    _parse_universal,

# Import mathematical utilities
    oresme_sequence,
    harmonic_numbers,
    binet_formula,

# Import compatibility information
    HAS_KECECI
)
# =============================================
# Convenience re-exports (for backward compatibility)
# =============================================

# These provide the same interface as factory functions
Real = Real
Complex = Complex
Quaternion = Quaternion
Octonion = Octonion
Sedenion = Sedenion
Pathion = Pathion
Chingon = Chingon
Routon = Routon
Voudon = Voudon
Bicomplex = Bicomplex
Neutrosophic = Neutrosophic

# =============================================
# Package initialization
# =============================================

def __getattr__(name):
    """Lazy loading for optional components."""
    if name == 'HAS_KECECI':
        from .main import HAS_KECECI
        return HAS_KECECI
    raise AttributeError(f"module 'adnus' has no attribute '{name}'")


def setup_package():
    """Optional setup function for package configuration."""
    import warnings
    
    # Set numpy print options if available
    try:
        import numpy as np
        np.set_printoptions(precision=4, suppress=True)
    except ImportError:
        pass
    
    # Configure warnings
    warnings.filterwarnings('ignore', category=RuntimeWarning, module='adnus')
    
    print(f"adnus v{__version__} - Advanced Number Systems initialized")
    print(f"kececinumbers available: {HAS_KECECI}")


# Optional: auto-setup on import
_AUTO_SETUP = False  # Set to True for automatic setup

if _AUTO_SETUP:
    setup_package()


# =============================================
# Documentation helpers
# =============================================

def show_available_types():
    """Display all available number types in the package."""
    types_info = {
        "ComplexNumber": "Standard complex numbers (fallback implementation)",
        "BicomplexNumber": "Bicomplex numbers z = z1 + z2·j",
        "NeutrosophicNumber": "Neutrosophic numbers a + bI (I² = I)",
        "HypercomplexNumber": "Unified wrapper for all hypercomplex numbers",
        "Real": "Real numbers (1D, via Cayley-Dickson level 0)",
        "Complex": "Complex numbers (2D, via Cayley-Dickson level 1)",
        "Quaternion": "Quaternions (4D, via Cayley-Dickson level 2)",
        "Octonion": "Octonions (8D, via Cayley-Dickson level 3)",
        "Sedenion": "Sedenions (16D, via Cayley-Dickson level 4)",
        "Pathion": "Pathions (32D, via Cayley-Dickson level 5)",
        "Chingon": "Chingons (64D, via Cayley-Dickson level 6)",
        "Routon": "Routons (128D, via Cayley-Dickson level 7)",
        "Voudon": "Voudons (256D, via Cayley-Dickson level 8)",
        "Bicomplex": "Bicomplex",
        "Neutrosophic": "Neutrosophic",
    }
    
    print("Available Number Types in adnus:")
    print("=" * 70)
    for name, desc in types_info.items():
        print(f"{name:20} : {desc}")
    print()


def get_version_info():
    """Get detailed version information."""
    import sys
    import platform
    
    info = {
        "adnus_version": __version__,
        "python_version": sys.version,
        "platform": platform.platform(),
        "kececinumbers_available": HAS_KECECI,
    }
    
    return info


# =============================================
# Quick test/example function
# =============================================

def quick_test():
    """Run a quick test to verify package functionality."""
    print("Running adnus quick test...")
    print("-" * 40)
    
    try:
        # Test ComplexNumber
        c1 = ComplexNumber(3, 4)
        c2 = ComplexNumber(1, 2)
        print(f"✓ ComplexNumber: {c1} + {c2} = {c1 + c2}")
        print(f"  Norm({c1}) = {c1.norm():.2f}")
        
        # Test BicomplexNumber
        bc = BicomplexNumber(ComplexNumber(1, 2), ComplexNumber(3, 4))
        print(f"✓ BicomplexNumber: {bc}")
        print(f"  Norm = {bc.norm():.2f}")
        
        # Test NeutrosophicNumber
        nn = NeutrosophicNumber(2, 3)
        print(f"✓ NeutrosophicNumber: {nn}")
        print(f"  Conjugate = {nn.conjugate()}")
        
        # Test Hypercomplex
        q = Quaternion(1, 2, 3, 4)
        print(f"✓ Quaternion: {q}")
        print(f"  Norm = {q.norm():.2f}")
        
        # Test parsing
        parsed = _parse_universal("1,2,3,4", "quaternion")
        print(f"✓ Parsing: '1,2,3,4' -> {parsed}")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


# =============================================
# Module documentation
# =============================================

__doc__ = """
adnus (Advanced Number Systems)
===============================

A comprehensive library for working with advanced number systems.

Modules:
--------
1. core           - Core number classes (ComplexNumber, BicomplexNumber, etc.)
2. cayley_dickson - Cayley-Dickson construction implementation
3. parsing        - Parsing utilities for various number formats
4. math_utils     - Mathematical sequences and functions
5. compat         - Compatibility layer with kececinumbers

Quick Start:
-----------
>>> import adnus
>>> from adnus import Complex, Quaternion
>>> c = Complex(3, 4)
>>> q = Quaternion(1, 2, 3, 4)
>>> print(c.norm())  # 5.0
>>> print(q * 2)     # Scalar multiplication

For more examples, see the examples/ directory or run:
>>> adnus.quick_test()
"""


# =============================================
# Final initialization
# =============================================

# Generate package-level logger
import logging

class NullHandler(logging.Handler):
    """Null handler to avoid 'No handlers found' warnings."""
    def emit(self, record):
        pass

# Set up logger
logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())

# Clean up namespace
del NullHandler

print(f"adnus {__version__} - Advanced Number Systems Library")
