class:
  name: "Macros documentation"

endlast:
  top: |2
    @small This is a small text, @endlast and this is a normal-sized text.

end:
  top: |2
    @small @color{255}{0}{0} Small red text, @end and big white text.

small:
  top: |2
    \attack{3}
    @small Add +2 \image{attack.svg} and gain \exp{1} if the target is adjacent to one of your allies.

big:
  top: |2
    @small A small text, @big and a big text.

title_font:
  top: |2
    @title_font This is a text using the title font.

color:
  top: |2
    @color{0}{0}{0} This is a text written in black.
    @color{255}{0}{0} This is a text written in red.

column2:
  top: |2
    \attack{3}
      \range{3}
      \immobilize
      Gain \exp{1} for every enemy targeted
    @column2 \aoe{triangle.aoe}

topleft:
  top: |2
    @topleft Augment
    @small On melee attack: Add +2 \image{attack.svg}

bottomright:
  top: |2
    \attack{6}
    @bottomright \image{loss.svg}