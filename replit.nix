{pkgs}: {
  deps = [
    pkgs.libuv
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.libuv
    ];
  };
}
