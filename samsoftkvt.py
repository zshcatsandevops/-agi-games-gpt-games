PS F:\#Stuff\CODING> & C:/Users/Admin/AppData/Local/Microsoft/WindowsApps/python3.13.exe f:/#Stuff/CODING/plantsvskoopas.py
pygame 2.6.1 (SDL 2.28.4, Python 3.13.9)
Hello from the pygame community. https://www.pygame.org/contribute.html
Traceback (most recent call last):
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 1116, in <module>
    draw_topbar()
    ~~~~~~~~~~~^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 883, in draw_topbar
    card.draw(screen, can_afford, is_sel)  
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^  
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 689, in draw
    temp_plant = self.cls(0, 0)
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 545, in __init__
    super().__init__(row, col)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 348, in __init__
    self.draw_plant()
    ~~~~~~~~~~~~~~~^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 553, in draw_plant
    fuse_end_x = self.rect.width//2 + 15 * math.cos(self.animation_timer * 2)
                                           
         ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'BombToad' object has no attribute 'animation_timer'
PS F:\#Stuff\CODING> & C:/Users/Admin/AppData/Local/Microsoft/WindowsApps/python3.13.exe f:/#Stuff/CODING/plantsvskoopas.py      
pygame 2.6.1 (SDL 2.28.4, Python 3.13.9)
Hello from the pygame community. https://www.pygame.org/contribute.html
Traceback (most recent call last):
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 1074, in <module>
    level.update(dt)
    ~~~~~~~~~~~~^^^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 795, in update
    self.spawn_enemy()
    ~~~~~~~~~~~~~~~~^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 823, in spawn_enemy
    enemy = HeavyKoopa(row)
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 327, in __init__
    super().__init__(row=row, hp=20, speed=30, dps=12, color=PURPLE)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 211, in __init__
    self.draw_enemy(color)
    ~~~~~~~~~~~~~~~^^^^^^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 243, in draw_enemy
    if self.armor_hp > 0:
       ^^^^^^^^^^^^^
AttributeError: 'HeavyKoopa' object has no attribute 'armor_hp'
PS F:\#Stuff\CODING> & C:/Users/Admin/AppData/Local/Microsoft/WindowsApps/python3.13.exe f:/#Stuff/CODING/plantsvskoopas.py
pygame 2.6.1 (SDL 2.28.4, Python 3.13.9)
Hello from the pygame community. https://www.pygame.org/contribute.html
Traceback (most recent call last):
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 1031, in <module>
    asyncio.run(main())
    ~~~~~~~~~~~^^^^^^^^
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.2544.0_x64__qbz5n2kfra8p0\Lib\asyncio\runners.py", line 195, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.2544.0_x64__qbz5n2kfra8p0\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.2544.0_x64__qbz5n2kfra8p0\Lib\asyncio\base_events.py", line 725, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 1024, in main
    update_loop()
    ~~~~~~~~~~~^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 982, in update_loop
    level.update(dt)
    ~~~~~~~~~~~~^^^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 725, in update
    self.spawn_enemy()
    ~~~~~~~~~~~~~~~~^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 748, in spawn_enemy
    enemy = HeavyKoopa(row)
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 305, in __init__
    super().__init__(row=row, hp=20, speed=30, dps=12, color=PURPLE)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 201, in __init__
    self.draw_enemy(color)
    ~~~~~~~~~~~~~~~^^^^^^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 228, in draw_enemy
    if self.armor_hp > 0:
       ^^^^^^^^^^^^^
AttributeError: 'HeavyKoopa' object has no attribute 'armor_hp'
PS F:\#Stuff\CODING> & C:/Users/Admin/AppData/Local/Microsoft/WindowsApps/python3.13.exe f:/#Stuff/CODING/plantsvskoopas.py
pygame 2.6.1 (SDL 2.28.4, Python 3.13.9)
Hello from the pygame community. https://www.pygame.org/contribute.html
Traceback (most recent call last):
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 1031, in <module>
    asyncio.run(main())
    ~~~~~~~~~~~^^^^^^^^
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.2544.0_x64__qbz5n2kfra8p0\Lib\asyncio\runners.py", line 195, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.2544.0_x64__qbz5n2kfra8p0\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.2544.0_x64__qbz5n2kfra8p0\Lib\asyncio\base_events.py", line 725, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 1024, in main
    update_loop()
    ~~~~~~~~~~~^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 982, in update_loop
    level.update(dt)
    ~~~~~~~~~~~~^^^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 725, in update
    self.spawn_enemy()
    ~~~~~~~~~~~~~~~~^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 744, in spawn_enemy
    enemy = Koopa(row)
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 295, in __init__
    super().__init__(row=row, hp=10, speed=45, dps=10, color=ORANGE)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 201, in __init__
    self.draw_enemy(color)
    ~~~~~~~~~~~~~~~^^^^^^^
  File "f:\#Stuff\CODING\plantsvskoopas.py", line 228, in draw_enemy
    if self.armor_hp > 0:
       ^^^^^^^^^^^^^
AttributeError: 'Koopa' object has no attribute 'armor_hp'
PS F:\#Stuff\CODING> 
