# Jasmine 🌸

**Just A Simple Manager for Incredibly Nice Environments**

> Stop managing dotfiles. Start ricing.

**Current version:** Alpha 0.1 "Onigiri" 🍙

## What is jasmine?

A simple, automated dotfile manager that doesn't rely on git bare repos or symlink hell.

**Features:**
- 🌾 Export and import complete rice setups
- 🔄 Swap between config variants instantly  
- 💧 Auto-reload on changes
- 📦 Portable rice packages anyone can use

## How it works

Jasmine uses a "source of truth" model - the `active.rice` file (TOML format) in `~/.jasmine/`.

This file stores:
- Where configs live in your system
- Where jasmine stores variants
- How to reload each component

Every command reads and modifies this file. Keep it safe, or use `jasmine edit` to fix issues.

## Why does it exist?

When I switched to Hyprland, I needed a dotfile manager that was:
- ✅ Easy to set up
- ✅ Supports variant swapping
- ✅ Auto-reloads configs
- ✅ Actually simple

I could not find an option like this - so i made jasmine instead (with my mid python skills)

## Why choose jasmine?

Jasmine is meant to introduce **zero pain**. I've been daily-driving it since I built it, and it just works.

Simple commands. No complexity. Just rice.

## Installation

todo this part

## Quick Start

**Create a blank rice:**
```bash
jasmine plant -e
```

**Track your first config:**
```bash
jasmine bloom hypr tm ~/.config/hypr/hyprland.conf "hyprctl reload"
```

**Edit and auto-reload:**
```bash
jasmine hypr -w
```

**Full docs:** [Coming soon]

## ALPHA WARNING !

Jasmine is currently in alpha - this means it could have bugs, please report them
The most lacking thing is logging and errors - please do not trust anything they say under any circumstances (General rule: if there is a sign of success, disregard all errors)

If you have any ideas for new features, i would love to know about too, there is a high chance i might implement them

