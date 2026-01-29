"""
- HDpip: A pip GUI based on maliang
- Copyright © 2025 寒冬利刃.
- License: MPL-2.0
"""
try:
    from . import core
except ImportError:
    import core

def main():
    print(core.base.getBaseDir())
    print(core.base.getPython())

if __name__ == "__main__":
    main()