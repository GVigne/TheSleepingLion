class:
  name: "Commands documentation"
  color: 181,99,184

image:
  top: |2
    Attack \image{attack.svg} 1
      Range \image{range.svg} 3
      Stun \image{stun.svg}

aoe:
  top: |2
    \aoe{full_hexagon.aoe}

exp:
  top: |2
    \exp{1}

multiline:
  top: |2
    \consume_fire \multiline{\retaliate{2}}{@small Self} \exp{1}

charges:
  top: |2
    @small On your next four heal actions, add +2 Heal \image{heal.svg}
    \charges{}{\exp{1}}{}{\exp{1}}

charges_non_loss:
  top: |2
    @small On your next two attacks, add +2 Attack \image{attack.svg}
    \charges_non_loss{}{\exp{1}}

## Note: summon and summon2 should be merged in latex (only one command but two images)
summon:
  top: |2
    \summon{Summon Rat Swarm}{6}{1}{2}{}{\poison}
summon2:
  top: |2
    \summon{Summon Mosquito Swarm}{4}{1 \image{fly.svg}}{1}{3}{\wound}{\retaliate{1}}

dot:
  top: |2
    \attack{3} \dot \dot

inside:
  top: |2
    \inside{\image{experience.svg}}{@color{255}{0}{0} 1}

divider_line:
  top: |2
    \attack{1}
    \divider_line
    \attack{1}
