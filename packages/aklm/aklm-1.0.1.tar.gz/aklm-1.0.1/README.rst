Automatic Keyboard Layout Manager (AKLM)
========================================

**AKLM** is a lightweight daemon that automatically switches your keyboard layout on Xorg with i3 window manager based on the focused application. No more manual layout switching when jumping between your IDE, browser, or terminal!

.. contents:: Table of Contents
   :depth: 2

Why AKLM?
---------

The Genesis
~~~~~~~~~~~

AKLM was born out of frustration while playing a game on Linux. The game was hardcoded to use the US keyboard layout with no option to change keymapping. For someone using an alternative layout (like Bépo or Dvorak), this made the game nearly unplayable.

.. note::
   **A Note on Proper Input Handling**

   Games like **Factorio** are exemplary in how they handle input. They work at the **keycode level** rather than the **keymap level**, which means they detect physical key positions regardless of your keyboard layout. This makes them truly layout-agnostic and universally accessible. More game developers should follow this approach!

AKLM solves this problem by automatically switching your keyboard layout based on which window has focus. Launch your game? AKLM switches to US. Go back to Firefox? Back to your preferred layout. It's seamless and automatic.

How It Works
------------

AKLM runs as a background daemon that:

1. Monitors i3 window focus events using the i3 IPC protocol
2. Reads window properties (specifically ``WM_CLASS``) of the focused window
3. Looks up the appropriate keyboard layout from its configuration file
4. Switches the layout using ``setxkbmap`` when needed

The switching only happens when the layout actually needs to change, avoiding unnecessary system calls.

Installation
------------

.. code-block:: bash

   pip install aklm

Or install from source:

.. code-block:: bash

   git clone https://git.yapbreak.fr/aoliva/aklm.git
   cd aklm
   pip install .

Requirements
~~~~~~~~~~~~

* **Operating System**: Linux with X11 (Xorg)
* **Window Manager**: i3 or i3-gaps
* **Tools**: ``setxkbmap`` (usually pre-installed)
* **Python**: 3.10 or later

Dependencies:

* ``i3ipc`` - for communicating with i3 window manager

Configuration
-------------

AKLM follows the XDG Base Directory Specification. It looks for configuration files in:

1. System-wide: ``/etc/xdg/aklm.ini`` (or directories in ``$XDG_CONFIG_DIRS``)
2. User-specific: ``$XDG_CONFIG_HOME/aklm/aklm.ini`` (defaults to ``~/.config/aklm/aklm.ini``)

User configuration takes precedence over system-wide configuration.

Configuration File Format
~~~~~~~~~~~~~~~~~~~~~~~~~

Create ``~/.config/aklm/aklm.ini`` with the following structure:

.. code-block:: ini

   [general]
   default_layout = fr bepo
   setxkbmap = /usr/bin/setxkbmap

   [log]
   level = info

   [layout]
   firefox = fr
   code = en
   factorio = us
   Steam = us
   discord = fr bepo

Configuration Sections
~~~~~~~~~~~~~~~~~~~~~~

**[general]**

* ``default_layout``: The keyboard layout to use when no specific mapping is found. Format: ``language variant`` (e.g., ``fr bepo``, ``us``, ``de nodeadkeys``)
* ``setxkbmap``: Full path to the setxkbmap binary (default: ``/usr/bin/setxkbmap``)

**[log]**

* ``level``: Logging verbosity. Options: ``error``, ``warning``, ``info``, ``debug``

**[layout]**

This section maps window classes to keyboard layouts. Each line follows the format:

.. code-block:: ini

   window_class = layout

* **window_class**: The ``WM_CLASS`` property of the application window
* **layout**: The keyboard layout to use (same format as ``default_layout``)

Finding Window Classes
~~~~~~~~~~~~~~~~~~~~~~

To find the ``WM_CLASS`` of any window, use the ``xprop`` utility:

1. Run ``xprop`` in a terminal
2. Click on the window you want to identify
3. Look for the ``WM_CLASS`` line in the output

.. code-block:: bash

   $ xprop | grep WM_CLASS
   WM_CLASS(STRING) = "code", "Code"

The second value (``Code`` in this example) is what you should use in your configuration.

**Common Window Classes:**

* Firefox: ``firefox``
* VS Code: ``code``
* Terminal (many): ``Alacritty``, ``Terminator``, ``Xterm``
* Steam: ``Steam``
* Discord: ``discord``

Usage
-----

Running AKLM
~~~~~~~~~~~~

Start AKLM manually:

.. code-block:: bash

   aklm

Or add it to your i3 configuration to start automatically:

.. code-block:: bash

   # ~/.config/i3/config
   exec --no-startup-id aklm

Running as a Systemd Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a more robust setup, create a systemd user service at ``~/.config/systemd/user/aklm.service``:

.. code-block:: ini

   [Unit]
   Description=Automatic Layout Manager
   After=graphical-session.target

   [Service]
   Type=simple
   ExecStart=/usr/bin/aklm
   Restart=on-failure

   [Install]
   WantedBy=graphical-session.target

Then enable and start it:

.. code-block:: bash

   systemctl --user enable --now aklm

Examples
--------

Example 1: Multilingual Developer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A French developer using Bépo layout who needs US layout for gaming:

.. code-block:: ini

   [general]
   default_layout = fr bepo

   [layout]
   code = us
   terminal = fr bepo
   firefox = fr
   Steam = us
   factorio = us

Example 2: Documentation Writer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Someone who writes in multiple languages:

.. code-block:: ini

   [general]
   default_layout = us

   [layout]
   firefox = fr
   libreoffice-writer = de
   thunderbird = us

Troubleshooting
---------------

Layout Not Switching
~~~~~~~~~~~~~~~~~~~~

1. **Check if AKLM is running**: ``ps aux | grep aklm``
2. **Verify window class**: Use ``xprop`` to confirm the actual window class
3. **Check logs**: Run AKLM with debug logging:

   .. code-block:: ini

      [log]
      level = debug

4. **Test setxkbmap manually**: ``setxkbmap fr`` to ensure it works

i3 Connection Issues
~~~~~~~~~~~~~~~~~~~~

Ensure i3 IPC socket is accessible. Check that your i3 is running properly:

.. code-block:: bash

   i3-msg -t get_version

Contributing
------------

Contributions are welcome! Please feel free to submit issues or pull requests.

License
-------

AKLM is licensed under the MIT License. See the LICENSE file for details.

Author
------

Adrien Oliva <aoliva@yapbreak.fr>
