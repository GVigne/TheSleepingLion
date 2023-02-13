r"""
This script is not meant to be launched by or through The Sleeping Lion. It is used to automatically generate documentation,
and should be manually executed every patch/update to get the names of all available images and aoes.

"""
from pathlib import Path

def names_to_latex(all_names: list[str]):
    latex_string = "\\begin{multicols}{2}\n\\begin{itemize}\n"
    for name in all_names:
        latex_string += "\\item \\verb`" + name +"`\n"
    latex_string += "\\end{itemize}\n\\end{multicols}\n"
    return latex_string

## Directory to where the PDF will be saved
target_directory = Path("Assets_names_list")
target_directory.mkdir(exist_ok=True)

images_path = Path("../../assets/")
aoe_path = Path("../../assets/aoe/")
save_path_aoe = target_directory / Path("aoe_names.txt")
save_path_images = target_directory / Path("images_names.txt")

aoe_names = [file.name for file in aoe_path.iterdir() if file.is_file()]
order_by_range = ["adjacent_two_hexes.aoe", "adjacent_three_hexes.aoe", "adjacent_triangle.aoe", "skewer.aoe",
                "long_skewer.aoe", "triangle.aoe", "full_hexagon.aoe", "cataclysm.aoe"]
aoe_names = [name for name in order_by_range if name in aoe_names] + [name for name in aoe_names if name not in order_by_range]

forbidden_images = ["not_found.svg", "one_charge.svg", "summon_1_block.png", "summon_2_blocks.png",
                    "template.svg", "enhancement_dot.svg", "__init__.py"]
elem_groups = ["fire.svg", "ice.svg", "earth.svg", "wind.svg", "dark.svg", "light.svg", "any_element.svg"]
status_group = ["muddle.svg", "wound.svg", "poison.svg", "immobilize.svg", "disarm.svg", "stun.svg", "curse.svg",
                "bless.svg", "strengthen.svg", "invisible.svg"]
actions_group = ["attack.svg", "move.svg", "range.svg", "target.svg", "heal.svg", "shield.svg", "retaliate.svg",
                "loot.svg", "jump.svg", "fly.svg"]

existing_names = [file.name for file in images_path.iterdir() if file.is_file()]
existing_names = [name for name in existing_names if name not in forbidden_images]
# Order names
images_names = [name for name in actions_group if name in existing_names] + \
               [name for name in status_group if name in existing_names] + \
               [name for name in elem_groups if name in existing_names] +\
               [name for name in existing_names if name not in actions_group and name not in status_group and name not in elem_groups]

with open(save_path_images, "w") as f:
    f.write(names_to_latex(images_names))

with open(save_path_aoe, "w") as f:
    f.write(names_to_latex(aoe_names))
