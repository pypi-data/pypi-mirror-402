{ pkgs, projectPath }:
pkgs.writeShellApplication {
  bashOptions = [ ];
  name = "labels-envars";
  text = ''
    export PRODUCT_ID="labels"
  '';
}
