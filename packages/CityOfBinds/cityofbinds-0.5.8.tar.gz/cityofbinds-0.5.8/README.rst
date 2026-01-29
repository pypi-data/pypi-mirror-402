================
City of Binds
================

A Python library for creating advanced key binds and macros for City of Heroes.

**Main Features**

- Bind, Macro, and CommandGroup classes for structured creation of their in-game counterparts
- BindFile class to manage collections of binds and more as well as file publishing
- Template based classes for the above to assist in content generation
- Common rotating bind classes for easy setup of complex bind file structures

**Advanced Features**

- BindFileGraph class for custom bind file networks
- BGFPublisher for publishing complex bind file graphs

Installation
~~~~~~~~~~~~

Install from PyPI using pip:

.. code-block:: bash

    pip install CityOfBinds

Background
~~~~~~~~~~

City of Heroes uses a powerful slash command system for most of its in-game operations. Things like targeting an enemy, activating a power, or even just moving can all be executed by their slash command counterparts.

While slash commands are typically ran in the chat window, they can also be bound to physical keys and in-game buttons. Respectively these would be known as binds (aka keybinds) and macros.

One of the slash commands available to users is the ``/bindloadfile`` command. This command allows users to load a file (called a bind file) containing multiple binds and macros all at once. Upon loading, these new binds would be immediately active in the game.

As more than one command can be bound to a key or button, these binds and macros can perform an action, and at the same time load a bind file to rebind that very same key or button! This is what is known as a rotating bind.

You can do some very cool things with rotating binds, whether it be for play optimization (e.g., set multiple powers on auto cast just by moving around) or roleplay (think casting a power and yelling a rotating catch phrase)!

No matter what you can think of yourself, this library can help you create the binds and files needed to bring your ideas to life in City of Heroes.

**Additional Resources**

- `Binds Wiki Page <https://homecoming.wiki/wiki/Binds>`_
- `List of Slash Commands <https://homecoming.wiki/wiki/List_of_Slash_Commands>`_

Walkthrough
~~~~~~~~~~~

**Basic Game Components**

The basic building blocks of this library are: Bind, Macro, and CommandGroup.

We can initialize a Bind by specifyin a trigger (aka the key on your keyboard) and optionally the commands we'd like to exectute when that trigger is pressed. For now let's just create a blank bind bound to the H key.

.. code-block:: python

    from CityOfBinds import Bind

    # Create a bind on the H key
    h_bind = Bind(key="H")

Now we can call one of the Bind's methods to add commands. Let's make it so hasten is activated when we press H.

.. code-block:: python

    # Add the hasten power command
    h_bind.commands.add_power("hasten")

Bind supports many different types of methods including toggling on, off, and location based execution of powers. For a full list of methods see the Bind class documentation.

If we were to print the string representation of this bind, we'd get the formatted bind as it'd be used in a bind file, and via the game_str method, we can even get the exact command we'd use in-game to execute this bind.

.. code-block:: python

    print(h_bind.get_str())
    # H "powexecname hasten"

    print(h_bind.game_str())
    # /bind H "powexecname hasten"

Very rarely do we want to just execute hasten alone. More often we'd like to auto cast that it to keep it always active. Let's create a new bind that does just that.

.. code-block:: python

    # Create a bind on the H key
    new_h_bind = Bind(key="H")

    # Add the auto power command for hasten
    new_h_bind.commands.add_auto_power("hasten")

    print(new_h_bind.get_str())
    # H "powexecauto hasten"

But of course we already have a bind on the H key! Let's instead add a modifier to the trigger so we can use both binds independently.

.. code-block:: python

    new_h_bind.trigger.modifier = "SHIFT"

    print(new_h_bind.get_str())
    # SHIFT+H "powexecauto hasten"

There we go! We can always access the trigger property of the bind to customize the key and modifier that make up the overall trigger. Note that we also could have just specified the modifier when we first created the bind (e.g., Bind("SHIFT+H")).

So far we've only added single commands to our binds, let's try adding more to make this bind more interesting.

.. code-block:: python

    # Add more commands to the bind
    new_h_bind.commands.add_command("say It's time for speed!")

    print(new_h_bind.get_str())
    # SHIFT+H "powexecauto hasten$$say It's time for speed!"

And just like that we get a bind with multiple commands, automatically separated by the proper in-game command separator ($$).

We can similarly create objects via the Macro class just as above, however instead of their commands being bound to a key, they'd be bound to an automatically created in-game button. Optionally, we can create MacroSlot objects which will create their macro button at a specific slot, or MacroImage objects which create macros with a custom icon. 

The CommandGroup class is also available to create objects that just help group multiple slash commands. Think of these as just a bind without the trigger part. While they may not be used as much as binds or macros, they do have interesting use in bind files.

**Bind Files**

Getting back to our example, while we could just call each bind's game_str method to get the command to load the new binds, let's instead move on to the BindFile class which can help us manage and publish our binds. We can define a blank bind file like so:

.. code-block:: python

    from CityOfBinds import BindFile

    # Create a blank bind file
    bind_file = BindFile()

Just like we added commands to our binds, we can add binds to our bind file.

.. code-block:: python

    # Add binds to the bind file
    bind_file.add_bind(h_bind)
    bind_file.add_bind(new_h_bind)

    print(bind_file.preview())
    # H "powexecname hasten"
    # SHIFT+H "powexecauto hasten$$say It's time for speed!"

As we can see by printing out the preview, both binds are now part of the bind file. We can now write this bind file to disk so we can load it in-game.

.. code-block:: python

    # Write bind file to disk
    bind_file.write_to_file("C:/path/to/Homecoming/settings/live/hasten_binds.txt")

We now have a bind file written to our city of heroes default folder! If you're not familiar with the default folder go ahead and readup up on it as it'll make future file management easier. `Default Folder <https://homecoming.wiki/wiki/Default_Folder>`_

Now in game we can just enter ``/bindloadfile hasten_binds.txt`` into the chat window and our new binds will be loaded and ready to use! Note that if you specificed a different path other than the default folder, you'd have to bindloadfile that entire path to that the file.

BindFile also supports adding Macros and CommandGroups, so feel free to explore those as well! In the case of loading macros, unless it's a MacroSlot object, every time the bind file is loaded, the macros will be added to the first available slot in your power tray.

In the case of CommandGroups, this allows arbitrary command execution when loading a bind file.

**Custom Rotating Binds**

The bind file we created in the previous example, while nice, is limited in scope in what we can actually do with binds. Let's get into more advanced tools to create a rotating bind that allows us to automatically put multiple powers on auto cast as we just move around in the game.

As we will be creating binds on the traditional movement keys (WASD), we can use a special bind class called WASDBind to help manage the actual movement slash commands that are needed to move the character around. We can define a WASDBind like so:

.. code-block:: python

    from CityOfBinds import WASDBind

    # Create a WASD bind system
    w_hasten_bind = WASDBind("W")

    print(w_hasten_bind.get_str())
    # W "+forward"

As we can see, the WASDBind automatically adds the proper movement command for the W key. We can add more commands to it just as before:

.. code-block:: python

    # Add the auto power command for hasten
    w_hasten_bind.commands.add_auto_power("hasten")

    print(w_hasten_bind.get_str())
    # W "+forward$$powexecauto hasten"

Now this bind will not only move the character forward, it'll also ensure hasten is on auto cast! Talk about set and forget! But we can go even further, let's go ahead and create a few more auto case W binds, as well as add each bind to its own bind file.

.. code-block:: python

    from CityOfBinds import BindFile

    # Create more WASD binds with different auto powers
    w_insp_bind = WASDBind("W")
    w_insp_bind.commands.add_auto_power("inner inspiration")

    w_domination_bind = WASDBind("W")
    w_domination_bind.commands.add_auto_power("domination")

    print(w_insp_bind.get_str())
    # W "+forward$$powexecauto inner inspiration"

    print(w_domination_bind.get_str())
    # W "+forward$$powexecauto domination"

    hasten_bf = BindFile().add_bind(w_hasten_bind)
    insp_bf = BindFile().add_bind(w_insp_bind)
    domination_bf = BindFile().add_bind(w_domination_bind)

Our three bind files will now allow us to put multiple powers on auto cast, however only one of the W binds will be active at one time. We need a way to make it so pressing W we will also load the new bind for W to enable auto casting of the next power.

We can always just use the add_command method to add a hard coded bindloadfile command to each bind, however, you'd have to keep track of file names and paths yourself. Instead let's use a special class called BindFileGraph to logically link the bind files:

.. code-block:: python

    from CityOfBinds import BindFileGraph

    # Create a bind file graph to manage the rotation
    bfg = BindFileGraph()

    # Add bind files to the graph
    bfg.add_bind_file(hasten_bf) # assigned index 0
    bfg.add_bind_file(insp_bf) # assigned index 1
    bfg.add_bind_file(domination_bf) # assigned index 2

    # Link the bind files in a rotation
    bfg.loop([0, 1, 2])
    # Creates a logical connection between files:
    # 0 -> 1 -> 2 -> 0

The above code shows how to add bind files to the bind file graph, as well as a special linking method to create a logical loop between the list of file indexes. Note that when files are added to the bind file graph, they are automatically assigned an index which we can reference for linking purposes.

Once the logical links are created, we can now publish the bind files using a publishing class called BGFPublisher. This class will take care of adding the proper bindloadfile commands to each bind based on the logical links we created in the bind file graph.

.. code-block:: python

    from CityOfBinds import BGFPublisher

    # Create a publisher for the bind file graph
    publisher = BGFPublisher(bfg)

    # Publish the bind files to disk
    publisher.publish_bind_files(
        parent_folder_name="auto_powers", 
        directory="C:/path/to/Homecoming/settings/live"
    )
    # C:/path/to/Homecoming/settings/live/auto_powers/0.txt
    #   W "+forward$$powexecauto hasten$$bindloadfilesilent auto_powers/1.txt"
    # C:/path/to/Homecoming/settings/live/auto_powers/1.txt
    #   W "+forward$$powexecauto inner inspiration$$bindloadfilesilent auto_powers/2.txt"
    # C:/path/to/Homecoming/settings/live/auto_powers/2.txt
    #   W "+forward$$powexecauto domination$$bindloadfilesilent auto_powers/0.txt"

And just like before we can go in-game and load the first bind file with ``/bindloadfile auto_powers/0.txt``. From there on out, as we move forward with the W key, the bind files will automatically rotate and ensure all powers will cycle between auto cast!

**Built In Rotating Binds**

Everything we've done up till now was to show how the core components of the library work together to create complex rotating binds. However, to make things easier, there are built in rotating bind classes that take care of the bind file graph and publisher for you.

Let's again create a bind system to auto cast multiple powers, but let's instead enable this on all WASD movement keys this time, as well as add even more powers. We can use the WASDRotatingBind class to help us with this.

.. code-block:: python

    from CityOfBinds import WASDRotatingBind

    # Create a rotating bind system
    wasd_bind = WASDRotatingBind()

    # Add powers you want automatically turned on
    wasd_bind.wasd_bind_template.add_auto_power_pool([
        "hasten", "inner inspiration", "domination", "mutation", "ageless core epiphany"
    ])

    # Generate the bind files
    wasd_bind.publish_bind_files(
        parent_folder_name="better_auto_powers", 
        directory="C:/path/to/Homecoming/settings/live"
    )
    # C:/path/to/Homecoming/settings/live/better_auto_powers/0.txt
    #   W "+forward$$powexecauto hasten$$bindloadfilesilent better_auto_powers/1.txt"
    #   A "+left$$powexecauto hasten$$bindloadfilesilent better_auto_powers/1.txt"
    #   S "+right$$powexecauto hasten$$bindloadfilesilent better_auto_powers/1.txt"
    #   D "+backward$$powexecauto hasten$$bindloadfilesilent better_auto_powers/1.txt"
    # C:/path/to/Homecoming/settings/live/better_auto_powers/1.txt
    #   W "+forward$$powexecauto inner inspiration$$bindloadfilesilent better_auto_powers/2.txt"
    #   A "+left$$powexecauto inner inspiration$$bindloadfilesilent better_auto_powers/2.txt"
    #   S "+right$$powexecauto inner inspiration$$bindloadfilesilent better_auto_powers/2.txt"
    #   D "+backward$$powexecauto inner inspiration$$bindloadfilesilent better_auto_powers/2.txt"
    # C:/path/to/Homecoming/settings/live/better_auto_powers/2.txt
    #   W "+forward$$powexecauto domination$$bindloadfilesilent better_auto_powers/3.txt"
    #   A "+left$$powexecauto domination$$bindloadfilesilent better_auto_powers/3.txt"
    #   S "+right$$powexecauto domination$$bindloadfilesilent better_auto_powers/3.txt"
    #   D "+backward$$powexecauto domination$$bindloadfilesilent better_auto_powers/3.txt"
    # C:/path/to/Homecoming/settings/live/better_auto_powers/3.txt
    #   W "+forward$$powexecauto mutation$$bindloadfilesilent better_auto_powers/4.txt"
    #   A "+left$$powexecauto mutation$$bindloadfilesilent better_auto_powers/4.txt"
    #   S "+right$$powexecauto mutation$$bindloadfilesilent better_auto_powers/4.txt"
    #   D "+backward$$powexecauto mutation$$bindloadfilesilent better_auto_powers/4.txt"
    # C:/path/to/Homecoming/settings/live/better_auto_powers/4.txt
    #   W "+forward$$powexecauto ageless core epiphany$$bindloadfilesilent better_auto_powers/0.txt"
    #   A "+left$$powexecauto ageless core epiphany$$bindloadfilesilent better_auto_powers/0.txt"
    #   S "+right$$powexecauto ageless core epiphany$$bindloadfilesilent better_auto_powers/0.txt"
    #   D "+backward$$powexecauto ageless core epiphany$$bindloadfilesilent better_auto_powers/0.txt"

And in just a few lines of code, we have a full WASD rotating bind system that will auto cast multiple powers as we move around Paragon City!

I've tried to add a lot of useful rotating bind classes to help with common use cases. Feel free to explore the documentation for more features!

**Advanced Rotating Bind Customization**

If any of the built in rotating bind classes don't fit your needs, you can of course always generate any type of custom rotating bind using the BindFileGraph and BGFPublisher classes as shown in the previous section.

All built in rotating binds allow extracting the underlying BindFileGraph to help with any customizations you may need. From there you can extend the graph as needed before publishing. For example:

.. code-block:: python

    from CityOfBinds import Bind, BindFile, RotatingBind, BindFileGraph, BGFPublisher

    # Create a bind file to switch languages with relevant binds
    language_switcher = BindFile()
    language_switcher.add_bind(
        Bind("F1").commands.add_command("say Switching to English!")
    )
    language_switcher.add_bind(
        Bind("F2").commands.add_command("say Cambiando a Español!")
    )

    # Create a bind file graph and add our language switcher
    bfg = BindFileGraph()
    bfg.add_bind_file(language_switcher) # assigned index 0

    # Create two rotating bind systems for different languages
    english_hello = RotatingBind("H").add_command_arguments_pool([
        "say", ["Hello!", "Hi!", "What's up?"]
    ])
    spanish_hello = RotatingBind("H").add_command_arguments_pool([
        "say", ["Hola!", "Buenos días!", "¿Qué tal?"]
    ])

    # Get the underlying bind file graphs
    english_bfg = english_hello.get_bind_file_graph()
    spanish_bfg = spanish_hello.get_bind_file_graph()

    # Extend the rotating bind created bind file graphs onto the main graph
    bfg.extend(english_bfg).extend(spanish_bfg)
    # file indexes 0, 1, 2 from english_bfg auto increment to 1, 2, 3 in bfg
    # file indexes 0, 1, 2 from spanish_bfg auto increment to 4, 5, 6 in bfg

    # Add custom links to make everything work together
    bfg.link(0, 1, load_conditions={on_trigger:"F1"}) # link language switch to english hello
    bfg.link(0, 4, load_conditions={on_trigger:"F2"}) # link language switch to spanish hola

    # Publish the bind files
    publisher = BGFPublisher(bfg)
    publisher.publish_bind_files(
        parent_folder_name="language_hello_binds", 
        directory="C:/path/to/Homecoming/settings/live"
    )
    # /bindloadfile language_hello_binds/0.txt to load the language switcher

While there is a lot more going on in this example, this shows how one might leverage the built in rotating bind classes to form a bind system which allows your character to cycle greetings by pressing the H key with the additional functionality of changing those greetings' languages via the F1 and F2 keys.

🔧 Development Setup
~~~~~~~~~~~~~~~~~~~~

If you want to contribute or modify the library:

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/yourusername/city-of-binds.git
    cd city-of-binds

    # Install in development mode with dev dependencies
    pip install -e ".[dev]"

    # Run tests
    pytest

    # Format code
    black .
    isort .
