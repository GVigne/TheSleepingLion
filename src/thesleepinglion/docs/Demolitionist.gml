class:
  name: Demolitionist
  color: 251, 163, 29

Windup:
  level: '1'
  initiative: '77'
  ID: 082
  top: |2
    @small On your next two attacks, add +2 Attack \image{attack.svg}.
    \charges_non_loss{}{\exp{1}}
  bottom: |2
    @small Double the value of your next Move ability.
    \charges_non_loss{}
Crushing Weight:
  level: '1'
  initiative: '22'
  ID: 083
  top: |2
    \attack{3} \dot
    @small Add +2 Attack \image{attack.svg} and gain \exp{1} if the target is adjacent to a wall.
  bottom: |2
    \move{2} \dot
    @small One adjacent enemy that is adjacent to a wall suffers 2 damage.
Knock Out the Support:
  level: '1'
  initiative: '20'
  ID: 084
  top: |2
    \attack{3} \dot
    @small All heals targeting the target have no effect this round. To signify this, place one of your character tokens on the target.
    \generate_earth \round_bonus
  bottom: |2
    \move{2} \dot
    \divider_line
    @small Destroy one adjacent obstacle. If you do, gain \exp{1} and perform
    \strengthen
      Self
Explode:
  level: '1'
  initiative: '28'
  ID: 085
  top: |2
    @small Destroy one adjacent obstacle.
    @small If you do, gain \exp{2} and perform
    \stun
    @small Target all enemies adjacent to the destroyed obstacle.
    @small Each target suffers 2 damage.
    \loss
  bottom: |2
    \move{4} \dot
      \consume_fire +2 Move \image{move.svg}
Implode:
  level: '1'
  initiative: '88'
  ID: 086
  top: |2
    \attack{3}
      \consume_earth +1 Attack \image{attack.svg}, \muddle, \exp{1}
  bottom: |2
    \move{3} \dot
    \divider_line
    @small Destroy one obstacle within Range \image{range.svg} 3.
Piston Punch:
  level: '1'
  initiative: '42'
  ID: 087
  top: |2
    \attack{2} \dot
      \push{2} \dot
      \consume_fire +1 Attack \image{attack.svg}, +1 PUSH \image{push.svg}, \exp{1}
  bottom: |2
    \stun
      Target one adjacent enemy
      \consume_earth \poison
Explosive Blitz:
  level: '1'
  initiative: '19'
  ID: 088
  top: |2
    \attack{2}
      \range{4} \dot
    \generate_fire
  bottom: |2
    \move{3} \dot
    @small If you opened a door during the movement, perform
    \stun
    @small Target all enemies within Range \image{range.svg} 3
    \exp{1}
    \loss
The Big One:
  level: '1'
  initiative: '37'
  ID: 089
  top: |2
    \attack{3}
      \range{2}
    \generate_fire \generate_earth \exp{1}
    @column2 \aoe{full_hexagon.aoe}
    \loss
  bottom: |2
    \move{3} \dot
    \divider_line
    @small Destroy one adjacent obstacle.
    @small If you do, gain \exp{1} and perform
    \bless
      Self
One-Two Punch:
  level: '1'
  initiative: '66'
  ID: 090
  top: |2
    \attack{2} \dot
    \divider_line
    \attack{1} \dot
    @small Add \push{2}, \muddle and gain \exp{1} if this attack targets the same enemy as the previous Attack ability.
  bottom: |2
    \attack{1}
    \loot{1}
Rubble:
  level: X
  initiative: '55'
  ID: 091
  top: |2
    @small Designate one hex within Range \image{range.svg} 3 containing a destruction token. All allies and enemies in or adjacent to that hex suffer 2 damage.
    \generate_earth \exp{1}
  bottom: |2
    \move{2} \dot
    \divider_line
    @small Create one 2-damage trap in an adjacent empty hex containing a destruction token.
Level:
  level: X
  initiative: '61'
  ID: 092
  top: |2
    \attack{3} \dot
      Add +3 Attack \image{attack.svg} and gain \exp{1} if the target is an objective.
  bottom: |2
    @small Add +1 Attack \image{attack.svg} to all your melee attacks this round.
    \round_bonus
Lobbed Charge:
  level: '1'
  initiative: '52'
  ID: 093
  top: |2
    @small Create one 3-damage \muddle trap in an empty hex within \range{3}.
    \generate_fire
  bottom: |2
    \move{4} \dot
    \divider_line
    @small Designate one adjacent enemy. If each hex of the movement brought your closer to that enemy, perform
    \multiline{\attack{X}}{@small \push{2} @endlast} \exp{1}
    @small targeting that enemy, where X is the number of hexes you moved.
    \loss
