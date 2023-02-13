class:
    name: Spellweaver
    color: 181,99,184

Fire Orbs:
    level: 1
    initiative: 69
    ID: 061
    top: |2
      \attack{3}
        \range{3}
        \target{3}
      @small Gain \exp{1} for each enemy targeted.
      \generate_fire
      \loss
    bottom: |2
      \move{3}

Impaling Eruption:
    level: 1
    initiative: 62
    ID: 062
    top: |2
      \attack{3}
        \range{4}
      @small Additionally, target all enemies on the path to the primary target.
      @small Gain \exp{1} for each enemy targeted.
      \generate_earth
      \loss
    bottom: |2
      \move{4}

Reviving Ether:
    level: 1
    initiative: 80
    ID: 063
    top: |2
      @small Recover \image{recover_card.svg} all your lost cards.
      \generate_dark
      \definitive_loss
    bottom: |2
      \move{4}
        \jump

Freezing Nova:
    level: 1
    initiative: 21
    ID: 064
    top: |2
      \attack{2}
        Target all adjacent enemies
        \immobilize
        \consume_ice +1 Attack \image{attack.svg}
    bottom: |2
      \heal{4}
        \range{4}
      \loss

Mana Bolt:
    level: 1
    initiative: 07
    ID: 065
    top: |2
      \attack{2}
        \range{3}
        \consume_any +1 Attack \image{attack.svg}, \exp{1}
    bottom: |2
      \heal{3}
        \range{1}

Frost Armor:
    level: 1
    initiative: 20
    ID: 066
    top: |2
      \attack{2}
        \range{3}
        \consume_any +1 Attack \image{attack.svg}, \exp{1}
    bottom: |2
      @small On the next two sources of damage on you, suffer no damage instead.
      \generate_ice
      \charges{\exp{1}}{\exp{1}}

Flame Strike:
    level: 1
    initiative: 36
    ID: 067
    top: |2
      \attack{3}
        \range{2}
        \consume_fire \wound
    bottom: |2
      \attack{2}
        \range{2}

Ride the wind:
    level: 1
    initiative: 83
    ID: 068
    top: |2
      \loot{1}
    bottom: |2
      \move{8}
        \jump
      \generate_wind
      \loss

Crackling Air:
    level: 1
    initiative: 25
    ID: 069
    top: |2
        On your next four attacks, add +1 Attack \image{attack.svg}.
        \consume_wind Add +2 Attack \image{attack.svg} instead.
      \charges{}{\exp{1}}{}{\exp{1}}
    bottom: |2
      \move{3}
      \consume_fire \multiline{\retaliate{2}}{@small Self @endlast} \round_bonus

Hardened Spikes:
    level: 1
    initiative: 26
    ID: 070
    top: |2
      \retaliate{2}
        Affect self and all adjacent allies.
        \consume_earth +1 Retaliate \image{retaliate.svg}
      \exp{2} \round_bonus
      \loss
    bottom: |2
      \move{3}
      \consume_ice \multiline{\shield{2}}{@small Self @endlast} \round_bonus

Aid from the Ether:
    level: 1
    initiative: 91
    ID: 071
    top: |2
      \heal{3}
        \range{3}
    bottom: |2
      \summon{Summon Mystic Ally}{2}{3}{2}{2}{}
      \exp{2} \permanent
      \loss
