# EZ Module Manager

A plug-n-play, modular Service Locator

![PyPI - Version](https://img.shields.io/pypi/v/ezmodulemanager)
![PyPI - License](https://img.shields.io/pypi/l/ezmodulemanager)

---
## Get it
```python
#PyPI
pip install ezmodulemanager
```

[Read the full documentation(or Quick Start) on GitHub](https://github.com/Obsidian-Cloud/EZModuleManager)


# Why this 'Service Locator'?

This 'Service Locator' is a structural design pattern designed to decouple object registration from execution. It was popularized by Martin Fowler, a pioneer of software architecture and a co-author of the Agile Manifesto.

## How it works: 'Discovery'

This module uses an event-driven startup sequence. By gating the entry point with if `__name__ == '__main__':`, the system triggers a dynamic import event using importlib.

- Registration: Class, clas methods, and functions use the `@mmreg` decorator 
to register themselves automatically during the import phase.
- Resolution: Your logic then uses `get_ob()` to 'grab and go', retrieving the objects it needs without hard-coded import dependencies.

## The 'Black Box' & Future Type Safety

Regarding `type hints`, I recognize that using a locator can 
create a 'black box'(passing/returning Any). I architected this 
framework solely for a project that required high flexibility
where type checking **does not** matter.

- **Current State**: It is a lightweight, high-speed discovery engine.
- **Future Roadmap**: I am working on a TypeVar type-checking module that will allow you to implement custom type checks on retrieved objects, turning the "black box" into a transparent, type-safe registry.

I’m not trying to replace Dependency Injection. I’m offering a reimagined, Pythonic alternative for developers who value simplicity *without* the bloat of Enterprise frameworks. Check out the source on GitHub to see just how minimal the implementation is.

## Features

**Supports All Object Types:** Functions, Classes, Class methods, 
Variables.

**Decoupled Object Execution:** Call a function in `module_A` from 
`module_B` without the modules 
ever importing one another.

**Isolated Registry:** A powerful registry component that stores the 
reference of any 'registered' objects, allowing for communication 
across your entire codebase.

**Circular Dependency Elimination:** Bypasses the common pitfalls of 
Python imports by utilizing a centralized registry for object access.

**Sequential Event-Driven Loading:** Uses `importlib` to load 
modules via custom `import_modlist()`, ensuring every object is
registered before your application logic ever executes it.

**Versatile Calling Methods:**

- **Direct Calls:** Execute functions/class methods immediately across 
namespaces (with or without arguments).
    
- **Deferred Use:** Retrieve and store classes, methods, and functions for later use.

**Zero-Bloat System:** No third-party dependencies; the system is 
designed to be lightweight and stay out of your way.

**Framework Agnostic:** Compatible with any standard Python entry point, 
including **Django**, **Flask**, and **FastAPI.** Completely standalone 
and modular.

**Version:** python 3.8+

## License

[MIT License](https://github.com/Obsidian-Cloud/EZModuleManager/blob/main/LICENSE)

