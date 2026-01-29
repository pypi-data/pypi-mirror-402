{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/be5afa0fcb31f0a96bf9ecba05a516c66fcd8114.tar.gz") { } }:

pkgs.mkShell {
    packages = [
        pkgs.python314
        pkgs.python314Packages.pip
    ];

    shellHook = ''
        unset PYTHONPATH
    '';
}
