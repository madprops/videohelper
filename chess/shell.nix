{pkgs ? import <nixpkgs> {}}:

pkgs.mkShell {
  packages = [
    pkgs.ffmpeg
    (pkgs.python3.withPackages (ps: [
      ps.chess
      ps.cairosvg
    ]))
  ];
}