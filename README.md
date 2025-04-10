# Selfwatcher

Tracks active window titles, keyboard inputs, mouse clicks, and scroll.

Motivated by [ulogme](https://karpathy.github.io/2014/08/03/quantifying-productivity) and wanting the same ability
to track keyboard inputs in [ActivityWatch](https://activitywatch.net/).

## What is tracked

Every 2 seconds, the scripts detect the current window class and title and associate all key presses and mouse inputs 
to that window. Keys are categorized (e.g., alphabets, ctrl, backspace) and mouse inputs are categorized as left clicks,
right clicks, and scrolls. See `KEYS_ARR` for all categories. If the same window is detected, the keyboard and mouse counts
are merged with the previous entry. Every 1 minute, the current data is written to a daily file at `~/.local/selfwatcher/YYYY/MM/YYYY-MM-dd.txt`. 

Sample output:
```
11:34:49;;Code;● README.md - selfwatcher - Visual Studio Code;time:2;k-az:5;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:0;k-del:0;k-cmd:0;k-arr:0;k-etr:0;k-spc:2;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:1;m-rc:0;m-mc:0;m-srl:0
11:34:51;;Code;README.md - selfwatcher - Visual Studio Code;time:10;k-az:6;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:2;k-del:0;k-cmd:0;k-arr:0;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:1;m-rc:0;m-mc:0;m-srl:0
11:35:01;;yakuake;Downloads : tmux: client — Yakuake;time:20;k-az:1;k-09:0;k-spl:0;k-alt:3;k-sft:0;k-ctl:0;k-del:0;k-cmd:1;k-arr:2;k-etr:2;k-spc:0;k-tab:0;k-esc:0;k-nav:3;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
11:35:21;;Code;README.md - selfwatcher - Visual Studio Code;time:8;k-az:3;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:2;k-del:0;k-cmd:1;k-arr:1;k-etr:0;k-spc:2;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:4;m-rc:0;m-mc:0;m-srl:44
11:35:29;;yakuake;Downloads : tmux: client — Yakuake;time:2;k-az:1;k-09:0;k-spl:0;k-alt:1;k-sft:0;k-ctl:0;k-del:0;k-cmd:1;k-arr:1;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:1;m-rc:0;m-mc:0;m-srl:0
11:35:31;;Code;README.md - selfwatcher - Visual Studio Code;time:2;k-az:2;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:0;k-del:0;k-cmd:2;k-arr:1;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:1;m-rc:0;m-mc:0;m-srl:0
11:35:33;;yakuake;Downloads : tmux: client — Yakuake;time:2;k-az:0;k-09:0;k-spl:0;k-alt:1;k-sft:0;k-ctl:0;k-del:0;k-cmd:0;k-arr:4;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
11:35:35;;Code;README.md - selfwatcher - Visual Studio Code;time:4;k-az:1;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:0;k-del:0;k-cmd:1;k-arr:0;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:1;m-rc:0;m-mc:0;m-srl:46
11:35:39;;yakuake;Downloads : tmux: client — Yakuake;time:2;k-az:1;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:0;k-del:0;k-cmd:1;k-arr:0;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:2;m-rc:0;m-mc:0;m-srl:0
11:35:41;;Code;README.md - selfwatcher - Visual Studio Code;time:2;k-az:1;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:0;k-del:0;k-cmd:0;k-arr:0;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
11:35:43;;Code;● README.md - selfwatcher - Visual Studio Code;time:6;k-az:12;k-09:0;k-spl:2;k-alt:0;k-sft:5;k-ctl:0;k-del:2;k-cmd:0;k-arr:1;k-etr:2;k-spc:1;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
```

## How to run

I'm running selfwatchers on macOS using [nix-darwin](https://github.com/nix-darwin/nix-darwin) and on NixOS running inside [UTM](https://github.com/utmapp/UTM/).

### NixOS

```nix
{
  config,
  lib,
  pkgs,
  ...
}:

{
  options = {
    myPythonPkg = lib.mkOption {
      type = lib.types.package;
      default = pkgs.python3;
    };
    myPythonPkgs = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
    };
    myPython = lib.mkOption {
      type = lib.types.package;
      default = config.myPythonPkg.withPackages (ps: lib.attrsets.attrVals config.myPythonPkgs ps);
    };
  };

  config = {
    myPythonPkgs = [
      "pynput"
      "xlib"
    ];
    environment.systemPackages = [
      config.myPython
    ];

    systemd.services."selfwatch" = {
      path = config.environment.systemPackages;
      after = [ "display-manager.service" ];
      wantedBy = [ "display-manager.service" ];
      serviceConfig = {
      Type = "simple";
      ExecStart = "${config.myPython}/bin/python /opt/projects/selfwatcher/selfwatch.py";
      User = "myuser"; #FIXME
      Restart = "always";
      RestartSec = 10;
      };
    };
  };
}
```

On other systems, you may need to update `xauth_files` inside `selfwatcher.py`.

### nix-darwin

Compile the code using `swiftc selfwatcher.swift`

```nix
{
  lib,
  pkgs,
  inputs,
  ...
}:
{
   launchd.user.agents.selfwatcher = {
    command = "/opt/projects/selfwatcher/selfwatcher";
    serviceConfig = {
      RunAtLoad = true;
      KeepAlive = true;
      StandardOutPath = "/opt/logs/selfwatcher.log";
      StandardErrorPath = "/opt/logs/selfwatcher.err";
    };
  };
}
```

Needs the `accessibility` permission.

## Notes

- The scripts just collect daily data for now. Processing the raw inputs and visualizing them will come later.
- The scripts are specific to my setup and will likely need some updates on other systems.
