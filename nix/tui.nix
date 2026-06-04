# nix/tui.nix — Alga TUI (Ink/React) compiled with tsc and bundled
{ pkgs, algaNpmLib, ... }:
let
  src = ../ui-tui;
  npmDeps = pkgs.fetchNpmDeps {
    inherit src;
    hash = "sha256-F6/MzZOWc0zhW9mIfnaY+PrllPvJcsA/OdFdEM+NpLY=";
  };

  npm = algaNpmLib.mkNpmPassthru { folder = "ui-tui"; attr = "tui"; pname = "alga-tui"; };

  packageJson = builtins.fromJSON (builtins.readFile (src + "/package.json"));
  version = packageJson.version;
in
pkgs.buildNpmPackage (npm // {
  pname = "alga-tui";
  inherit src npmDeps version;

  doCheck = false;
  npmFlags = [ "--legacy-peer-deps" ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/alga-tui

    # Single self-contained bundle built by scripts/build.mjs (esbuild).
    cp -r dist $out/lib/alga-tui/dist

    # package.json kept for "type": "module" resolution on `node dist/entry.js`.
    cp package.json $out/lib/alga-tui/

    runHook postInstall
  '';
})
