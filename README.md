# Selfwatcher

Tracks active window titles, keyboard inputs, mouse clicks, and scrolls.

Motivated by [ulogme](https://karpathy.github.io/2014/08/03/quantifying-productivity) and wanting the same ability
to track keyboard inputs in [ActivityWatch](https://activitywatch.net/).

## What is tracked

Every 2 seconds, the scripts detect the current window class and title and associate all key presses and mouse inputs 
to that window. Keys are categorized (e.g., alphabets, ctrl, backspace) and mouse inputs are categorized as left clicks,
right clicks, and scrolls. See `KEYS_ARR` for all categories. If the same window is detected, the keyboard and mouse counts
are merged with the previous entry.

Every 1 minute, the collected data is written to the file at `~/.local/selfwatcher/YYYY/MM/YYYY-MM-dd.p2.i300.txt`. 

Sample output:
```
_started: 2025-05-03 20:26:10
2025-05-03 20:27:09;2025-05-03 20:27:03;;yakuake;Downloads : tmux: client — Yakuake;k-az:0;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:0;k-del:0;k-cmd:0;k-arr:0;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:1;m-rc:0;m-mc:0;m-srl:0
2025-05-03 20:27:13;2025-05-03 20:27:11;;Code;● README.md - selfwatcher - Visual Studio Code;k-az:2;k-09:0;k-spl:0;k-alt:0;k-sft:1;k-ctl:1;k-del:0;k-cmd:1;k-arr:0;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:1;m-rc:0;m-mc:0;m-srl:0
2025-05-03 20:27:15;2025-05-03 20:27:15;;Code;README.md - selfwatcher - Visual Studio Code;k-az:2;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:1;k-del:0;k-cmd:0;k-arr:0;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
2025-05-03 20:27:17;2025-05-03 20:27:17;;Code;● README.md - selfwatcher - Visual Studio Code;k-az:0;k-09:0;k-spl:1;k-alt:0;k-sft:0;k-ctl:1;k-del:0;k-cmd:0;k-arr:0;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
2025-05-03 20:27:19;2025-05-03 20:27:19;;Code;README.md - selfwatcher - Visual Studio Code;k-az:2;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:1;k-del:2;k-cmd:1;k-arr:0;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
2025-05-03 20:27:21;2025-05-03 20:27:21;;yakuake;Downloads : tmux: client — Yakuake;k-az:0;k-09:0;k-spl:0;k-alt:0;k-sft:3;k-ctl:0;k-del:0;k-cmd:1;k-arr:0;k-etr:4;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
```

## How to run

I'm running selfwatcher on macOS using [nix-darwin](https://github.com/nix-darwin/nix-darwin) and on NixOS with Plasma 6 inside [UTM](https://github.com/utmapp/UTM/).

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

    systemd.services."selfwatcher" = {
      path = config.environment.systemPackages;
      after = [ "display-manager.service" ];
      wantedBy = [ "display-manager.service" ];
      serviceConfig = {
      Type = "simple";
      ExecStart = "${config.myPython}/bin/python /opt/projects/selfwatcher/selfwatcher.py";
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
- I also use a [Firefox extension](https://github.com/sdht0/append-hostname-to-title) to track hostnames of websites open in Firefox.
