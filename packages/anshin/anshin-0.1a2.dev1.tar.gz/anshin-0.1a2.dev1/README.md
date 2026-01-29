# anshin

```
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣴⡆⢰⣶⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠚⠛⠛⠛⠃⠘⠛⠛⠛⠛⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣠⣾⣿⠏⢠⣾⣿⣿⣿⣿⣿⣦⠈⢿⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠐⠛⠛⠛⠀⠛⠛⠛⠛⠛⠛⠛⠛⠃⠘⠛⠛⠓⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢰⠇⣾⣿⣿⣿⣿⣿⣿⡇⢸⣿⣿⣿⠏⣰⣿⣿⡏⢠⣾⣿⡟⠁⠸⣷⠀⠀
⠀⠀⣉⣀⣉⣉⣉⠉⣉⣉⣉⣁⣈⣉⣉⡉⠀⣉⣉⣉⠀⣈⣉⣉⠁⠀⠀⣿⡇⠀
⠀⠸⠿⠿⠿⠿⠿⠀⠿⠿⠿⠿⠿⠿⠿⠟⠀⠿⠿⠿⠀⠿⠿⠿⠁⠀⠀⠻⠇⠀
```


<h4>
    anshin is an early-stage Python/TOML tool for describing and building a
    system in a reproducible way (inspired by declarative OS configuration
    workflows).
</h4>

>>> [!important]
Concepts related to and including the following are explicitly deferred:

- perfect sandboxing
- full package ecosystem
- bootloader integration (later)
- full cross-compilation
- more init systems (yes!)

Only concepts related to and including the following are explicity supported:

- BUILD HOST: Ubuntu 24.04(-based)
- TARGET INIT BACKEND: `systemd`
- MODULES [SMALL SET]: (base, users, sshd, packages)
- RECIPES [SMALL SET]: (shell, utilities)

⚠️ YOU are FREE to LICENSE this project under the terms set forth via
either the `LICENSE_APACHE` OR `LICENSE_GPLv3` file available at the project
root ⚠️
>>>

This package is a minimal functional seed:
- `anshin init` creates starter TOML config files
- `anshin validate` validates an `anshin.system.toml`
- `anshin --version` prints the version

## Usage:

```bash
anshin
anshin init --dir .
anshin validate anshin.system.toml
anshin --version
```

---

## Status:

Pre-alpha. Expect changes.

---


###### Made with ❤️ (Be nice!)
