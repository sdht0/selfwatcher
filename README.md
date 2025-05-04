# Selfwatcher

Tracks active window titles, keyboard inputs, mouse clicks, and scrolls.

Motivated by [ulogme](https://karpathy.github.io/2014/08/03/quantifying-productivity) and wanting the same ability
to track keyboard inputs in [ActivityWatch](https://activitywatch.net/).

## What is tracked

Every 2 seconds, the scripts detect the current window class and title and associate all key presses and mouse inputs 
to that window. Keys are categorized (e.g., alphabets, ctrl, backspace) and mouse inputs are categorized as left clicks,
right clicks, and scrolls. See `KEYS_ARR` for all categories. If the same window is detected, the keyboard and mouse counts
are merged with the previous entry.

Every 1 minute, the collected data is written to the file at `~/.local/selfwatcher/YYYY/MM/YYYY-MM-dd.txt`. 

Sample output:
```
_started: TIMESTAMP: 2025-05-04T11:24:46.565-04:00 | POLL_INTERVAL_SEC: 2 | IDLE_TIMEOUT_SEC: 300 | PRINT_INTERVAL_SEC: 59
2025-05-04T11:25:10.621-04:00;24.051;;yakuake;Downloads : tmux: client — Yakuake;k-az:1;k-09:0;k-spl:0;k-alt:2;k-sft:0;k-ctl:1;k-del:0;k-cmd:1;k-arr:5;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
2025-05-04T11:25:12.625-04:00;2.000;;Code;selfwatcher.py - scripts - nix - Visual Studio Code;k-az:1;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:0;k-del:0;k-cmd:0;k-arr:0;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
2025-05-04T11:25:18.637-04:00;6.007;;yakuake;Downloads : tmux: client — Yakuake;k-az:1;k-09:0;k-spl:0;k-alt:0;k-sft:0;k-ctl:0;k-del:0;k-cmd:1;k-arr:0;k-etr:0;k-spc:0;k-tab:0;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
2025-05-04T11:25:20.640-04:00;2.000;;firefox;Get UTC Time [chatgpt.com] — Mozilla Firefox;k-az:1;k-09:0;k-spl:0;k-alt:1;k-sft:0;k-ctl:0;k-del:0;k-cmd:1;k-arr:0;k-etr:0;k-spc:0;k-tab:1;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:0;m-rc:0;m-mc:0;m-srl:0
2025-05-04T11:25:24.645-04:00;4.003;;yakuake;Downloads : tmux: client — Yakuake;k-az:2;k-09:0;k-spl:0;k-alt:1;k-sft:1;k-ctl:1;k-del:0;k-cmd:1;k-arr:0;k-etr:0;k-spc:0;k-tab:1;k-esc:0;k-nav:0;k-fun:0;k-oth:0;m-lc:1;m-rc:0;m-mc:0;m-srl:0
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
