{
  description = "Django Auth Microservice";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          pkgs.python3
          pkgs.pylyzer
        ];
        shellHook = ''
          export SHELL="${pkgs.bashInteractive}/bin/bash"
        '';
      };
    };
}
